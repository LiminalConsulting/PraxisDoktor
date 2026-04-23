<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { api, type ChatMessage } from '$lib/api';
	import { wsClient } from '$lib/ws';
	import { me } from '$lib/stores/auth';
	import { Send } from 'lucide-svelte';

	let messages = $state<ChatMessage[]>([]);
	let input = $state('');
	let scroller: HTMLDivElement | null = null;
	let unsub: (() => void) | null = null;
	const pid = 'team_chat';

	async function load() {
		messages = await api.listMessages(pid);
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
		await api.sendMessage(pid, body);
	}
	onMount(() => {
		load();
		unsub = wsClient.subscribe(`chat:${pid}`, (ev) => {
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

<div class="mx-auto flex h-full max-w-3xl flex-col overflow-hidden rounded-xl border border-praxis-200 bg-white shadow-sm">
	<div bind:this={scroller} class="flex-1 space-y-2 overflow-y-auto bg-praxis-50 p-4">
		{#each messages as m (m.id)}
			{@const mine = m.user_id === $me?.id}
			<div class={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
				<div
					class={`max-w-[80%] rounded-2xl px-3 py-2 text-sm shadow-sm ${mine
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
			<p class="mt-4 text-center text-xs text-ink-400">Team-Chat ist leer. Schreiben Sie die erste Nachricht.</p>
		{/if}
	</div>
	<form onsubmit={send} class="flex items-center gap-2 border-t border-praxis-200 bg-white p-3">
		<input
			type="text"
			bind:value={input}
			placeholder="Nachricht an das Team…"
			class="flex-1 rounded-lg border border-praxis-300 px-3 py-2 text-sm focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20"
		/>
		<button
			type="submit"
			class="flex h-9 items-center gap-1.5 rounded-lg bg-praxis-700 px-3 text-sm font-medium text-white transition hover:bg-praxis-800 disabled:opacity-50"
			disabled={!input.trim()}
		>
			<Send size={14} /> Senden
		</button>
	</form>
</div>
