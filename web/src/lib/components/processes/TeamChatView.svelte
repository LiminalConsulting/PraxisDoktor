<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { api, type ChatMessage } from '$lib/api';
	import { wsClient } from '$lib/ws';
	import { me } from '$lib/stores/auth';

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

<div class="mx-auto flex h-[calc(100vh-7.5rem)] max-w-3xl flex-col rounded-xl border border-stone-200 bg-white">
	<div bind:this={scroller} class="flex-1 space-y-2 overflow-y-auto p-4">
		{#each messages as m (m.id)}
			<div
				class="rounded-lg px-3 py-2 text-sm {m.user_id === $me?.id
					? 'ml-12 bg-teal-50'
					: 'mr-12 bg-stone-100'}"
			>
				<div class="text-[10px] font-medium uppercase tracking-wide text-stone-500">
					{m.user_id} · {fmt(m.created_at)}
				</div>
				<div class="whitespace-pre-wrap text-stone-900">{m.body}</div>
			</div>
		{/each}
		{#if messages.length === 0}
			<p class="mt-4 text-center text-xs text-stone-400">Team-Chat ist leer. Schreiben Sie die erste Nachricht.</p>
		{/if}
	</div>
	<form on:submit={send} class="border-t border-stone-200 p-3">
		<input
			type="text"
			bind:value={input}
			placeholder="Nachricht an das Team…"
			class="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
		/>
	</form>
</div>
