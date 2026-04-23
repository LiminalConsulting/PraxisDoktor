<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Process } from '$lib/api';
	import ProcessIcon from '$lib/components/ProcessIcon.svelte';
	import PhaseBadge from '$lib/components/PhaseBadge.svelte';
	import { Construction } from 'lucide-svelte';

	let { pid }: { pid: string } = $props();
	let proc = $state<Process | null>(null);

	onMount(async () => {
		try {
			proc = await api.processMeta(pid);
		} catch {}
	});
</script>

<div class="mx-auto max-w-2xl">
	<div class="rounded-xl border border-dashed border-praxis-300 bg-white p-10 text-center">
		<div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-praxis-100 text-praxis-700">
			<Construction size={26} />
		</div>
		<h2 class="text-base font-semibold text-ink-900">{proc?.display_name ?? pid}</h2>
		<p class="mx-auto mt-2 max-w-md text-sm text-ink-500">
			Dieses Werkzeug ist als Platzhalter angelegt und wird in einer kommenden
			Iteration gemeinsam mit dem Praxisteam ausgebaut.
		</p>

		{#if proc}
			<div class="mx-auto mt-6 grid max-w-md grid-cols-2 gap-x-4 gap-y-3 rounded-lg bg-praxis-50 p-4 text-left text-xs">
				<div>
					<div class="mb-0.5 text-[10px] font-semibold uppercase tracking-wider text-praxis-700">Surface</div>
					<div class="text-ink-700">{proc.surface}</div>
				</div>
				<div>
					<div class="mb-0.5 text-[10px] font-semibold uppercase tracking-wider text-praxis-700">Phase</div>
					<PhaseBadge phase={proc.phase} />
				</div>
				<div>
					<div class="mb-0.5 text-[10px] font-semibold uppercase tracking-wider text-praxis-700">Inputs</div>
					<div class="text-ink-700">{proc.inputs.join(', ') || '—'}</div>
				</div>
				<div>
					<div class="mb-0.5 text-[10px] font-semibold uppercase tracking-wider text-praxis-700">Outputs</div>
					<div class="text-ink-700">{proc.outputs.join(', ') || '—'}</div>
				</div>
			</div>
		{/if}
	</div>
</div>
