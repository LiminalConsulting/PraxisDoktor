<script lang="ts">
	import '../app.css';
	import { practice } from '$lib/practice';
	import { Menu, X } from 'lucide-svelte';

	let { children } = $props();
	let mobileOpen = $state(false);

	const nav = [
		{ href: '/', label: 'Start' },
		{ href: '/leistungen', label: 'Leistungen' },
		{ href: '/team', label: 'Team' },
		{ href: '/kontakt', label: 'Kontakt' },
		{ href: '/booking', label: 'Termin', highlight: true }
	];
</script>

<header class="sticky top-0 z-40 bg-white/90 backdrop-blur border-b border-ink-200">
	<div class="max-w-6xl mx-auto px-4 md:px-6 py-3 flex items-center justify-between">
		<a href="/" class="flex items-center gap-2 group">
			<span class="w-8 h-8 rounded-md bg-praxis-700 grid place-items-center text-white font-semibold">U</span>
			<span class="font-medium text-ink-900 hidden sm:block">{practice.shortName}</span>
		</a>

		<nav class="hidden md:flex items-center gap-1">
			{#each nav as item}
				<a
					href={item.href}
					class="px-3 py-2 rounded-md text-sm font-medium transition-colors
						{item.highlight
							? 'bg-fresh-400 text-praxis-900 hover:bg-fresh-500'
							: 'text-ink-700 hover:bg-praxis-50 hover:text-praxis-700'}"
				>
					{item.label}
				</a>
			{/each}
		</nav>

		<button
			class="md:hidden p-2 -mr-2 text-ink-700"
			aria-label="Menü öffnen"
			onclick={() => (mobileOpen = !mobileOpen)}
		>
			{#if mobileOpen}<X size={24} />{:else}<Menu size={24} />{/if}
		</button>
	</div>

	{#if mobileOpen}
		<nav class="md:hidden border-t border-ink-200 px-4 py-3 flex flex-col gap-1">
			{#each nav as item}
				<a
					href={item.href}
					onclick={() => (mobileOpen = false)}
					class="px-3 py-3 rounded-md text-base font-medium
						{item.highlight
							? 'bg-fresh-400 text-praxis-900'
							: 'text-ink-700 hover:bg-praxis-50'}"
				>
					{item.label}
				</a>
			{/each}
		</nav>
	{/if}
</header>

<main>
	{@render children()}
</main>

<footer class="bg-praxis-900 text-praxis-100 mt-16">
	<div class="max-w-6xl mx-auto px-4 md:px-6 py-10 grid gap-8 md:grid-cols-3 text-sm">
		<div>
			<div class="font-semibold text-white mb-2">{practice.shortName}</div>
			<div>{practice.address.street}</div>
			<div>{practice.address.zip} {practice.address.city}</div>
		</div>
		<div>
			<div class="font-semibold text-white mb-2">Kontakt</div>
			<div>Tel: {practice.contact.phone}</div>
			<div>Fax: {practice.contact.fax}</div>
			<div>E-Mail: <a class="underline" href="mailto:{practice.contact.email}">{practice.contact.email}</a></div>
		</div>
		<div>
			<div class="font-semibold text-white mb-2">Sprechzeiten</div>
			{#each practice.hours as h}
				<div>{h.days}: {h.time}</div>
			{/each}
		</div>
	</div>
	<div class="border-t border-praxis-700">
		<div class="max-w-6xl mx-auto px-4 md:px-6 py-4 text-xs text-praxis-300 flex flex-wrap gap-4 justify-between">
			<span>© {new Date().getFullYear()} {practice.shortName}</span>
			<span class="flex gap-4">
				<a href="/impressum" class="hover:text-white">Impressum</a>
				<a href="/datenschutz" class="hover:text-white">Datenschutz</a>
			</span>
		</div>
	</div>
</footer>
