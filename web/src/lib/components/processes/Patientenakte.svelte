<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Patient, type Fall, type Befund, type CoherenceIssue } from '$lib/api';
	import { gaps as gapsRegistry } from '$lib/gaps';
	import AmbiguityBanner from '$lib/components/AmbiguityBanner.svelte';
	import { Search, User, Phone, Mail, MapPin, Calendar,
	         FileText, Activity, AlertTriangle, ShieldCheck, X } from 'lucide-svelte';

	let meta = $state<{ adapter: string; grounded_kinds: string[]; ungrounded_kinds: string[] } | null>(null);
	let mode = $state<'list' | 'coherence'>('list');

	// list pane
	let query = $state('');
	let patients = $state<Patient[]>([]);
	let listBusy = $state(false);

	// detail pane
	let selectedId = $state<string | null>(null);
	let detail = $state<{
		patient: Patient;
		faelle: { grounded: boolean; reason?: string; data: Fall[] };
		befunde: { grounded: boolean; reason?: string; data: Befund[] };
		coherence_issues: CoherenceIssue[];
	} | null>(null);
	let detailBusy = $state(false);

	// coherence pane
	let allIssues = $state<CoherenceIssue[]>([]);
	let coherenceScanned = $state(0);
	let coherenceBusy = $state(false);

	let pageGaps = $derived(meta ? gapsRegistry.patientenakte(meta.adapter, meta.ungrounded_kinds) : []);

	onMount(async () => {
		try {
			meta = await api.patientenakteMeta();
			await loadList();
		} catch (e) { /* not authorized → tool layout will handle */ }
	});

	async function loadList() {
		listBusy = true;
		try { patients = (await api.patientenakteList(query, 50)).patients; }
		finally { listBusy = false; }
	}

	async function selectPatient(pid: string) {
		selectedId = pid;
		detail = null;
		detailBusy = true;
		try {
			const r = await api.patientenakteGet(pid);
			detail = {
				patient: r.patient,
				faelle: r.faelle,
				befunde: r.befunde,
				coherence_issues: r.coherence_issues
			};
		} finally {
			detailBusy = false;
		}
	}

	async function loadCoherence() {
		coherenceBusy = true;
		try {
			const r = await api.patientenakteCoherence(200);
			allIssues = r.issues;
			coherenceScanned = r.scanned_patients;
		} finally {
			coherenceBusy = false;
		}
	}

	async function dismissIssue(issue: CoherenceIssue) {
		const note = prompt(`Begründung für das Ausblenden ("${issue.message}"):`);
		if (note === null) return;
		await api.patientenakteDismiss(issue.record_id, issue.rule, note);
		allIssues = allIssues.filter(
			(i) => !(i.record_id === issue.record_id && i.rule === issue.rule)
		);
	}

	function formatDate(d: string | null): string {
		if (!d) return '—';
		return new Date(d).toLocaleDateString('de-DE');
	}
	function fullName(p: Patient): string {
		return [p.titel, p.vorname, p.nachname].filter(Boolean).join(' ').trim();
	}
	function age(d: string | null): string {
		if (!d) return '';
		const dob = new Date(d);
		const today = new Date();
		let a = today.getFullYear() - dob.getFullYear();
		const m = today.getMonth() - dob.getMonth();
		if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) a--;
		return `${a} J.`;
	}
</script>

