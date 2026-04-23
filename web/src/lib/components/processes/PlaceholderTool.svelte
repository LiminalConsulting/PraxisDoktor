<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Process } from '$lib/api';

	let { pid }: { pid: string } = $props();
	let proc = $state<Process | null>(null);

	onMount(async () => {
		try {
			proc = await api.processMeta(pid);
		} catch {}
	});
</script>

<div class="rounded-xl border border-dashed border-stone-300 bg-white p-8 text-center">
	<p class="text-sm text-stone-500">
		<span class="font-medium text-stone-700">{proc?.display_name ?? pid}</span>
		— dieses Werkzeug ist als Platzhalter angelegt und wird im nächsten Schritt
		gemeinsam mit dem Praxisteam ausgebaut.
	</p>

	{#if proc}
		<dl class="mx-auto mt-6 grid max-w-md grid-cols-2 gap-x-6 gap-y-2 text-left text-xs">
			<dt class="text-stone-500">Surface</dt><dd>{proc.surface}</dd>
			<dt class="text-stone-500">Phase</dt><dd>{proc.phase}</dd>
			<dt class="text-stone-500">Inputs</dt><dd>{proc.inputs.join(', ') || '—'}</dd>
			<dt class="text-stone-500">Outputs</dt><dd>{proc.outputs.join(', ') || '—'}</dd>
		</dl>
	{/if}
</div>
