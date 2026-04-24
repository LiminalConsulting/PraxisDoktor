<script lang="ts">
	import { practice } from '$lib/practice';
</script>

<section class="max-w-5xl mx-auto px-4 md:px-6 py-12 md:py-16">
	<h1 class="text-3xl md:text-4xl font-semibold text-praxis-900 mb-3">Leistungen</h1>
	<p class="text-ink-700 max-w-prose mb-10">
		Das gesamte Spektrum der ambulanten Urologie und Andrologie — Diagnostik,
		Vorsorge, konservative Therapien und kleinere Eingriffe.
	</p>
	<div class="grid gap-5 md:grid-cols-2">
		{#each practice.services as s}
			<div class="p-6 rounded-xl bg-white border border-ink-200">
				<div class="font-semibold text-praxis-900 mb-2">{s.title}</div>
				<div class="text-ink-700 text-sm">{s.text}</div>
			</div>
		{/each}
	</div>
</section>
