<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { api, type ProcessInstance } from '$lib/api';
	import { wsClient } from '$lib/ws';
	import { Mic, Square, Upload, Check, X, Copy } from 'lucide-svelte';

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
	let mediaRecorder: MediaRecorder | null = null;
	let audioChunks: Blob[] = [];
	let audioStream: MediaStream | null = null;
	let unsub: (() => void) | null = null;

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
	}

	async function startNew() {
		const inst = await api.createInstance(PID, title || 'Patient ohne Name');
		current = inst;
		syncFromInstance(inst);
		await loadInstances();
		subscribeCurrent();
	}

	function subscribeCurrent() {
		unsub?.();
		if (!current) return;
		unsub = wsClient.subscribe(`process:patient_intake:${current.id}`, async () => {
			// any event → refresh instance state
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
		await api.appendTransition(PID, current.id, 'field_accepted', {
			field,
			value: fieldValues[field]
		});
	}
	async function reject(field: string) {
		if (!current) return;
		await api.appendTransition(PID, current.id, 'field_rejected', {
			field,
			value: fieldOriginals[field]
		});
	}
	async function commitCorrection(field: string) {
		if (!current) return;
		const before = fieldOriginals[field] ?? '';
		const after = fieldValues[field];
		if (before === after) return;
		await api.appendTransition(PID, current.id, 'field_corrected', {
			field,
			from: before,
			to: after
		});
	}

	async function copyValue(field: string) {
		try {
			await navigator.clipboard.writeText(fieldValues[field] ?? '');
		} catch {}
	}

	async function doUndo() {
		if (!current) return;
		try {
			await api.undo(PID, current.id);
		} catch {}
	}
	$effect(() => {
		registerUndo?.(doUndo);
	});

	function statusColor(s: string): string {
		switch (s) {
			case 'accepted':
				return 'border-emerald-300 bg-emerald-50';
			case 'corrected':
				return 'border-amber-300 bg-amber-50';
			case 'rejected':
				return 'border-stone-300 bg-stone-100 text-stone-400';
			default:
				return 'border-stone-300 bg-white';
		}
	}

	onMount(() => {
		loadInstances();
		// keyboard undo
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

<div class="space-y-6">
	{#if !current}
		<section class="rounded-xl border border-stone-200 bg-white p-6">
			<h2 class="mb-3 text-base font-semibold text-stone-900">Neue Sitzung starten</h2>
			<form on:submit|preventDefault={startNew} class="flex items-end gap-3">
				<div class="flex-1">
					<label class="block text-sm font-medium text-stone-700" for="title">Patientenname</label>
					<input
						id="title"
						type="text"
						bind:value={title}
						placeholder="Mueller, Hans"
						class="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2 text-sm"
					/>
				</div>
				<button class="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800">
					Sitzung starten
				</button>
			</form>
		</section>

		{#if instances.length}
			<section class="rounded-xl border border-stone-200 bg-white p-4">
				<h3 class="mb-2 text-sm font-medium text-stone-700">Letzte Sitzungen</h3>
				<ul class="divide-y divide-stone-100 text-sm">
					{#each instances.slice(0, 8) as i (i.id)}
						<li class="flex items-center justify-between py-2">
							<div>
								<div class="font-medium text-stone-900">{i.title || '(ohne Name)'}</div>
								<div class="text-xs text-stone-500">
									{new Date(i.created_at).toLocaleString('de-DE')} · {i.status}
								</div>
							</div>
							<button
								class="text-xs font-medium text-teal-700 hover:underline"
								on:click={() => {
									syncFromInstance(i);
									subscribeCurrent();
								}}
							>
								Öffnen →
							</button>
						</li>
					{/each}
				</ul>
			</section>
		{/if}
	{:else}
		<section class="rounded-xl border border-stone-200 bg-white p-4">
			<div class="flex flex-wrap items-center justify-between gap-3">
				<div>
					<div class="text-sm font-medium text-stone-900">{current.title}</div>
					<div class="text-xs text-stone-500">Sitzung {current.id.slice(0, 8)} · Status {current.status}</div>
				</div>
				<div class="flex items-center gap-2">
					{#if recState === 'idle'}
						<button
							class="flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
							on:click={startRec}
						>
							<Mic size={14} /> Aufnahme starten
						</button>
					{:else if recState === 'recording'}
						<button
							class="flex animate-pulse items-center gap-1.5 rounded-lg bg-stone-900 px-3 py-1.5 text-sm font-medium text-white"
							on:click={stopRec}
						>
							<Square size={14} /> Stop
						</button>
					{:else}
						<span class="text-sm text-stone-500">{recState}…</span>
					{/if}

					<label class="flex cursor-pointer items-center gap-1.5 rounded-lg border border-stone-300 bg-white px-3 py-1.5 text-sm text-stone-700 hover:bg-stone-50">
						<Upload size={14} /> Audio
						<input type="file" accept="audio/*" class="hidden" on:change={uploadFile} />
					</label>
					<label class="flex cursor-pointer items-center gap-1.5 rounded-lg border border-stone-300 bg-white px-3 py-1.5 text-sm text-stone-700 hover:bg-stone-50">
						<Upload size={14} /> Anamnesebogen
						<input type="file" accept="image/*" class="hidden" on:change={uploadFormImage} />
					</label>
					<button class="text-xs text-stone-500 hover:underline" on:click={() => (current = null)}>
						Zurück zur Liste
					</button>
				</div>
			</div>

			{#if current.current_state?.transcript}
				<details class="mt-3 text-xs text-stone-600">
					<summary class="cursor-pointer">Transkript anzeigen</summary>
					<p class="mt-2 whitespace-pre-wrap rounded bg-stone-50 p-2">{current.current_state.transcript}</p>
				</details>
			{/if}
		</section>

		<section class="rounded-xl border border-stone-200 bg-white p-4">
			<h3 class="mb-3 text-sm font-medium text-stone-700">Patientendaten</h3>
			<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
				{#each FIELDS as f (f)}
					<div>
						<label class="block text-xs font-medium text-stone-600" for={`fld-${f}`}>
							{LABELS[f] ?? f}
						</label>
						<div class="mt-1 flex gap-1">
							<input
								id={`fld-${f}`}
								type="text"
								class={`flex-1 rounded-lg border px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 ${statusColor(fieldStatus[f] ?? 'pending')}`}
								bind:value={fieldValues[f]}
								on:blur={() => commitCorrection(f)}
								on:keydown={(e) => {
									if (e.key === 'Enter') {
										(e.target as HTMLInputElement).blur();
									}
								}}
							/>
							<button
								class="rounded-lg border border-stone-300 bg-white px-1.5 text-stone-600 hover:bg-emerald-50 hover:text-emerald-700"
								title="Akzeptieren"
								on:click={() => accept(f)}
							>
								<Check size={14} />
							</button>
							<button
								class="rounded-lg border border-stone-300 bg-white px-1.5 text-stone-600 hover:bg-red-50 hover:text-red-700"
								title="Ablehnen"
								on:click={() => reject(f)}
							>
								<X size={14} />
							</button>
							<button
								class="rounded-lg border border-stone-300 bg-white px-1.5 text-stone-600 hover:bg-stone-100"
								title="Wert kopieren"
								on:click={() => copyValue(f)}
							>
								<Copy size={14} />
							</button>
						</div>
					</div>
				{/each}
			</div>
		</section>
	{/if}
</div>
