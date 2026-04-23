<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { dndzone, type DndEvent } from 'svelte-dnd-action';
	import { api, type Process } from '$lib/api';
	import { wsClient } from '$lib/ws';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import ProcessIcon from '$lib/components/ProcessIcon.svelte';
	import PhaseBadge from '$lib/components/PhaseBadge.svelte';

	let cards = $state<Process[]>([]);
	let activity = $state<Record<string, number>>({});
	let unsubs: Array<() => void> = [];

	async function load() {
		const res = await api.dashboard();
		cards = res.processes;
		// subscribe to chat channels for activity blink
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

<div class="min-h-screen bg-stone-50">
	<AppHeader />

	<main class="mx-auto max-w-6xl p-6">
		<h1 class="mb-1 text-2xl font-semibold text-stone-900">Dashboard</h1>
		<p class="mb-6 text-sm text-stone-500">
			Ziehen, um die Reihenfolge zu ändern. Doppelklick öffnet das Werkzeug.
		</p>

		<section
			class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
			use:dndzone={{ items: cards, flipDurationMs: 200, dropTargetStyle: {} }}
			on:consider={handleDnd}
			on:finalize={handleDndFinalize}
		>
			{#each cards as c (c.id)}
				<div
					class="group relative cursor-grab rounded-xl border border-stone-200 bg-white p-4 shadow-sm transition hover:border-teal-300 hover:shadow"
					on:dblclick={() => open(c)}
					role="button"
					tabindex="0"
					on:keydown={(e) => (e.key === 'Enter' ? open(c) : null)}
				>
					<div class="flex items-start justify-between">
						<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-stone-100 text-stone-700">
							<ProcessIcon name={c.icon} />
						</div>
						<PhaseBadge phase={c.phase} />
					</div>

					<h3 class="mt-3 text-sm font-medium text-stone-900">{c.display_name}</h3>
					<p class="mt-0.5 text-xs text-stone-500">
						{c.surface === 'tool' ? 'Werkzeug' : c.surface === 'conversation' ? 'Gespräch' : 'Übersicht'}
					</p>

					{#if activity[c.id] > 0}
						<span
							class="absolute right-3 top-3 inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-teal-600 px-1.5 text-[10px] font-semibold text-white"
							title="Neue Aktivität"
						>
							{activity[c.id]}
						</span>
					{/if}

					<button
						class="mt-3 text-xs font-medium text-teal-700 hover:underline"
						on:click|stopPropagation={() => open(c)}
					>
						Öffnen →
					</button>
				</div>
			{/each}
		</section>

		{#if cards.length === 0}
			<p class="mt-8 text-center text-sm text-stone-500">Keine Prozesse für Ihre Rolle.</p>
		{/if}
	</main>
</div>
