<script lang="ts">
	import { goto } from '$app/navigation';
	import { logout, me } from '$lib/stores/auth';
	import { Home, LogOut, Settings, Stethoscope } from 'lucide-svelte';

	let showAdmin = $derived(($me?.roles ?? []).includes('praxisinhaber'));

	async function doLogout() {
		await logout();
		await goto('/login');
	}
</script>

<header class="flex h-14 items-center justify-between bg-praxis-700 px-5 text-white shadow-[0_2px_8px_rgba(0,0,0,0.10)]">
	<div class="flex items-center gap-4">
		<button
			class="flex items-center gap-2"
			onclick={() => goto('/dashboard')}
			title="Zum Dashboard"
		>
			<div class="flex h-8 w-8 items-center justify-center rounded-md bg-white/10">
				<Stethoscope size={18} />
			</div>
			<div class="text-left">
				<div class="text-sm font-semibold leading-tight">PraxisDoktor</div>
				<div class="text-[10px] uppercase tracking-wider opacity-70">Urologie Karlsruhe</div>
			</div>
		</button>
		<button
			class="ml-2 flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-white/80 transition hover:bg-white/10 hover:text-white"
			onclick={() => goto('/dashboard')}
			title="Dashboard"
		>
			<Home size={15} /> Dashboard
		</button>
	</div>

	<div class="flex items-center gap-1.5 text-sm">
		{#if showAdmin}
			<button
				class="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-white/80 transition hover:bg-white/10 hover:text-white"
				onclick={() => goto('/admin')}
			>
				<Settings size={15} /> Admin
			</button>
		{/if}
		<div class="ml-2 mr-1 flex items-center gap-2 rounded-md bg-white/10 px-3 py-1.5 text-xs">
			<div class="flex h-6 w-6 items-center justify-center rounded-full bg-white/20 text-[10px] font-semibold uppercase">
				{$me?.display_name?.[0] ?? '?'}
			</div>
			<span class="opacity-90">{$me?.display_name}</span>
		</div>
		<button
			class="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-white/80 transition hover:bg-white/10 hover:text-white"
			onclick={doLogout}
			title="Abmelden"
		>
			<LogOut size={15} />
		</button>
	</div>
</header>