<div class="flex flex-col h-full">
	<AmbiguityBanner gaps={pageGaps} />

	<!-- Mode tabs -->
	<div class="border-b border-ink-200 px-4 py-2 flex gap-1 bg-white">
		<button
			class="px-3 py-1.5 rounded text-sm font-medium transition-colors
				{mode === 'list' ? 'bg-praxis-700 text-white' : 'text-ink-700 hover:bg-praxis-50'}"
			onclick={() => (mode = 'list')}
		>
			<User size={14} class="inline mr-1" /> Patienten
		</button>
		<button
			class="px-3 py-1.5 rounded text-sm font-medium transition-colors
				{mode === 'coherence' ? 'bg-praxis-700 text-white' : 'text-ink-700 hover:bg-praxis-50'}"
			onclick={() => { mode = 'coherence'; if (allIssues.length === 0) loadCoherence(); }}
		>
			<ShieldCheck size={14} class="inline mr-1" /> Datenqualität
		</button>
	</div>

	{#if mode === 'list'}
		<div class="flex-1 grid grid-cols-1 md:grid-cols-[320px_1fr] min-h-0">
			<!-- LIST PANE -->
			<aside class="border-r border-ink-200 flex flex-col min-h-0 bg-praxis-50/40">
				<div class="p-3 border-b border-ink-200 bg-white">
					<div class="relative">
						<Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
						<input
							type="text"
							bind:value={query}
							onkeydown={(e) => e.key === 'Enter' && loadList()}
							oninput={() => { /* debounce later */ }}
							placeholder="Name, ID oder PLZ"
							class="w-full pl-9 pr-3 py-2 rounded-md border border-ink-300 bg-white text-sm focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20"
						/>
					</div>
					<div class="text-xs text-ink-500 mt-2">
						{patients.length} Patient{patients.length === 1 ? '' : 'en'} · Adapter: {meta?.adapter ?? '…'}
					</div>
				</div>
				<div class="overflow-y-auto flex-1">
					{#if listBusy && patients.length === 0}
						<div class="p-6 text-center text-ink-500 text-sm">Lädt …</div>
					{:else if patients.length === 0}
						<div class="p-6 text-center text-ink-500 text-sm">Keine Treffer.</div>
					{:else}
						<ul>
							{#each patients as p}
								<li>
									<button
										class="w-full text-left px-3 py-2.5 border-b border-ink-100 hover:bg-praxis-100/40 transition
											{selectedId === p.id ? 'bg-praxis-100/60' : ''}"
										onclick={() => selectPatient(p.id)}
									>
										<div class="font-medium text-ink-900 text-sm">
											{fullName(p)}
										</div>
										<div class="text-xs text-ink-500 mt-0.5 flex justify-between">
											<span>{p.id}</span>
											<span>{formatDate(p.geburtsdatum)} {age(p.geburtsdatum)}</span>
										</div>
									</button>
								</li>
							{/each}
						</ul>
					{/if}
				</div>
			</aside>

			<!-- DETAIL PANE -->
			<section class="overflow-y-auto p-6 bg-white">
				{#if !selectedId}
					<div class="h-full grid place-items-center text-ink-400 text-sm">
						Wählen Sie einen Patienten aus der Liste.
					</div>
				{:else if detailBusy}
					<div class="text-ink-500 text-sm">Lädt Akte …</div>
				{:else if detail}
					{@const p = detail.patient}
					<div class="max-w-3xl">
						<header class="mb-6">
							<h2 class="text-2xl font-semibold text-praxis-900">{fullName(p)}</h2>
							<div class="text-sm text-ink-500 mt-1 flex flex-wrap gap-x-4 gap-y-1">
								<span>{p.id}</span>
								{#if p.geburtsdatum}<span>{formatDate(p.geburtsdatum)} ({age(p.geburtsdatum)})</span>{/if}
								{#if p.geschlecht}<span>{p.geschlecht === 'M' ? 'männlich' : p.geschlecht === 'W' ? 'weiblich' : 'divers'}</span>{/if}
							</div>
						</header>

						<!-- Coherence issues for this patient -->
						{#if detail.coherence_issues.length > 0}
							<div class="mb-6 rounded-lg border border-amber-300 bg-amber-50 p-4">
								<div class="font-semibold text-amber-900 mb-2 flex items-center gap-2">
									<AlertTriangle size={16} /> Datenqualität ({detail.coherence_issues.length})
								</div>
								<ul class="space-y-1.5 text-sm text-amber-900/90">
									{#each detail.coherence_issues as i}
										<li>· {i.message}{#if i.suggestion}<span class="text-amber-700/80"> — {i.suggestion}</span>{/if}</li>
									{/each}
								</ul>
							</div>
						{/if}

						<!-- Master fields -->
						<div class="grid gap-x-6 gap-y-3 sm:grid-cols-2 mb-8">
							{#each [
								['Anrede', p.anrede],
								['Muttersprache', p.muttersprache],
								['Adresse', p.strasse ? `${p.strasse} ${p.hausnr ?? ''}` : null],
								['Ort', p.plz || p.ort ? `${p.plz ?? ''} ${p.ort ?? ''}`.trim() : null],
								['Telefon (privat)', p.telefon_privat],
								['Telefon (mobil)', p.telefon_mobil],
								['E-Mail', p.email]
							] as [label, value]}
								<div>
									<div class="text-xs uppercase tracking-wide text-ink-500">{label}</div>
									<div class="text-sm text-ink-900 mt-0.5">{value || '—'}</div>
								</div>
							{/each}
						</div>

						<!-- Fälle -->
						<div class="mb-8">
							<div class="flex items-center gap-2 mb-3">
								<FileText size={16} class="text-praxis-700" />
								<h3 class="font-semibold text-praxis-900">Fälle</h3>
								{#if !detail.faelle.grounded}
									<span class="text-xs px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300">
										Schema unsicher
									</span>
								{/if}
							</div>
							{#if detail.faelle.data.length === 0}
								<div class="text-sm text-ink-500 italic">Keine Fälle.</div>
							{:else}
								<table class="w-full text-sm">
									<thead class="text-xs text-ink-500 border-b border-ink-200">
										<tr><th class="text-left py-1.5 pr-3">Quartal</th><th class="text-left pr-3">Fallart</th><th class="text-left pr-3">Diagnosen</th><th class="text-left">Eröffnet</th></tr>
									</thead>
									<tbody>
										{#each detail.faelle.data as f}
											<tr class="border-b border-ink-100">
												<td class="py-2 pr-3 font-medium">{f.quartal}</td>
												<td class="pr-3"><span class="text-xs px-2 py-0.5 rounded bg-praxis-100 text-praxis-800">{f.fallart}</span></td>
												<td class="pr-3 text-ink-700">{f.diagnose_codes.join(', ') || '—'}</td>
												<td class="text-ink-500">{formatDate(f.eroeffnet_am)}</td>
											</tr>
										{/each}
									</tbody>
								</table>
							{/if}
						</div>

						<!-- Befunde -->
						<div>
							<div class="flex items-center gap-2 mb-3">
								<Activity size={16} class="text-praxis-700" />
								<h3 class="font-semibold text-praxis-900">Befunde</h3>
								{#if !detail.befunde.grounded}
									<span class="text-xs px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300">
										Schema unsicher
									</span>
								{/if}
							</div>
							{#if detail.befunde.data.length === 0}
								<div class="text-sm text-ink-500 italic">Keine Befunde.</div>
							{:else}
								<ul class="space-y-2">
									{#each detail.befunde.data as b}
										<li class="border border-ink-200 rounded-lg p-3">
											<div class="flex justify-between text-sm">
												<span class="font-medium text-praxis-900">{b.typ ?? 'Befund'}</span>
												<span class="text-ink-500 text-xs">{formatDate(b.erstellt_am)} · {b.ersteller ?? ''}</span>
											</div>
											<div class="text-sm text-ink-700 mt-1">{b.inhalt}</div>
										</li>
									{/each}
								</ul>
							{/if}
						</div>
					</div>
				{/if}
			</section>
		</div>
	{:else if mode === 'coherence'}
		<div class="flex-1 overflow-y-auto p-6 bg-white">
			<div class="max-w-4xl">
				<div class="flex items-baseline justify-between mb-4">
					<h2 class="text-xl font-semibold text-praxis-900">Datenqualität</h2>
					<div class="text-sm text-ink-500">
						{coherenceScanned} Patient{coherenceScanned === 1 ? '' : 'en'} geprüft · {allIssues.length} offene Hinweise
					</div>
				</div>
				<p class="text-sm text-ink-700 mb-6 max-w-prose">
					Automatische Prüfung auf Pflichtfeld-Vollständigkeit, Format-Korrektheit und
					grobe Plausibilität. Hinweise lassen sich ausblenden, wenn sie bewusst stehen
					bleiben sollen — z. B. bei Alt-Datensätzen.
				</p>

				{#if coherenceBusy}
					<div class="text-ink-500 text-sm">Prüft …</div>
				{:else if allIssues.length === 0}
					<div class="rounded-lg border border-praxis-200 bg-praxis-50 p-6 text-center text-praxis-800">
						<ShieldCheck size={24} class="mx-auto mb-2 text-praxis-600" />
						Keine offenen Hinweise. ✨
					</div>
				{:else}
					<ul class="space-y-2">
						{#each allIssues as i (i.record_id + ':' + i.rule)}
							<li class="border border-ink-200 rounded-lg p-4 flex gap-3 items-start">
								<div class="shrink-0 mt-0.5
									{i.severity === 'error' ? 'text-red-600' : i.severity === 'warning' ? 'text-amber-600' : 'text-ink-400'}">
									<AlertTriangle size={18} />
								</div>
								<div class="flex-1 min-w-0">
									<div class="text-xs text-ink-500 mb-1">
										{i.record_kind} · {i.record_id} · {i.rule}
									</div>
									<div class="text-sm text-ink-900">{i.message}</div>
									{#if i.suggestion}
										<div class="text-sm text-ink-600 mt-1">→ {i.suggestion}</div>
									{/if}
								</div>
								<div class="shrink-0 flex gap-2">
									<button
										onclick={() => selectPatient(i.record_id).then(() => mode = 'list')}
										class="text-xs px-2.5 py-1 rounded border border-ink-300 text-ink-700 hover:bg-praxis-50"
									>
										Anzeigen
									</button>
									<button
										onclick={() => dismissIssue(i)}
										title="Ausblenden"
										class="text-xs px-2 py-1 rounded text-ink-500 hover:bg-ink-100"
									>
										<X size={14} />
									</button>
								</div>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		</div>
	{/if}
</div>

<!-- Local helper component (defined inline via snippet syntax not yet used; small enough to inline as markup) -->
<style>
	/* nothing custom — Tailwind covers the layout */
</style>
