<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type Process } from '$lib/api';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import ChatPanel from '$lib/components/ChatPanel.svelte';
	import ProcessIcon from '$lib/components/ProcessIcon.svelte';
	import { MessageSquare, Undo2 } from 'lucide-svelte';

	let {
		processId,
		showChatToggle = true,
		showUndo = false,
		onUndo,
		children
	}: {
		processId: string;
		showChatToggle?: boolean;
		showUndo?: boolean;
		onUndo?: () => void;
		children: any;
	} = $props();

	let allProcs = $state<Process[]>([]);
	let chatOpen = $state(false);
	let current = $derived(allProcs.find((p) => p.id === processId));

	async function load() {
		const res = await api.dashboard();
		allProcs = res.processes;
	}
	onMount(load);

	function nav(pid: string) {
		if (pid === processId) return;
		goto(`/tool/${pid}`);
	}
</script>

<div class="flex h-screen flex-col bg-stone-50">
	<AppHeader />

	<div class="flex flex-1 overflow-hidden">
		<!-- Left: vertical tab bar of accessible processes -->
		<nav class="flex w-14 flex-col items-center gap-1 border-r border-stone-200 bg-white py-2">
			{#each allProcs as p (p.id)}
				<button
					class="flex h-10 w-10 items-center justify-center rounded-lg transition hover:bg-stone-100"
					class:bg-teal-100={p.id === processId}
					class:text-teal-800={p.id === processId}
					class:text-stone-600={p.id !== processId}
					title={p.display_name}
					on:click={() => nav(p.id)}
				>
					<ProcessIcon name={p.icon} size={18} />
				</button>
			{/each}
		</nav>

		<!-- Center: tool content -->
		<main class="flex-1 overflow-y-auto">
			<div class="border-b border-stone-200 bg-white px-6 py-3 flex items-center justify-between">
				<h1 class="text-lg font-semibold text-stone-900">
					{current?.display_name ?? processId}
				</h1>
				<div class="flex items-center gap-2">
					{#if showUndo}
						<button
							class="flex items-center gap-1 rounded px-2 py-1 text-sm text-stone-600 hover:bg-stone-100"
							on:click={() => onUndo?.()}
							title="Letzte Aktion rückgängig (Cmd+Z)"
						>
							<Undo2 size={14} /> Rückgängig
						</button>
					{/if}
				</div>
			</div>
			<div class="p-6">
				{@render children()}
			</div>
		</main>

		<!-- Right: chat trigger + panel -->
		{#if showChatToggle}
			<div class="flex">
				<ChatPanel processId={processId} open={chatOpen} />
				<button
					class="flex w-9 items-center justify-center border-l border-stone-200 bg-white text-stone-600 hover:bg-stone-100"
					on:click={() => (chatOpen = !chatOpen)}
					title={chatOpen ? 'Chat schließen' : 'Chat öffnen'}
				>
					<MessageSquare size={16} />
				</button>
			</div>
		{/if}
	</div>
</div>
