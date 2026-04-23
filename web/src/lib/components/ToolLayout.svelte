<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type Process } from '$lib/api';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import ChatPanel from '$lib/components/ChatPanel.svelte';
	import ProcessIcon from '$lib/components/ProcessIcon.svelte';
	import PhaseBadge from '$lib/components/PhaseBadge.svelte';
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

<div class="flex h-screen flex-col bg-praxis-50">
	<AppHeader />

	<div class="flex flex-1 overflow-hidden">
		<!-- Left: vertical tab bar of accessible processes -->
		<nav class="flex w-16 flex-col items-center gap-1 border-r border-praxis-200 bg-white py-3">
			{#each allProcs as p (p.id)}
				<button
					class={`group relative flex h-11 w-11 items-center justify-center rounded-lg transition
						${p.id === processId
							? 'bg-praxis-700 text-white shadow-sm'
							: 'text-ink-500 hover:bg-praxis-100 hover:text-praxis-700'}`}
					title={p.display_name}
					onclick={() => nav(p.id)}
				>
					<ProcessIcon name={p.icon} size={20} />
					{#if p.id === processId}
						<span class="absolute -left-3 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r-full bg-praxis-700"></span>
					{/if}
				</button>
			{/each}
		</nav>

		<!-- Center: tool content -->
		<main class="flex flex-1 flex-col overflow-hidden">
			<div class="flex h-14 items-center justify-between border-b border-praxis-200 bg-white px-6">
				<div class="flex items-center gap-3">
					<div class="flex h-9 w-9 items-center justify-center rounded-lg bg-praxis-100 text-praxis-700">
						{#if current}
							<ProcessIcon name={current.icon} size={18} />
						{/if}
					</div>
					<div>
						<h1 class="text-[15px] font-semibold leading-tight text-ink-900">
							{current?.display_name ?? processId}
						</h1>
						{#if current}
							<div class="flex items-center gap-2 text-[11px] text-ink-500">
								<PhaseBadge phase={current.phase} />
								<span class="opacity-60">·</span>
								<span class="capitalize">{current.surface === 'tool' ? 'Werkzeug' : current.surface === 'conversation' ? 'Gespräch' : 'Übersicht'}</span>
							</div>
						{/if}
					</div>
				</div>
				<div class="flex items-center gap-2">
					{#if showUndo}
						<button
							class="flex items-center gap-1.5 rounded-md border border-praxis-300 bg-white px-3 py-1.5 text-sm text-ink-700 transition hover:bg-praxis-100 hover:text-praxis-800"
							onclick={() => onUndo?.()}
							title="Letzte Aktion rückgängig (Cmd+Z)"
						>
							<Undo2 size={14} /> Rückgängig
						</button>
					{/if}
				</div>
			</div>
			<div class="flex-1 overflow-y-auto p-6">
				{@render children()}
			</div>
		</main>

		<!-- Right: chat trigger + panel -->
		{#if showChatToggle}
			<div class="flex">
				<ChatPanel processId={processId} open={chatOpen} />
				<button
					class={`flex w-10 items-center justify-center border-l border-praxis-200 transition
						${chatOpen ? 'bg-praxis-700 text-white' : 'bg-white text-ink-500 hover:bg-praxis-100 hover:text-praxis-700'}`}
					onclick={() => (chatOpen = !chatOpen)}
					title={chatOpen ? 'Chat schließen' : 'Chat öffnen'}
				>
					<MessageSquare size={16} />
				</button>
			</div>
		{/if}
	</div>
</div>
