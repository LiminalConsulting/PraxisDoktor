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
		co_pilot: 'bg-teal-100 text-teal-800',
		autonomous: 'bg-emerald-100 text-emerald-800',
		placeholder: 'bg-stone-100 text-stone-600',
		dashboard_only: 'bg-amber-100 text-amber-800',
		decline: 'bg-stone-200 text-stone-500'
	};
</script>

<span class={`inline-block rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${colors[phase] || 'bg-stone-100 text-stone-600'}`}>
	{labels[phase] || phase}
</span>
