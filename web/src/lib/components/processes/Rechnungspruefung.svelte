<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type RuleIssue, type Patient } from '$lib/api';
	import { gaps as gapsRegistry } from '$lib/gaps';
	import AmbiguityBanner from '$lib/components/AmbiguityBanner.svelte';
	import { Receipt, AlertTriangle, AlertCircle, Info, CheckCircle2, X, ArrowLeft } from 'lucide-svelte';

	let meta = $state<{ adapter: string; ungrounded_kinds: string[]; rule_count: number } | null>(null);
	let quartal = $state(currentQuartal());

	type FallSummary = {
		fall_id: string;
		patient_id: string;
		patient_name: string;
		position_count: number;
		issue_count: number;
		error_count: number;
		warning_count: number;
		katalog: string[];
	};

	let summary = $state<{
		fall_count: number;
		position_count: number;
		issue_count: number;
		error_count: number;
		faelle: FallSummary[];
	} | null>(null);
	let summaryBusy = $state(false);

	let selectedFall = $state<string | null>(null);
	let detail = $state<{
		fall_id: string;
		patient: Patient;
		positions: any[];
		issues: RuleIssue[];
		dismissed_issues: RuleIssue[];
	} | null>(null);
	let detailBusy = $state(false);

	let pageGaps = $derived(meta ? gapsRegistry.rechnungspruefung(meta.adapter, meta.ungrounded_kinds, meta.rule_count) : []);

	function currentQuartal(): string {
		const d = new Date();
		return `${d.getFullYear()}Q${Math.floor(d.getMonth() / 3) + 1}`;
	}

	onMount(async () => {
		try {
			meta = await api.rechnungspruefungMeta();
			await loadQuartal();
		} catch {}
	});

	async function loadQuartal() {
		summaryBusy = true;
		summary = null;
		selectedFall = null;
		detail = null;
		try {
			summary = await api.rechnungspruefungQuartal(quartal);
		} finally {
			summaryBusy = false;
		}
	}

	async function selectFall(fid: string) {
		selectedFall = fid;
		detail = null;
		detailBusy = true;
		try {
			detail = await api.rechnungspruefungFall(fid);
		} finally {
			detailBusy = false;
		}
	}

	async function dismissIssue(i: RuleIssue) {
		if (!detail) return;
		const note = prompt(`Begründung für das Ausblenden ("${i.rule_name}"):`);
		if (note === null) return;
		await api.rechnungspruefungDismiss(detail.fall_id, i.rule_id, i.position_ids, note);
		detail.issues = detail.issues.filter(
			(x) => !(x.rule_id === i.rule_id && JSON.stringify(x.position_ids) === JSON.stringify(i.position_ids))
		);
	}

	async function markReady() {
		if (!detail) return;
		await api.rechnungspruefungMarkReady(detail.fall_id);
		// reload summary so this fall drops out of the "needs review" list
		await loadQuartal();
	}

	function severityColor(s: string): string {
		return s === 'error' ? 'text-red-600' : s === 'warning' ? 'text-amber-600' : 'text-ink-400';
	}
	function severityBg(s: string): string {
		return s === 'error' ? 'bg-red-50 border-red-200' : s === 'warning' ? 'bg-amber-50 border-amber-200' : 'bg-ink-50 border-ink-200';
	}
	function fmtEur(n: number | null | undefined): string {
		if (n == null) return '—';
		return n.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
	}
</script>

