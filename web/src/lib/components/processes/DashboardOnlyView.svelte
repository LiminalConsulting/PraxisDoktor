<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Process } from '$lib/api';
	import ProcessIcon from '$lib/components/ProcessIcon.svelte';
	import PhaseBadge from '$lib/components/PhaseBadge.svelte';
	import { Eye, AlertCircle } from 'lucide-svelte';

	let { pid }: { pid: string } = $props();
	let proc = $state<Process | null>(null);

	onMount(async () => {
		try { proc = await api.processMeta(pid); } catch {}
	});

	const phaseExplain: Record<string, string> = {
		dashboard_only:
			'Dieser Prozess wird beobachtet, aber nicht aktiv automatisiert. Wir lesen Daten aus dem bestehenden System und stellen sie hier transparent dar.',
		decline:
			'Dieser Prozess ist bewusst nicht Teil des Werkzeug-Umfangs (z. B. wegen regulatorischer Komplexität). Er wird im bestehenden System weitergeführt; hier nur als Kontext sichtbar.'
	};
</script>

<div class="mx-auto max-w-3xl space-y-4">
	<div class="rounded-xl border border-praxis-200 bg-white p-6 shadow-sm">
		<div class="flex items-start justify-between gap-4">
			<div class="flex items-center gap-3">
				<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-praxis-100 text-praxis-700">
					{#if proc}<ProcessIcon name={proc.icon} size={22} />{/if}
				</div>
				<div>
					<h2 class="text-base font-semibold text-ink-900">{proc?.display_name ?? pid}</h2>
					<div class="mt-0.5 flex items-center gap-2 text-xs text-ink-500">
						<Eye size={13} />
						<span>Read-only Übersicht</span>
						{#if proc}
							<span class="opacity-50">·</span>
							<PhaseBadge phase={proc.phase} />
						{/if}
					</div>
				</div>
			</div>
		</div>

		{#if proc}
			<p class="mt-4 rounded-lg bg-praxis-50 p-3 text-sm text-ink-700">
				{phaseExplain[proc.phase] ?? 'Übersichtsansicht — Inhalt wird in einer kommenden Iteration angebunden.'}
			</p>
		{/if}
	</div>

	<div class="rounded-xl border border-dashed border-praxis-300 bg-white p-8 text-center">
		<AlertCircle class="mx-auto mb-3 text-ink-400" size={28} />
		<p class="text-sm text-ink-500">
			Hier werden in einer kommenden Iteration die aktuellen Live-Daten dieses Prozesses angezeigt.
		</p>
		{#if proc}
			<div class="mx-auto mt-6 grid max-w-md grid-cols-2 gap-x-4 gap-y-3 rounded-lg bg-praxis-50 p-4 text-left text-xs">
				<div>
					<div class="mb-0.5 text-[10px] font-semibold uppercase tracking-wider text-praxis-700">Quelle</div>
					<div class="text-ink-700">{proc.inputs.join(', ') || '—'}</div>
				</div>
				<div>
					<div class="mb-0.5 text-[10px] font-semibold uppercase tracking-wider text-praxis-700">Signal</div>
					<div class="text-ink-700">{proc.outputs.join(', ') || '—'}</div>
				</div>
			</div>
		{/if}
	</div>
</div>
