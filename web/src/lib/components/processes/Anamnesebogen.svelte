<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type ProcessInstance } from '$lib/api';
	import { ChevronLeft, Copy, Check, RefreshCw, FileText, Sparkles, Info } from 'lucide-svelte';

	const PID = 'anamnesebogen';

	type Mode = 'patientenhinweise' | 'praxis_eigen';
	let activeMode = $state<Mode>('patientenhinweise');

	let instances = $state<ProcessInstance[]>([]);
	let current = $state<ProcessInstance | null>(null);
	let prose = $state<string>('');
	let answers = $state<Record<string, any>>({});
	let copied = $state<boolean>(false);
	let busy = $state<boolean>(false);

	async function loadInstances() {
		instances = await api.listInstances(PID);
	}

	function selectInstance(inst: ProcessInstance) {
		current = inst;
		const s = inst.current_state ?? {};
		prose = (s.anamnese_prose as string) ?? '';
		answers = (s.answers as Record<string, any>) ?? {};
	}

	function instanceSource(inst: ProcessInstance): string {
		return (inst.current_state?.source as string) ?? '';
	}

	function instanceLabel(inst: ProcessInstance): string {
		const src = instanceSource(inst);
		if (src.includes('patientenhinweise')) return 'MO-Import';
		if (src.includes('infoskop')) return 'Infoskop';
		if (src.includes('praxis_eigen')) return 'Praxis-Bogen';
		return 'Neu';
	}

	function instanceBadgeClasses(inst: ProcessInstance): string {
		const src = instanceSource(inst);
		if (src.includes('patientenhinweise')) {
			return 'bg-amber-50 text-amber-800 ring-1 ring-amber-200';
		}
		if (src.includes('infoskop')) {
			return 'bg-ink-100 text-ink-700 ring-1 ring-ink-200';
		}
		return 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200';
	}

	let uploadBusy = $state(false);
	let uploadError = $state<string | null>(null);

	async function uploadPatientenhinweise(e: Event) {
		const input = e.target as HTMLInputElement;
		if (!input.files?.length) return;
		uploadBusy = true;
		uploadError = null;
		try {
			const fd = new FormData();
			fd.append('file', input.files[0]);
			const res = await fetch('/api/anamnese/upload-patientenhinweise', {
				method: 'POST',
				credentials: 'include',
				body: fd,
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				uploadError = err.detail ?? 'Upload fehlgeschlagen';
				return;
			}
			await loadInstances();
			// auto-select the newest instance
			const newest = instances[0];
			if (newest) selectInstance(newest);
		} catch (e) {
			uploadError = String(e);
		} finally {
			uploadBusy = false;
			input.value = '';
		}
	}

	async function seedDemo(mode: Mode) {
		busy = true;
		try {
			await fetch('/api/anamnese/seed-demo', {
				method: 'POST',
				credentials: 'include',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ mode }),
			});
			await loadInstances();
		} finally {
			busy = false;
		}
	}

	async function regenerate() {
		if (!current) return;
		busy = true;
		try {
			const res = await fetch(`/api/anamnese/regenerate-prose/${current.id}`, {
				method: 'POST',
				credentials: 'include',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ answers }),
			});
			const data = await res.json();
			prose = data.anamnese_prose ?? '';
		} finally {
			busy = false;
		}
	}

	async function copyProse() {
		try {
			await navigator.clipboard.writeText(prose);
			copied = true;
			setTimeout(() => (copied = false), 1500);
		} catch {}
	}

	function formatAnswerKey(key: string): string {
		const map: Record<string, string> = {
			anliegen_heute: 'Anliegen heute',
			krankenkasse: 'Krankenkasse',
			vers_gesetzlich: 'Gesetzlich versichert',
			vers_privat: 'Privat versichert',
			vers_zusatz: 'Zusatzversicherung',
			pflegegrad: 'Pflegegrad',
			groesse: 'Größe (cm)',
			gewicht: 'Gewicht (kg)',
			beruf: 'Beruf',
			vor_op: 'Frühere OP',
			vor_op_text: 'OP-Details',
			medikamente_ja: 'Nimmt Medikamente',
			medikamente_text: 'Medikamenten-Liste',
			rauchen: 'Tabakkonsum',
			alkohol: 'Alkoholkonsum',
			familie_krebs: 'Krebs in der Familie',
			familie_krebs_text: 'Familiäre Krebserkrankung',
			hausarzt_name: 'Hausarzt',
			hausarzt_anschrift: 'Hausarzt-Anschrift',
			'miktionsbeschwerden.brennen': 'Brennen beim Wasserlassen',
			'miktionsbeschwerden.haeufiger_drang': 'Häufiger Harndrang',
			'miktionsbeschwerden.imperativ': 'Imperativer Drang',
			'miktionsbeschwerden.nykturie': 'Nächtliches Wasserlassen',
			'miktionsbeschwerden.haematurie': 'Blut im Urin',
			'miktionsbeschwerden.schwacher_strahl': 'Schwacher Strahl',
			'miktionsbeschwerden.nachtraeufeln': 'Nachträufeln',
			'miktionsbeschwerden.inkontinenz': 'Unfreiwilliger Urinverlust',
			'miktionsbeschwerden.trueber_urin': 'Trüber Urin',
			'miktionsbeschwerden.schmerzen_unterbauch': 'Unterbauchschmerzen',
			'miktionsbeschwerden.schmerzen_damm': 'Druck im Damm',
			'miktionsbeschwerden.dauer': 'Dauer der Miktionsbeschwerden',
			'vorerkrankungen.bluthochdruck': 'Hoher Blutdruck',
			'vorerkrankungen.diabetes': 'Diabetes',
			'vorerkrankungen.herzinfarkt': 'Herzinfarkt',
			'vorerkrankungen.schrittmacher': 'Herzschrittmacher',
			'vorerkrankungen.durchblutung': 'Durchblutungsstörungen',
			'vorerkrankungen.thrombose': 'Thrombose/Embolie',
			'vorerkrankungen.asthma': 'Asthma',
			'vorerkrankungen.lunge': 'Lungenerkrankung',
			'vorerkrankungen.schilddruese': 'Schilddrüse',
			'vorerkrankungen.krebs': 'Krebs',
			'vorerkrankungen.epilepsie': 'Epilepsie',
			'vorerkrankungen.magen_darm': 'Magen-Darm',
			'vorerkrankungen.niere': 'Niere',
			'vorerkrankungen.osteoporose': 'Osteoporose',
			'allergien.schmerzmittel': 'Allergie: Schmerzmittel',
			'allergien.antibiotika': 'Allergie: Antibiotika',
			'allergien.lokalanaesthesie': 'Allergie: Lokalanästhesie',
			'allergien.jod': 'Allergie: Jod',
			'allergien.kontrastmittel': 'Allergie: Kontrastmittel',
			'allergien.weitere_text': 'Sonstige Allergien',
			'allergien.keine': 'Keine bekannten Allergien',
		};
		return map[key] ?? key.replace(/_/g, ' ').replace(/\./g, ' › ');
	}

	function formatAnswerValue(v: any): string {
		if (v === true) return 'Ja';
		if (v === false) return 'Nein';
		if (v === 'aktuell') return 'aktuell';
		if (v === 'frueher') return 'früher';
		if (v === 'nie') return 'nie';
		if (v === 'regelmaessig') return 'regelmäßig';
		if (v === 'kein') return 'kein';
		return String(v);
	}

	function flattenAnswers(obj: Record<string, any>, prefix = ''): Array<[string, any]> {
		const out: Array<[string, any]> = [];
		for (const [k, v] of Object.entries(obj)) {
			const key = prefix ? `${prefix}.${k}` : k;
			if (v && typeof v === 'object' && !Array.isArray(v)) {
				out.push(...flattenAnswers(v, key));
			} else if (v !== '' && v !== null && v !== undefined) {
				out.push([key, v]);
			}
		}
		return out;
	}

	const flatAnswers = $derived(flattenAnswers(answers));

	onMount(() => {
		loadInstances();
	});
