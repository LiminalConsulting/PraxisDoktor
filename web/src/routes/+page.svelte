<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { me } from '$lib/stores/auth';

	onMount(() => {
		goto($me ? '/dashboard' : '/login');
	});
</script>

<div class="flex h-screen items-center justify-center text-gray-400">…</div>
