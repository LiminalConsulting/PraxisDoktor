<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { api, type ChatMessage } from '$lib/api';
	import { wsClient } from '$lib/ws';
	import { me } from '$lib/stores/auth';

	let { processId, open = false }: { processId: string; open?: boolean } = $props();

	let messages = $state<ChatMessage[]>([]);
	let input = $state('');
	let scroller: HTMLDivElement | null = null;
	let unsub: (() => void) | null = null;

	async function load() {
		messages = await api.listMessages(processId);
		queueScroll();
	}

	function queueScroll() {
		setTimeout(() => {
			if (scroller) scroller.scrollTop = scroller.scrollHeight;
		}, 30);
	}

	async function send(e: Event) {
		e.preventDefault();
		const body = input.trim();
		if (!body) return;
		input = '';
		try {
			await api.sendMessage(processId, body);
		} catch {}
	}

	onMount(() => {
		load();
		unsub = wsClient.subscribe(`chat:${processId}`, (ev) => {
			if (ev.type === 'chat_message') {
				messages = [...messages, ev.message];
				queueScroll();
			}
		});
	});
	onDestroy(() => unsub?.());

	function fmtTime(iso: string) {
		const d = new Date(iso);
		return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
	}
</script>

<aside
	class="flex h-full flex-col border-l border-stone-200 bg-white transition-all duration-200"
	class:w-80={open}
	class:w-0={!open}
	class:overflow-hidden={!open}
>
	<header class="flex h-10 items-center border-b border-stone-200 px-3 text-sm font-medium text-stone-800">
		Chat
	</header>
	<div bind:this={scroller} class="flex-1 space-y-2 overflow-y-auto p-3">
		{#each messages as m (m.id)}
			<div
				class="rounded-lg px-3 py-2 text-sm {m.user_id === $me?.id
					? 'ml-6 bg-teal-50 text-stone-900'
					: 'mr-6 bg-stone-100 text-stone-900'}"
			>
				<div class="text-[10px] font-medium uppercase tracking-wide text-stone-500">
					{m.user_id} · {fmtTime(m.created_at)}
				</div>
				<div class="whitespace-pre-wrap">{m.body}</div>
			</div>
		{/each}
		{#if messages.length === 0}
			<p class="mt-4 text-center text-xs text-stone-400">Noch keine Nachrichten.</p>
		{/if}
	</div>
	<form on:submit={send} class="border-t border-stone-200 p-2">
		<input
			type="text"
			bind:value={input}
			placeholder="Nachricht schreiben…"
			class="w-full rounded-lg border border-stone-300 px-3 py-1.5 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
		/>
	</form>
</aside>
