<script lang="ts">
	import { page } from '$app/stores';
	import ToolLayout from '$lib/components/ToolLayout.svelte';
	import PatientIntake from '$lib/components/processes/PatientIntake.svelte';
	import TeamChatView from '$lib/components/processes/TeamChatView.svelte';
	import PlaceholderTool from '$lib/components/processes/PlaceholderTool.svelte';

	let pid = $derived($page.params.process_id ?? '');
	let undoFn = $state<() => void>(() => {});
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
{:else}
	<ToolLayout processId={pid}>
		{#snippet children()}
			<PlaceholderTool {pid} />
		{/snippet}
	</ToolLayout>
{/if}
