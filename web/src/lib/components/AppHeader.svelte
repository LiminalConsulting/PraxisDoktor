<script lang="ts">
	import { goto } from '$app/navigation';
	import { logout, me } from '$lib/stores/auth';
	import { Home, LogOut, Settings } from 'lucide-svelte';

	let showAdmin = $derived(($me?.roles ?? []).includes('praxisinhaber'));

	async function doLogout() {
		await logout();
		await goto('/login');
	}
</script>

<header class="flex h-12 items-center justify-between border-b border-stone-200 bg-white px-4">
	<div class="flex items-center gap-3">
		<button
			class="flex items-center gap-1.5 rounded px-2 py-1 text-sm text-stone-600 hover:bg-stone-100"
			on:click={() => goto('/dashboard')}
			title="Dashboard"
		>
			<Home size={16} /> Dashboard
		</button>
		<span class="text-sm font-medium text-stone-800">PraxisDoktor</span>
	</div>
	<div class="flex items-center gap-3 text-sm">
		{#if showAdmin}
			<button
				class="flex items-center gap-1.5 rounded px-2 py-1 text-stone-600 hover:bg-stone-100"
				on:click={() => goto('/admin')}
			>
				<Settings size={16} /> Admin
			</button>
		{/if}
		<span class="text-stone-500">{$me?.display_name}</span>
		<button
			class="flex items-center gap-1.5 rounded px-2 py-1 text-stone-600 hover:bg-stone-100"
			on:click={doLogout}
		>
			<LogOut size={16} /> Abmelden
		</button>
	</div>
</header>