<div class="flex flex-col h-full">
	<AmbiguityBanner gaps={pageGaps} />

	<!-- Quartal selector -->
	<div class="border-b border-ink-200 px-4 py-2.5 flex items-center justify-between bg-white">
		<div class="flex items-center gap-3">
			<Receipt size={18} class="text-praxis-700" />
			<span class="font-semibold text-praxis-900">Rechnungsprüfung</span>
			<select
				bind:value={quartal}
				onchange={loadQuartal}
				class="px-3 py-1 rounded border border-ink-300 text-sm"
			>
				{#each ['2025Q4', '2026Q1', '2026Q2'] as q}<option value={q}>{q}</option>{/each}
			</select>
		</div>
		{#if meta}
			<div class="text-xs text-ink-500">
				{meta.rule_count} Regeln aktiv · Adapter {meta.adapter}
			</div>
		{/if}
	</div>

	{#if !selectedFall}
		<!-- SUMMARY VIEW -->
		<div class="flex-1 overflow-y-auto p-6 bg-white">
			<div class="max-w-5xl">
				{#if summaryBusy}
					<div class="text-ink-500 text-sm">Prüft Quartal …</div>
				{:else if summary}
					<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
						{#each [
							{ label: 'Fälle', value: summary.fall_count, accent: 'ok' as const },
							{ label: 'Positionen', value: summary.position_count, accent: 'ok' as const },
							{ label: 'Hinweise', value: summary.issue_count, accent: (summary.issue_count > 0 ? 'warn' : 'ok') as 'warn' | 'ok' },
							{ label: 'Fehler', value: summary.error_count, accent: (summary.error_count > 0 ? 'err' : 'ok') as 'err' | 'ok' }
						] as s}
							<div class="rounded-lg border border-ink-200 bg-white p-4">
								<div class="text-xs text-ink-500 uppercase tracking-wide">{s.label}</div>
								<div class="text-2xl font-semibold mt-1
									{s.accent === 'err' ? 'text-red-700' : s.accent === 'warn' ? 'text-amber-700' : 'text-praxis-900'}">
									{s.value}
								</div>
							</div>
						{/each}
					</div>

					{#if summary.faelle.length === 0}
						<div class="rounded-lg border border-praxis-200 bg-praxis-50 p-6 text-center">
							<CheckCircle2 size={28} class="mx-auto mb-2 text-praxis-600" />
							Keine Fälle in diesem Quartal.
						</div>
					{:else}
						<div class="border border-ink-200 rounded-lg overflow-hidden">
							<table class="w-full text-sm">
								<thead class="bg-praxis-50 text-xs uppercase tracking-wide text-ink-600">
									<tr>
										<th class="text-left px-4 py-2.5">Fall</th>
										<th class="text-left px-4 py-2.5">Patient</th>
										<th class="text-left px-4 py-2.5">Katalog</th>
										<th class="text-right px-4 py-2.5">Pos.</th>
										<th class="text-right px-4 py-2.5">Fehler</th>
										<th class="text-right px-4 py-2.5">Warn</th>
										<th class="px-4 py-2.5"></th>
									</tr>
								</thead>
								<tbody>
									{#each summary.faelle as f}
										<tr class="border-t border-ink-100 hover:bg-praxis-50/50 cursor-pointer"
											onclick={() => selectFall(f.fall_id)}>
											<td class="px-4 py-2.5 font-mono text-xs text-ink-700">{f.fall_id}</td>
											<td class="px-4 py-2.5">{f.patient_name}</td>
											<td class="px-4 py-2.5">
												{#each f.katalog as k}
													<span class="text-xs px-1.5 py-0.5 rounded bg-praxis-100 text-praxis-800 mr-1">{k}</span>
												{/each}
											</td>
											<td class="px-4 py-2.5 text-right text-ink-700">{f.position_count}</td>
											<td class="px-4 py-2.5 text-right">
												{#if f.error_count > 0}
													<span class="text-red-700 font-medium">{f.error_count}</span>
												{:else}
													<span class="text-ink-300">—</span>
												{/if}
											</td>
											<td class="px-4 py-2.5 text-right">
												{#if f.warning_count > 0}
													<span class="text-amber-700">{f.warning_count}</span>
												{:else}
													<span class="text-ink-300">—</span>
												{/if}
											</td>
											<td class="px-4 py-2.5 text-right">
												<span class="text-praxis-600 text-xs">prüfen →</span>
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}
				{/if}
			</div>
		</div>
	{:else}
		<!-- DETAIL VIEW -->
		<div class="flex-1 overflow-y-auto bg-white">
			<div class="border-b border-ink-200 bg-praxis-50/40 px-6 py-3 flex items-center gap-3">
				<button
					onclick={() => { selectedFall = null; detail = null; }}
					class="p-1.5 rounded hover:bg-white text-ink-700"
					aria-label="Zurück"
				>
					<ArrowLeft size={18} />
				</button>
				<span class="font-mono text-sm text-ink-700">{selectedFall}</span>
				{#if detail}
					<span class="text-sm text-ink-700">·</span>
					<span class="font-semibold text-praxis-900">
						{detail.patient.vorname} {detail.patient.nachname}
					</span>
				{/if}
				<div class="flex-1"></div>
				{#if detail && detail.issues.filter(i => i.severity === 'error').length === 0}
					<button
						onclick={markReady}
						class="px-3 py-1.5 rounded-md bg-praxis-700 text-white text-sm font-medium hover:bg-praxis-800"
					>
						<CheckCircle2 size={14} class="inline mr-1" />
						Zur Abrechnung freigeben
					</button>
				{/if}
			</div>

			<div class="p-6 max-w-4xl">
				{#if detailBusy}
					<div class="text-ink-500 text-sm">Lädt …</div>
				{:else if detail}
					<!-- Issues -->
					{#if detail.issues.length > 0}
						<h3 class="text-sm uppercase tracking-wide text-ink-600 mb-3">
							Hinweise ({detail.issues.length})
						</h3>
						<ul class="space-y-2 mb-8">
							{#each detail.issues as i (i.rule_id + i.position_ids.join(','))}
								<li class="border rounded-lg p-4 flex gap-3 items-start {severityBg(i.severity)}">
									<div class="shrink-0 mt-0.5 {severityColor(i.severity)}">
										{#if i.severity === 'error'}<AlertCircle size={18} />
										{:else if i.severity === 'warning'}<AlertTriangle size={18} />
										{:else}<Info size={18} />
										{/if}
									</div>
									<div class="flex-1 min-w-0">
										<div class="flex items-baseline justify-between gap-2">
											<div class="font-medium text-ink-900">{i.rule_name}</div>
											<div class="text-xs text-ink-500 font-mono shrink-0">{i.rule_id}</div>
										</div>
										<div class="text-sm text-ink-800 mt-1">{i.message}</div>
										{#if i.suggestion}
											<div class="text-sm text-ink-600 mt-1">→ {i.suggestion}</div>
										{/if}
										{#if i.source}
											<div class="text-xs text-ink-500 mt-2">Quelle: {i.source}</div>
										{/if}
									</div>
									<button
										onclick={() => dismissIssue(i)}
										title="Als Falsch-Positiv markieren"
										class="shrink-0 p-1 text-ink-400 hover:text-ink-700 hover:bg-white rounded"
									>
										<X size={14} />
									</button>
								</li>
							{/each}
						</ul>
					{:else}
						<div class="rounded-lg border border-praxis-200 bg-praxis-50 p-4 mb-8 flex items-center gap-3">
							<CheckCircle2 size={20} class="text-praxis-600" />
							<div class="text-praxis-900 font-medium">Keine offenen Hinweise.</div>
						</div>
					{/if}

					<!-- Positions table -->
					<h3 class="text-sm uppercase tracking-wide text-ink-600 mb-3">
						Positionen ({detail.positions.length})
					</h3>
					<div class="border border-ink-200 rounded-lg overflow-hidden">
						<table class="w-full text-sm">
							<thead class="bg-praxis-50 text-xs uppercase text-ink-600">
								<tr>
									<th class="text-left px-3 py-2">Datum</th>
									<th class="text-left px-3 py-2">Katalog</th>
									<th class="text-left px-3 py-2">Code</th>
									<th class="text-left px-3 py-2">Bezeichnung</th>
									<th class="text-right px-3 py-2">Anzahl</th>
									<th class="text-right px-3 py-2">Faktor</th>
									<th class="text-right px-3 py-2">Betrag</th>
								</tr>
							</thead>
							<tbody>
								{#each detail.positions as p}
									<tr class="border-t border-ink-100">
										<td class="px-3 py-2 text-ink-700">{p.leistungsdatum ?? '—'}</td>
										<td class="px-3 py-2"><span class="text-xs px-1.5 py-0.5 rounded bg-praxis-100 text-praxis-800">{p.katalog}</span></td>
										<td class="px-3 py-2 font-mono text-xs">{p.code}</td>
										<td class="px-3 py-2 text-ink-700">{p.bezeichnung ?? '—'}</td>
										<td class="px-3 py-2 text-right text-ink-700">{p.anzahl}</td>
										<td class="px-3 py-2 text-right text-ink-700">{p.faktor ?? '—'}</td>
										<td class="px-3 py-2 text-right font-medium">{fmtEur(p.betrag_eur)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>

					{#if detail.dismissed_issues.length > 0}
						<details class="mt-6 text-sm">
							<summary class="cursor-pointer text-ink-500">
								{detail.dismissed_issues.length} Hinweis{detail.dismissed_issues.length === 1 ? '' : 'e'} ausgeblendet
							</summary>
							<ul class="mt-2 space-y-1">
								{#each detail.dismissed_issues as i}
									<li class="text-ink-500">· {i.rule_name}: {i.message}</li>
								{/each}
							</ul>
						</details>
					{/if}
				{/if}
			</div>
		</div>
	{/if}
</div>

