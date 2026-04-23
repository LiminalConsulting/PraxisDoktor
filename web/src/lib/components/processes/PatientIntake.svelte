<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { api, type ProcessInstance } from '$lib/api';
	import { wsClient } from '$lib/ws';
	import { Mic, Square, Upload, Check, X, Copy, FileText, ChevronLeft, Loader2, AlertTriangle } from 'lucide-svelte';

	let { registerUndo }: { registerUndo?: (fn: () => void) => void } = $props();

	const PID = 'patient_intake';

	const FIELDS = [
		'nachname', 'vorname', 'geburtsdatum', 'geschlecht',
		'titel', 'anrede', 'strasse', 'hausnr', 'plz', 'ort',
		'telefon_privat', 'telefon_mobil', 'email', 'muttersprache'
	];
	const LABELS: Record<string, string> = {
		nachname: 'Nachname', vorname: 'Vorname', geburtsdatum: 'Geburtsdatum',
		geschlecht: 'Geschlecht', titel: 'Titel', anrede: 'Anrede',
		strasse: 'Straße', hausnr: 'Hausnr.', plz: 'PLZ', ort: 'Ort',
		telefon_privat: 'Telefon (privat)', telefon_mobil: 'Telefon (mobil)',
		email: 'E-Mail', muttersprache: 'Muttersprache'
	};

	let instances = $state<ProcessInstance[]>([]);
	let current = $state<ProcessInstance | null>(null);
	let title = $state('');
	let recState = $state<'idle' | 'recording' | 'uploading' | 'transcribing'>('idle');
	let ollamaWarn = $state<string | null>(null);
	let mediaRecorder: MediaRecorder | null = null;
	let audioChunks: Blob[] = [];
	let audioStream: MediaStream | null = null;
	let unsub: (() => void) | null = null;
	let copied = $state<string | null>(null);

	let fieldValues = $state<Record<string, string>>({});
	let fieldOriginals = $state<Record<string, string>>({});
	let fieldStatus = $state<Record<string, 'pending' | 'accepted' | 'rejected' | 'corrected'>>({});

	async function loadInstances() {
		instances = await api.listInstances(PID);
		if (current) {
			const fresh = instances.find((i) => i.id === current!.id);
			if (fresh) syncFromInstance(fresh);
		}
	}

	function syncFromInstance(inst: ProcessInstance) {
		current = inst;
		const fields = (inst.current_state?.fields ?? {}) as Record<string, { value: any; status: string }>;
		const newVals: Record<string, string> = {};
		const newOrig: Record<string, string> = {};
		const newStatus: Record<string, 'pending' | 'accepted' | 'rejected' | 'corrected'> = {};
		for (const f of FIELDS) {
			const v = fields[f];
			newVals[f] = v?.value ?? '';
			newOrig[f] = v?.value ?? '';
			newStatus[f] = (v?.status as any) ?? 'pending';
		}
		fieldValues = newVals;
		fieldOriginals = newOrig;
		fieldStatus = newStatus;
		recState = inst.status === 'processing' ? 'transcribing' : 'idle';
	}

	async function startNew() {
		const inst = await api.createInstance(PID, title || 'Patient ohne Name');
		current = inst;
		syncFromInstance(inst);
		title = '';
		await loadInstances();
		subscribeCurrent();
	}

	function subscribeCurrent() {
		unsub?.();
		if (!current) return;
		unsub = wsClient.subscribe(`process:patient_intake:${current.id}`, async () => {
			if (current) {
				const fresh = await api.getInstance(PID, current.id);
				syncFromInstance(fresh);
			}
		});
	}

	async function startRec() {
		audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
		audioChunks = [];
		mediaRecorder = new MediaRecorder(audioStream);
		mediaRecorder.ondataavailable = (e) => {
			if (e.data.size > 0) audioChunks.push(e.data);
		};
		mediaRecorder.onstop = async () => {
			const blob = new Blob(audioChunks, { type: 'audio/webm' });
			audioStream?.getTracks().forEach((t) => t.stop());
			if (current) {
				recState = 'uploading';
				await api.uploadAudio(current.id, blob);
				recState = 'transcribing';
			} else {
				recState = 'idle';
			}
		};
		mediaRecorder.start();
		recState = 'recording';
	}
	function stopRec() {
		mediaRecorder?.stop();
	}

	async function uploadFile(e: Event) {
		const input = e.target as HTMLInputElement;
		if (!input.files?.length || !current) return;
		recState = 'uploading';
		await api.uploadAudio(current.id, input.files[0], input.files[0].name);
		recState = 'transcribing';
	}

	async function uploadFormImage(e: Event) {
		const input = e.target as HTMLInputElement;
		if (!input.files?.length || !current) return;
		await api.uploadForm(current.id, input.files[0], input.files[0].name);
	}

	async function accept(field: string) {
		if (!current) return;
		await api.appendTransition(PID, current.id, 'field_accepted', { field, value: fieldValues[field] });
	}
	async function reject(field: string) {
		if (!current) return;
		await api.appendTransition(PID, current.id, 'field_rejected', { field, value: fieldOriginals[field] });
	}
	async function commitCorrection(field: string) {
		if (!current) return;
		const before = fieldOriginals[field] ?? '';
		const after = fieldValues[field];
		if (before === after) return;
		await api.appendTransition(PID, current.id, 'field_corrected', { field, from: before, to: after });
	}
	async function copyValue(field: string) {
		try {
			await navigator.clipboard.writeText(fieldValues[field] ?? '');
			copied = field;
			setTimeout(() => (copied = null), 1200);
		} catch {}
	}

	async function doUndo() {
		if (!current) return;
		try { await api.undo(PID, current.id); } catch {}
	}
	$effect(() => { registerUndo?.(doUndo); });

	function fieldClasses(s: string): string {
		switch (s) {
			case 'accepted':  return 'border-emerald-300 bg-emerald-50/60 focus:border-emerald-400 focus:ring-emerald-400/20';
			case 'corrected': return 'border-amber-300 bg-amber-50/60 focus:border-amber-400 focus:ring-amber-400/20';
			case 'rejected':  return 'border-praxis-300 bg-ink-100 text-ink-400 focus:border-praxis-400 focus:ring-praxis-400/20';
			default:          return 'border-praxis-300 bg-white focus:border-praxis-500 focus:ring-praxis-500/20';
		}
	}

	function statusDot(s: string): string {
		switch (s) {
			case 'accepted':  return 'bg-emerald-500';
			case 'corrected': return 'bg-amber-500';
			case 'rejected':  return 'bg-ink-300';
			default:          return 'bg-ink-200';
		}
	}

	async function checkOllama() {
		try {
			const h = await api.intakeHealth();
			if (!h.ollama.reachable) {
				ollamaWarn = `Ollama nicht erreichbar (${h.ollama.expected_model}). Erst nach Start der KI-Laufzeit kann extrahiert werden.`;
			} else if (h.ollama.model_present === false) {
				ollamaWarn = `Ollama läuft, aber das Modell ${h.ollama.expected_model} ist nicht installiert. Im Terminal: \`ollama pull ${h.ollama.expected_model}\`.`;
			} else {
				ollamaWarn = null;
			}
		} catch {
			ollamaWarn = null;
		}
	}

	onMount(() => {
		loadInstances();
		checkOllama();
		const handler = (e: KeyboardEvent) => {
			if ((e.metaKey || e.ctrlKey) && e.key === 'z' && !(e.target as HTMLElement)?.matches?.('input,textarea')) {
				e.preventDefault();
				doUndo();
			}
		};
		window.addEventListener('keydown', handler);
		return () => window.removeEventListener('keydown', handler);
	});
	onDestroy(() => unsub?.());
