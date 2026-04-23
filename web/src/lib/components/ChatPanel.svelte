<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { api, type ChatMessage } from '$lib/api';
	import { wsClient } from '$lib/ws';
	import { me } from '$lib/stores/auth';
	import { Send } from 'lucide-svelte';

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

	function fmt(iso: string) {
		return new Date(iso).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
	}
</script>

<aside
	class="flex h-full flex-col border-l border-praxis-200 bg-white transition-all duration-200"
	class:w-80={open}
	class:w-0={!open}
	class:overflow-hidden={!open}
>
	<header class="flex h-12 items-center border-b border-praxis-200 bg-praxis-100 px-4">
		<span class="text-xs font-semibold uppercase tracking-wider text-praxis-700">Prozess-Chat</span>
	</header>
	<div bind:this={scroller} class="flex-1 space-y-2 overflow-y-auto bg-praxis-50 p-3">
		{#each messages as m (m.id)}
			{@const mine = m.user_id === $me?.id}
			<div class={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
				<div
					class={`max-w-[85%] rounded-2xl px-3 py-2 text-sm shadow-sm ${mine
						? 'rounded-br-sm bg-praxis-700 text-white'
						: 'rounded-bl-sm bg-white text-ink-900 ring-1 ring-praxis-200'}`}
				>
					<div class={`text-[10px] font-medium uppercase tracking-wider ${mine ? 'text-white/70' : 'text-ink-400'}`}>
						{m.user_id} · {fmt(m.created_at)}
					</div>
					<div class="mt-0.5 whitespace-pre-wrap leading-snug">{m.body}</div>
				</div>
			</div>
		{/each}
		{#if messages.length === 0}
			<p class="mt-4 text-center text-xs text-ink-400">Noch keine Nachrichten.</p>
		{/if}
	</div>
	<form onsubmit={send} class="flex items-center gap-2 border-t border-praxis-200 bg-white p-2">
		<input
			type="text"
			bind:value={input}
			placeholder="Nachricht schreiben…"
			class="flex-1 rounded-lg border border-praxis-300 bg-white px-3 py-1.5 text-sm focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20"
		/>
		<button
			type="submit"
			class="flex h-8 w-8 items-center justify-center rounded-lg bg-praxis-700 text-white transition hover:bg-praxis-800 disabled:opacity-50"
			disabled={!input.trim()}
			title="Senden"
		>
			<Send size={14} />
		</button>
	</form>
</aside>
