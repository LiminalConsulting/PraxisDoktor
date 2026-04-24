<script lang="ts">
	import { practice } from '$lib/practice';
</script>

<section class="max-w-5xl mx-auto px-4 md:px-6 py-12 md:py-16">
	<h1 class="text-3xl md:text-4xl font-semibold text-praxis-900 mb-3">Unser Team</h1>
	<p class="text-ink-700 max-w-prose mb-10">
		Seit 2024 führen wir die Praxis gemeinsam. Zwei Schwerpunkte, ein
		gemeinsames Verständnis von Medizin: gründlich, persönlich, ohne Hektik.
	</p>
	<div class="grid gap-6 md:grid-cols-2">
		{#each practice.doctors as d}
			<div class="p-6 rounded-xl bg-white border border-ink-200">
				<div class="aspect-[4/3] rounded-lg bg-praxis-100 mb-5"></div>
				<div class="font-semibold text-praxis-900 text-lg">{d.name}</div>
				<div class="text-praxis-700 text-sm font-medium mb-3">{d.role}</div>
				<div class="text-ink-700 text-sm mb-4">{d.bio}</div>
				<div class="flex flex-wrap gap-2">
					{#each d.focus as f}
						<span class="text-xs px-2.5 py-1 rounded-full bg-praxis-50 text-praxis-700">{f}</span>
					{/each}
				</div>
			</div>
		{/each}
	</div>
</section>