</script>

{#if ollamaWarn}
	<div class="mb-4 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
		<AlertTriangle size={16} class="mt-0.5 flex-shrink-0" />
		<div class="flex-1">{ollamaWarn}</div>
		<button class="text-xs font-medium underline" onclick={checkOllama}>Erneut prüfen</button>
	</div>
{/if}

{#if !current}
	<!-- Landing: start-new + recent sessions -->
	<div class="grid grid-cols-1 gap-6 lg:grid-cols-5">
		<section class="lg:col-span-3 rounded-xl border border-praxis-200 bg-white p-6 shadow-sm">
			<h2 class="text-sm font-semibold uppercase tracking-wider text-praxis-700">Neue Sitzung</h2>
			<p class="mt-1 text-sm text-ink-500">
				Geben Sie den Patientennamen ein und starten Sie die Aufnahme. Die Sitzung erscheint sofort in der Liste.
			</p>
			<form onsubmit={(e) => { e.preventDefault(); startNew(); }} class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
				<div class="flex-1">
					<label class="mb-1 block text-xs font-semibold uppercase tracking-wider text-praxis-700" for="title">
						Patientenname
					</label>
					<input
						id="title"
						type="text"
						bind:value={title}
						placeholder="Müller, Hans"
						class="w-full rounded-lg border border-praxis-300 px-3 py-2 text-sm focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20"
					/>
				</div>
				<button class="rounded-lg bg-praxis-700 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-praxis-800">
					Sitzung starten →
				</button>
			</form>
		</section>

		<section class="lg:col-span-2 rounded-xl border border-praxis-200 bg-white p-4 shadow-sm">
			<h3 class="px-2 text-xs font-semibold uppercase tracking-wider text-praxis-700">Letzte Sitzungen</h3>
			{#if instances.length === 0}
				<p class="mt-3 px-2 text-xs text-ink-400">Noch keine Sitzungen.</p>
			{:else}
				<ul class="mt-2 divide-y divide-praxis-100">
					{#each instances.slice(0, 8) as i (i.id)}
						<li>
							<button
								class="flex w-full items-center justify-between gap-3 rounded-md px-2 py-2 text-left transition hover:bg-praxis-50"
								onclick={() => { syncFromInstance(i); subscribeCurrent(); }}
							>
								<div class="min-w-0">
									<div class="truncate text-sm font-medium text-ink-900">{i.title || '(ohne Name)'}</div>
									<div class="text-[11px] text-ink-500">
										{new Date(i.created_at).toLocaleString('de-DE')}
									</div>
								</div>
								<span class={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider
									${i.status === 'ready' ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
										: i.status === 'processing' ? 'bg-amber-50 text-amber-700 ring-1 ring-amber-200'
										: i.status === 'error' ? 'bg-red-50 text-red-700 ring-1 ring-red-200'
										: 'bg-praxis-100 text-praxis-700 ring-1 ring-praxis-200'}`}>
									{i.status}
								</span>
							</button>
						</li>
					{/each}
				</ul>
			{/if}
		</section>
	</div>
{:else}
	<!-- Active session: two-panel layout, legacy-style -->
	<div class="space-y-4">
		<section class="rounded-xl border border-praxis-200 bg-white p-4 shadow-sm">
			<div class="flex flex-wrap items-center justify-between gap-3">
				<div class="flex items-center gap-3">
					<button
						class="flex h-8 w-8 items-center justify-center rounded-md border border-praxis-300 text-ink-500 hover:bg-praxis-100 hover:text-praxis-700"
						onclick={() => (current = null)}
						title="Zurück zur Liste"
					>
						<ChevronLeft size={16} />
					</button>
					<div>
						<div class="text-sm font-semibold text-ink-900">{current.title}</div>
						<div class="text-[11px] text-ink-500">
							Sitzung {current.id.slice(0, 8)} ·
							<span class={current.status === 'ready' ? 'text-emerald-700' : current.status === 'error' ? 'text-red-700' : 'text-amber-700'}>
								{current.status}
							</span>
						</div>
					</div>
				</div>
				<div class="flex flex-wrap items-center gap-2">
					{#if recState === 'idle'}
						<button
							class="flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-sm font-semibold text-white shadow-sm transition hover:bg-red-700"
							onclick={startRec}
						>
							<Mic size={14} /> Aufnahme starten
						</button>
					{:else if recState === 'recording'}
						<button
							class="flex animate-pulse items-center gap-1.5 rounded-lg bg-ink-900 px-3 py-1.5 text-sm font-semibold text-white"
							onclick={stopRec}
						>
							<Square size={14} fill="currentColor" /> Stop
						</button>
					{:else}
						<span class="flex items-center gap-1.5 rounded-lg bg-amber-50 px-3 py-1.5 text-sm font-medium text-amber-800 ring-1 ring-amber-200">
							<Loader2 size={14} class="animate-spin" />
							{recState === 'uploading' ? 'Lade hoch…' : 'Auswertung…'}
						</span>
					{/if}

					<label class="flex cursor-pointer items-center gap-1.5 rounded-lg border border-praxis-300 bg-white px-3 py-1.5 text-sm text-ink-700 transition hover:bg-praxis-100 hover:text-praxis-800">
						<Upload size={14} /> Audio
						<input type="file" accept="audio/*" class="hidden" onchange={uploadFile} />
					</label>
					<label class="flex cursor-pointer items-center gap-1.5 rounded-lg border border-praxis-300 bg-white px-3 py-1.5 text-sm text-ink-700 transition hover:bg-praxis-100 hover:text-praxis-800">
						<FileText size={14} /> Anamnesebogen
						<input type="file" accept="image/*" class="hidden" onchange={uploadFormImage} />
					</label>
				</div>
			</div>

			{#if current.current_state?.error}
				<div class="mt-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
					<AlertTriangle size={16} class="mt-0.5 flex-shrink-0" />
					<div>{current.current_state.error}</div>
				</div>
			{/if}

			{#if current.current_state?.transcript}
				<details class="mt-4 rounded-lg bg-praxis-50 p-3 text-xs text-ink-700">
					<summary class="cursor-pointer text-[11px] font-semibold uppercase tracking-wider text-praxis-700">
						Transkript anzeigen
					</summary>
					<p class="mt-2 whitespace-pre-wrap leading-relaxed">{current.current_state.transcript}</p>
				</details>
			{/if}
		</section>

		<section class="rounded-xl border border-praxis-200 bg-white shadow-sm">
			<div class="flex items-center justify-between border-b border-praxis-200 bg-praxis-50 px-4 py-2.5">
				<h3 class="text-xs font-semibold uppercase tracking-wider text-praxis-700">Patientendaten</h3>
				<div class="flex items-center gap-3 text-[10px] text-ink-500">
					<span class="flex items-center gap-1"><span class="h-2 w-2 rounded-full bg-emerald-500"></span> akzeptiert</span>
					<span class="flex items-center gap-1"><span class="h-2 w-2 rounded-full bg-amber-500"></span> korrigiert</span>
					<span class="flex items-center gap-1"><span class="h-2 w-2 rounded-full bg-ink-300"></span> abgelehnt</span>
				</div>
			</div>
			<div class="grid grid-cols-1 gap-x-5 gap-y-3 p-5 sm:grid-cols-2">
				{#each FIELDS as f (f)}
					<div>
						<label class="mb-1 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-praxis-700" for={`fld-${f}`}>
							<span class={`inline-block h-1.5 w-1.5 rounded-full ${statusDot(fieldStatus[f] ?? 'pending')}`}></span>
							{LABELS[f] ?? f}
						</label>
						<div class="flex gap-1">
							<input
								id={`fld-${f}`}
								type="text"
								class={`flex-1 rounded-lg border px-2.5 py-1.5 text-sm transition focus:outline-none focus:ring-2 ${fieldClasses(fieldStatus[f] ?? 'pending')}`}
								bind:value={fieldValues[f]}
								onblur={() => commitCorrection(f)}
								onkeydown={(e) => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur(); }}
							/>
							<button
								class="flex h-8 w-8 items-center justify-center rounded-lg border border-praxis-300 bg-white text-ink-500 transition hover:bg-emerald-50 hover:text-emerald-700"
								title="Akzeptieren"
								onclick={() => accept(f)}
							>
								<Check size={14} />
							</button>
							<button
								class="flex h-8 w-8 items-center justify-center rounded-lg border border-praxis-300 bg-white text-ink-500 transition hover:bg-red-50 hover:text-red-700"
								title="Ablehnen"
								onclick={() => reject(f)}
							>
								<X size={14} />
							</button>
							<button
								class={`relative flex h-8 w-8 items-center justify-center rounded-lg border border-praxis-300 bg-white text-ink-500 transition hover:bg-praxis-100 hover:text-praxis-700 ${copied === f ? 'border-praxis-500 bg-praxis-100 text-praxis-700' : ''}`}
								title="Wert kopieren"
								onclick={() => copyValue(f)}
							>
								<Copy size={14} />
								{#if copied === f}
									<span class="absolute -top-7 right-0 whitespace-nowrap rounded bg-ink-900 px-1.5 py-0.5 text-[10px] font-medium text-white shadow">kopiert</span>
								{/if}
							</button>
						</div>
					</div>
				{/each}
			</div>
		</section>
	</div>
{/if}
