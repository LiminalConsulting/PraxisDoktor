<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { loadMe } from '$lib/stores/auth';

	let { children } = $props();
	let ready = $state(false);

	onMount(async () => {
		const u = await loadMe();
		const path = $page.url.pathname;
		if (!u && path !== '/login') {
			await goto('/login');
		} else if (u && path === '/login') {
			await goto('/dashboard');
		}
		ready = true;
	});
</script>

{#if ready}
	{@render children()}
{:else}
	<div class="flex h-screen items-center justify-center text-stone-400">…</div>
{/if}
