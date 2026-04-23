<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { dndzone, type DndEvent } from 'svelte-dnd-action';
	import { api, type Process } from '$lib/api';
	import { wsClient } from '$lib/ws';
	import { me } from '$lib/stores/auth';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import ProcessIcon from '$lib/components/ProcessIcon.svelte';
	import PhaseBadge from '$lib/components/PhaseBadge.svelte';

	let cards = $state<Process[]>([]);
	let activity = $state<Record<string, number>>({});
	let unsubs: Array<() => void> = [];

	const surfaceLabel: Record<string, string> = {
		tool: 'Werkzeug',
		conversation: 'Gespräch',
		dashboard_only: 'Übersicht'
	};

	async function load() {
		const res = await api.dashboard();
		cards = res.processes;
		for (const u of unsubs) u();
		unsubs = [];
		for (const c of cards) {
			activity[c.id] = c.chat_count ?? 0;
			const off = wsClient.subscribe(`chat:${c.id}`, (ev) => {
				if (ev.type === 'chat_message') {
					activity[c.id] = (activity[c.id] || 0) + 1;
				}
			});
			unsubs.push(off);
		}
		activity = activity;
	}

	function handleDnd(e: CustomEvent<DndEvent<Process>>) {
		cards = e.detail.items;
	}
	function handleDndFinalize(e: CustomEvent<DndEvent<Process>>) {
		cards = e.detail.items;
		api.saveLayout(cards.map((c) => c.id)).catch(() => {});
	}

	function open(c: Process) {
		goto(`/tool/${c.id}`);
	}

	onMount(load);
</script>

<div class="flex min-h-screen flex-col bg-praxis-50">
	<AppHeader />

	<main class="mx-auto w-full max-w-7xl flex-1 px-6 py-8">
		<div class="mb-6 flex items-end justify-between">
			<div>
				<h1 class="text-[22px] font-semibold tracking-tight text-praxis-800">
					Guten Tag{$me?.display_name ? `, ${$me.display_name.split(' ')[0]}` : ''}.
				</h1>
				<p class="mt-1 text-sm text-ink-500">
					Ihre Werkzeuge und Prozesse. Karten lassen sich per Ziehen neu anordnen, Doppelklick öffnet ein Werkzeug.
				</p>
			</div>
			<div class="hidden text-right text-xs text-ink-500 sm:block">
				{cards.length}
				{cards.length === 1 ? 'Prozess' : 'Prozesse'}
			</div>
		</div>

		<section
			class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
			use:dndzone={{ items: cards, flipDurationMs: 200, dropTargetStyle: {} }}
			onconsider={handleDnd}
			onfinalize={handleDndFinalize}
		>
			{#each cards as c (c.id)}
				<div
					class="group relative flex cursor-grab flex-col rounded-xl border border-praxis-200 bg-white p-4 shadow-[0_1px_2px_rgba(60,90,70,0.06)] transition hover:-translate-y-0.5 hover:border-praxis-400 hover:shadow-[0_4px_18px_rgba(60,90,70,0.12)] active:cursor-grabbing"
					ondblclick={() => open(c)}
					role="button"
					tabindex="0"
					onkeydown={(e) => (e.key === 'Enter' ? open(c) : null)}
				>
					<div class="flex items-start justify-between">
						<div class="flex h-11 w-11 items-center justify-center rounded-lg bg-praxis-100 text-praxis-700 transition group-hover:bg-praxis-700 group-hover:text-white">
							<ProcessIcon name={c.icon} size={22} />
						</div>
						<PhaseBadge phase={c.phase} />
					</div>

					<h3 class="mt-3 text-sm font-semibold text-ink-900">{c.display_name}</h3>
					<p class="mt-0.5 text-xs text-ink-500">{surfaceLabel[c.surface] ?? c.surface}</p>

					<div class="mt-auto flex items-end justify-between pt-4">
						<button
							class="text-xs font-semibold text-praxis-700 transition hover:text-praxis-800"
							onclick={(e) => {
								e.stopPropagation();
								open(c);
							}}
						>
							Öffnen →
						</button>
						{#if activity[c.id] > 0}
							<span
								class="inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-praxis-700 px-1.5 text-[10px] font-bold text-white"
								title="Neue Aktivität"
							>
								{activity[c.id]}
							</span>
						{/if}
					</div>
				</div>
			{/each}
		</section>

		{#if cards.length === 0}
			<div class="rounded-xl border border-dashed border-praxis-300 bg-white p-10 text-center">
				<p class="text-sm text-ink-500">Keine Prozesse für Ihre Rolle freigeschaltet.</p>
			</div>
		{/if}
	</main>

	<footer class="mx-auto w-full max-w-7xl px-6 pb-6 text-[11px] text-ink-400">
		PraxisDoktor · alle Daten verbleiben in der Praxis · Entwicklungsstand
	</footer>
</div>