</script>

{#if !current}
	<div class="space-y-4">
		<!-- Mode toggle -->
		<section class="rounded-xl border border-praxis-200 bg-white p-4 shadow-sm">
			<div class="mb-3 flex items-center justify-between">
				<h2 class="text-sm font-semibold uppercase tracking-wider text-praxis-700">Anamnese-Quelle</h2>
				<span class="text-[11px] text-ink-500">Wie kommt die Anamnese in die Patientenakte?</span>
			</div>
			<div class="grid grid-cols-1 gap-3 md:grid-cols-2">
				<button
					class={`group rounded-lg border-2 p-4 text-left transition ${
						activeMode === 'patientenhinweise'
							? 'border-amber-600 bg-amber-50'
							: 'border-praxis-200 bg-white hover:border-amber-300 hover:bg-amber-50/40'
					}`}
					onclick={() => (activeMode = 'patientenhinweise')}
				>
					<div class="flex items-start gap-3">
						<FileText size={20} class="mt-0.5 text-amber-700" />
						<div class="flex-1">
							<div class="flex items-center justify-between">
								<h3 class="text-sm font-semibold text-ink-900">Patientenhinweise-Import</h3>
								<span class="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-800">
									sofort
								</span>
							</div>
							<p class="mt-1 text-xs text-ink-600">
								Workaround für den Kopier-Bug im MO-<em>Patientenhinweise</em>-Fenster.
								Screenshot machen → hochladen → fertiger Anamnese-Text zum Einfügen.
							</p>
						</div>
					</div>
				</button>

				<button
					class={`group rounded-lg border-2 p-4 text-left transition ${
						activeMode === 'praxis_eigen'
							? 'border-emerald-600 bg-emerald-50'
							: 'border-praxis-200 bg-white hover:border-emerald-300 hover:bg-emerald-50/30'
					}`}
					onclick={() => (activeMode = 'praxis_eigen')}
				>
					<div class="flex items-start gap-3">
						<Sparkles size={20} class="mt-0.5 text-emerald-700" />
						<div class="flex-1">
							<div class="flex items-center justify-between">
								<h3 class="text-sm font-semibold text-ink-900">Praxis-eigener Bogen</h3>
								<span class="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-700">
									konfigurierbar
								</span>
							</div>
							<p class="mt-1 text-xs text-ink-600">
								Maßgeschneidert für die Urologie. Erweiterbar nach Bedarf — neue Module entstehen
								aus dem <em>Verbesserungs-Wünsche</em>-Kanal.
							</p>
						</div>
					</div>
				</button>
			</div>
		</section>

		<!-- Action panel for the active mode -->
		<div class="grid grid-cols-1 gap-4 lg:grid-cols-5">
			<section class="lg:col-span-3 rounded-xl border border-praxis-200 bg-white p-6 shadow-sm">
				{#if activeMode === 'patientenhinweise'}
					<h3 class="text-sm font-semibold text-ink-900">Screenshot vom MO-Patientenhinweise-Fenster</h3>
					<p class="mt-1 text-sm text-ink-500">
						Patient hat Infoskop ausgefüllt → in Medical Office den Eintrag öffnen
						(<em>Patientenhinweise</em>-Fenster) → Screenshot machen
						(Windows: <kbd class="rounded bg-praxis-100 px-1 py-0.5 text-[10px]">⊞ + Shift + S</kbd>) → hier hochladen.
					</p>
					<div class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
						<label class="flex cursor-pointer items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-amber-700">
							<FileText size={16} /> Screenshot hochladen…
							<input type="file" accept="image/*" class="hidden" onchange={uploadPatientenhinweise} disabled={uploadBusy} />
						</label>
						{#if uploadBusy}
							<span class="flex items-center gap-1.5 text-sm text-ink-500">
								<RefreshCw size={14} class="animate-spin" /> wird verarbeitet…
							</span>
						{/if}
					</div>
					{#if uploadError}
						<div class="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
							<Info size={14} class="mt-0.5 flex-shrink-0" />
							<div>{uploadError}</div>
						</div>
					{/if}
					<div class="mt-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
						<Info size={14} class="mt-0.5 flex-shrink-0" />
						<div>
							Hintergrund: Im MO-<em>Patientenhinweise</em>-Fenster steht der Anamnese-Inhalt
							strukturiert da, lässt sich aber dort nicht markieren/kopieren. Dieses Werkzeug
							umgeht den Bug per Bildschirmfoto + Texterkennung.
						</div>
					</div>
				{:else}
					<h3 class="text-sm font-semibold text-ink-900">Praxis-eigener Anamnesebogen</h3>
					<p class="mt-1 text-sm text-ink-500">
						Patient füllt das Praxis-eigene Formular am iPad oder über die Praxis-Website aus.
						Die strukturierten Antworten werden hier eingehen und automatisch in einen
						Anamnese-Text im Klinik-Stil umgewandelt.
					</p>
					<div class="mt-4 flex flex-wrap gap-3">
						<button
							class="flex items-center gap-1.5 rounded-lg bg-emerald-700 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-emerald-800 disabled:opacity-50"
							onclick={() => seedDemo('praxis_eigen')}
							disabled={busy}
						>
							<Sparkles size={14} /> Demo-Eingabe zeigen
						</button>
						<a
							class="flex items-center gap-1.5 rounded-lg border border-praxis-300 bg-white px-4 py-2 text-sm text-ink-700 transition hover:bg-praxis-50"
							href="/anamnese-bogen"
							target="_blank"
						>
							<FileText size={14} /> Formular-Vorschau öffnen
						</a>
					</div>
					<div class="mt-4 flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50/60 px-3 py-2 text-xs text-emerald-900">
						<Info size={14} class="mt-0.5 flex-shrink-0" />
						<div>
							Die Felder dieses Formulars können in Absprache mit der Praxis erweitert oder
							angepasst werden — z.B. zusätzliche Module für Tumor-Verlauf, Erektionsstörungen,
							oder Nachsorge.
						</div>
					</div>
				{/if}
			</section>

			<!-- Recent submissions -->
			<section class="lg:col-span-2 rounded-xl border border-praxis-200 bg-white p-4 shadow-sm">
				<h3 class="px-2 text-xs font-semibold uppercase tracking-wider text-praxis-700">Eingegangen</h3>
				{#if instances.length === 0}
					<p class="mt-3 px-2 text-xs text-ink-400">
						Noch keine Eingänge.<br />Klicken Sie <em>Demo</em> für eine Vorschau.
					</p>
				{:else}
					<ul class="mt-2 divide-y divide-praxis-100">
						{#each instances.slice(0, 12) as i (i.id)}
							<li>
								<button
									class="flex w-full items-start gap-3 rounded-md px-2 py-2 text-left transition hover:bg-praxis-50"
									onclick={() => selectInstance(i)}
								>
									<div class="min-w-0 flex-1">
										<div class="truncate text-sm font-medium text-ink-900">
											{i.title?.replace('Anamnese: ', '') || '(ohne Name)'}
										</div>
										<div class="text-[11px] text-ink-500">
											{new Date(i.created_at).toLocaleString('de-DE', {
												day: '2-digit',
												month: '2-digit',
												hour: '2-digit',
												minute: '2-digit',
											})}
										</div>
									</div>
									<span class={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${instanceBadgeClasses(i)}`}>
										{instanceLabel(i)}
									</span>
								</button>
							</li>
						{/each}
					</ul>
				{/if}
			</section>
		</div>
	</div>
{:else}
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
						<div class="text-sm font-semibold text-ink-900">{current.title?.replace('Anamnese: ', '')}</div>
						<div class="text-[11px] text-ink-500">
							Eingang {new Date(current.created_at).toLocaleString('de-DE')}
							{#if current.current_state?.dob}· geb. {current.current_state.dob}{/if}
							· Quelle: <strong>{instanceLabel(current)}</strong>
						</div>
					</div>
				</div>
			</div>
			{#if current.current_state?.infoskop_coverage_note}
				<div class="mt-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
					<Info size={14} class="mt-0.5 flex-shrink-0" />
					<div>
						<strong>Infoskop-Lücke:</strong> {current.current_state.infoskop_coverage_note}
					</div>
				</div>
			{/if}
		</section>

		<div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
			<!-- Left panel: structured answers -->
			<section class="rounded-xl border border-praxis-200 bg-white shadow-sm">
				<div class="border-b border-praxis-200 bg-praxis-50 px-4 py-2.5">
					<h3 class="text-xs font-semibold uppercase tracking-wider text-praxis-700">Formular-Antworten</h3>
				</div>
				<div class="max-h-[60vh] overflow-y-auto p-4">
					{#if flatAnswers.length === 0}
						<p class="text-xs text-ink-400">Keine Antworten erfasst.</p>
					{:else}
						<dl class="space-y-1.5 text-sm">
							{#each flatAnswers as [k, v] (k)}
								<div class="grid grid-cols-3 gap-2 border-b border-praxis-100 pb-1.5">
									<dt class="col-span-1 text-[11px] font-medium text-praxis-700">
										{formatAnswerKey(k)}
									</dt>
									<dd class="col-span-2 text-ink-800">{formatAnswerValue(v)}</dd>
								</div>
							{/each}
						</dl>
					{/if}
				</div>
			</section>

			<!-- Right panel: anamnesis prose -->
			<section class="rounded-xl border border-praxis-200 bg-white shadow-sm">
				<div class="flex items-center justify-between border-b border-praxis-200 bg-praxis-50 px-4 py-2.5">
					<h3 class="text-xs font-semibold uppercase tracking-wider text-praxis-700">Anamnese-Text (zum Kopieren nach Medical Office)</h3>
					<div class="flex items-center gap-2">
						<button
							class="flex items-center gap-1.5 rounded-md border border-praxis-300 px-2 py-1 text-[11px] font-medium text-praxis-700 transition hover:bg-praxis-100"
							onclick={regenerate}
							disabled={busy}
							title="Erneut aus Antworten generieren"
						>
							<RefreshCw size={12} class={busy ? 'animate-spin' : ''} />
							Neu erzeugen
						</button>
						<button
							class="flex items-center gap-1.5 rounded-md bg-praxis-700 px-3 py-1 text-[11px] font-semibold text-white shadow-sm transition hover:bg-praxis-800"
							onclick={copyProse}
						>
							{#if copied}
								<Check size={12} /> Kopiert
							{:else}
								<Copy size={12} /> Kopieren
							{/if}
						</button>
					</div>
				</div>
				<div class="p-4">
					<textarea
						bind:value={prose}
						class="h-[55vh] w-full resize-none rounded-lg border border-praxis-300 bg-praxis-50/30 p-3 font-mono text-sm leading-relaxed text-ink-900 focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20"
						placeholder="Anamnese-Text erscheint hier nach Patientensubmission…"
					></textarea>
					<p class="mt-2 text-[11px] text-ink-500">
						Der Text ist vor dem Kopieren bearbeitbar. Über <em>Neu erzeugen</em> wird er aus den
						aktuellen Antworten neu zusammengesetzt.
					</p>
				</div>
			</section>
		</div>
	</div>
{/if}
