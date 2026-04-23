<script lang="ts">
	let { phase }: { phase: string } = $props();

	const labels: Record<string, string> = {
		co_pilot: 'Co-Pilot',
		autonomous: 'Autonom',
		placeholder: 'Geplant',
		dashboard_only: 'Beobachtung',
		decline: 'Nicht im Umfang'
	};
	const colors: Record<string, string> = {
		co_pilot: 'bg-praxis-100 text-praxis-800 ring-1 ring-praxis-200',
		autonomous: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
		placeholder: 'bg-ink-100 text-ink-500 ring-1 ring-ink-200',
		dashboard_only: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
		decline: 'bg-ink-100 text-ink-400 ring-1 ring-ink-200'
	};
</script>

<span class={`inline-block rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${colors[phase] ?? 'bg-ink-100 text-ink-500'}`}>
	{labels[phase] ?? phase}
</span>
