"""
Speaker diarization using SpeechBrain speaker embeddings + KMeans clustering.

Approach:
1. Load audio, split into short windows (1-2s)
2. Extract ECAPA-TDNN speaker embeddings per window via SpeechBrain
3. Cluster into 2 speakers with KMeans
4. Align clusters to named speakers (doctor / patient) using the Whisper segments
   and a simple heuristic: doctor tends to speak first and more overall
5. Re-segment using Whisper transcript segments + cluster labels
6. Return a formatted transcript: "ARZT: ...\nPATIENT: ..."
"""
from __future__ import annotations

import os
import tempfile
import numpy as np


def diarize(
    audio_path: str,
    transcript: str,
    patient_ref: str = "",
    doctor_name: str = "",
) -> str:
    """
    Run speaker diarization on audio_path.
    Returns a formatted transcript string with speaker labels.
    Falls back to plain transcript if diarization fails.
    """
    try:
        return _diarize_impl(audio_path, transcript, patient_ref, doctor_name)
    except Exception as e:
        # Non-fatal: return plain transcript with a note
        return transcript


def _diarize_impl(
    audio_path: str,
    transcript: str,
    patient_ref: str,
    doctor_name: str,
) -> str:
    import torch
    import torchaudio
    from sklearn.cluster import KMeans
    from speechbrain.inference.speaker import EncoderClassifier

    # Determine speaker labels
    label_doctor = doctor_name.split(",")[0].strip() if doctor_name else "Arzt"
    label_patient = patient_ref.split(",")[0].strip() if patient_ref else "Patient"

    # Load audio
    waveform, sr = torchaudio.load(audio_path)
    # Convert to mono
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    # Resample to 16kHz (SpeechBrain expects 16kHz)
    if sr != 16000:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
        waveform = resampler(waveform)
        sr = 16000

    total_samples = waveform.shape[1]
    total_duration = total_samples / sr

    # Need at least 4 seconds of audio to diarize meaningfully
    if total_duration < 4.0:
        return transcript

    # Load SpeechBrain ECAPA-TDNN model (downloads to ~/.cache/huggingface on first run)
    classifier = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        run_opts={"device": "cpu"},
        savedir=os.path.join(os.path.expanduser("~"), ".cache", "speechbrain", "spkrec-ecapa"),
    )

    # Sliding window: 1.5s windows, 0.75s hop
    window_sec = 1.5
    hop_sec = 0.75
    window_samples = int(window_sec * sr)
    hop_samples = int(hop_sec * sr)

    embeddings = []
    window_times = []  # (start_sec, end_sec) per window

    for start in range(0, total_samples - window_samples + 1, hop_samples):
        end = start + window_samples
        chunk = waveform[:, start:end]
        with torch.no_grad():
            emb = classifier.encode_batch(chunk)
        embeddings.append(emb.squeeze().numpy())
        window_times.append((start / sr, end / sr))

    if len(embeddings) < 2:
        return transcript

    X = np.array(embeddings)

    # Cluster into 2 speakers
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)

    # Build a timeline: for each 0.1s frame, which cluster is dominant?
    frame_dur = 0.1
    n_frames = int(total_duration / frame_dur) + 1
    frame_votes = np.full(n_frames, -1, dtype=int)

    for i, (t_start, t_end) in enumerate(window_times):
        f_start = int(t_start / frame_dur)
        f_end = int(t_end / frame_dur)
        for f in range(f_start, min(f_end, n_frames)):
            frame_votes[f] = labels[i]

    # Smooth: fill -1 gaps by nearest neighbor
    for f in range(n_frames):
        if frame_votes[f] == -1:
            # find nearest non-minus-one
            left = right = -1
            for ll in range(f - 1, -1, -1):
                if frame_votes[ll] != -1:
                    left = frame_votes[ll]; break
            for rr in range(f + 1, n_frames):
                if frame_votes[rr] != -1:
                    right = frame_votes[rr]; break
            frame_votes[f] = left if left != -1 else (right if right != -1 else 0)

    # Assign cluster 0 to doctor (speaks first / more) heuristic
    # Count which cluster dominates the first 25% of audio
    cutoff = n_frames // 4
    first_quarter = frame_votes[:cutoff]
    count0 = np.sum(first_quarter == 0)
    count1 = np.sum(first_quarter == 1)
    # Cluster that appears more in first quarter = doctor
    doctor_cluster = 0 if count0 >= count1 else 1
    patient_cluster = 1 - doctor_cluster

    def cluster_to_label(c: int) -> str:
        return label_doctor if c == doctor_cluster else label_patient

    # Now re-segment: find contiguous runs of same speaker in frame_votes
    # and build (start_sec, end_sec, speaker_label) segments
    segments: list[tuple[float, float, str]] = []
    if n_frames == 0:
        return transcript

    run_start = 0
    run_label = cluster_to_label(frame_votes[0])
    for f in range(1, n_frames):
        lbl = cluster_to_label(frame_votes[f])
        if lbl != run_label:
            segments.append((run_start * frame_dur, f * frame_dur, run_label))
            run_start = f
            run_label = lbl
    segments.append((run_start * frame_dur, n_frames * frame_dur, run_label))

    # Merge very short segments (< 1s) into neighbors
    merged: list[tuple[float, float, str]] = []
    for seg in segments:
        if merged and (seg[1] - seg[0]) < 1.0:
            # Merge with previous
            prev = merged[-1]
            merged[-1] = (prev[0], seg[1], prev[2])
        else:
            merged.append(seg)

    # Now align Whisper transcript to diarization segments
    # Use faster-whisper segments if available (re-transcribe with word timestamps)
    # Fallback: chunk the raw transcript text by time proportion
    lines = _align_transcript_to_segments(transcript, merged, total_duration)

    if not lines:
        return transcript

    return "\n".join(lines)


def _align_transcript_to_segments(
    transcript: str,
    segments: list[tuple[float, float, str]],
    total_duration: float,
) -> list[str]:
    """
    Simple alignment: distribute transcript words proportionally across segments.
    Returns list of "SPEAKER: text" lines.
    """
    if not segments or not transcript.strip():
        return []

    words = transcript.split()
    if not words:
        return []

    total_seg_time = sum(s[1] - s[0] for s in segments)
    lines = []
    word_idx = 0

    for start, end, speaker in segments:
        seg_dur = end - start
        proportion = seg_dur / total_seg_time if total_seg_time > 0 else 0
        n_words = max(1, round(proportion * len(words)))

        chunk_words = words[word_idx: word_idx + n_words]
        word_idx += n_words

        if chunk_words:
            lines.append(f"{speaker}: {' '.join(chunk_words)}")

    # Remaining words go to last speaker
    if word_idx < len(words):
        remaining = " ".join(words[word_idx:])
        if lines:
            lines[-1] += " " + remaining
        else:
            lines.append(f"{segments[-1][2]}: {remaining}")

    return lines
