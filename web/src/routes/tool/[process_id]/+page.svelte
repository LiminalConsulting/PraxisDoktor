<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api';
	import ToolLayout from '$lib/components/ToolLayout.svelte';
	import PatientIntake from '$lib/components/processes/PatientIntake.svelte';
	import TeamChatView from '$lib/components/processes/TeamChatView.svelte';
	import PlaceholderTool from '$lib/components/processes/PlaceholderTool.svelte';
	import DashboardOnlyView from '$lib/components/processes/DashboardOnlyView.svelte';

	let pid = $derived($page.params.process_id ?? '');
	let undoFn = $state<() => void>(() => {});
	let surface = $state<string | null>(null);
	let phase = $state<string | null>(null);

	$effect(() => {
		const id = pid;
		if (!id) return;
		surface = null;
		phase = null;
		(async () => {
			try {
				const p = await api.processMeta(id);
				surface = p.surface;
				phase = p.phase;
				api.markSeen(id).catch(() => {});
			} catch {}
		})();
	});
</script>

{#if pid === 'patient_intake'}
	<ToolLayout
		processId={pid}
		showChatToggle
		showUndo
		onUndo={() => undoFn()}
	>
		{#snippet children()}
			<PatientIntake registerUndo={(fn) => (undoFn = fn)} />
		{/snippet}
	</ToolLayout>
{:else if pid === 'team_chat'}
	<ToolLayout processId={pid} showChatToggle={false}>
		{#snippet children()}
			<TeamChatView />
		{/snippet}
	</ToolLayout>
{:else if surface === 'dashboard_only'}
	<ToolLayout processId={pid} showChatToggle>
		{#snippet children()}
			<DashboardOnlyView {pid} />
		{/snippet}
	</ToolLayout>
{:else}
	<ToolLayout processId={pid} showChatToggle>
		{#snippet children()}
			<PlaceholderTool {pid} />
		{/snippet}
	</ToolLayout>
{/if}
