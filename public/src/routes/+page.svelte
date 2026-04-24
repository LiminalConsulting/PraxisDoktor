<script lang="ts">
	import { practice } from '$lib/practice';
	import { Calendar, ClipboardList, Stethoscope } from 'lucide-svelte';
</script>

<!-- Hero -->
<section class="relative bg-gradient-to-br from-praxis-50 via-white to-praxis-100">
	<div class="max-w-6xl mx-auto px-4 md:px-6 py-16 md:py-24 grid md:grid-cols-2 gap-10 items-center">
		<div>
			<div class="text-sm font-medium text-praxis-700 mb-3 tracking-wide uppercase">Urologie · Karlsruhe</div>
			<h1 class="text-3xl md:text-5xl font-semibold leading-tight text-praxis-900">
				Herzlich Willkommen
			</h1>
			<p class="mt-5 text-lg text-ink-700 max-w-prose">
				Moderne Urologie und Andrologie in Karlsruhe. Krebsvorsorge, Potenz- und
				Fruchtbarkeits-Checks in kompetenter, persönlicher Betreuung.
			</p>
			<div class="mt-7 flex flex-wrap gap-3">
				<a href="/booking" class="inline-flex items-center gap-2 px-5 py-3 rounded-md bg-praxis-700 text-white font-medium hover:bg-praxis-800 transition">
					<Calendar size={18} /> Termin vereinbaren
				</a>
				<a href="/leistungen" class="inline-flex items-center gap-2 px-5 py-3 rounded-md bg-white border border-ink-200 text-ink-900 font-medium hover:bg-praxis-50 transition">
					Unsere Leistungen
				</a>
			</div>
		</div>
		<div class="aspect-[4/3] rounded-2xl bg-praxis-100 grid place-items-center text-praxis-500">
			<!-- Placeholder for hero image. Real image lives in /static once Papa approves. -->
			<Stethoscope size={64} strokeWidth={1.2} />
		</div>
	</div>
</section>

<!-- Three pillars -->
<section class="max-w-6xl mx-auto px-4 md:px-6 py-16">
	<div class="grid gap-6 md:grid-cols-3">
		<a href="/leistungen" class="group p-6 rounded-xl bg-white border border-ink-200 hover:border-praxis-300 transition">
			<div class="w-10 h-10 rounded-lg bg-praxis-100 grid place-items-center mb-4 group-hover:bg-praxis-200 transition">
				<Stethoscope size={20} class="text-praxis-700" />
			</div>
			<div class="font-semibold text-praxis-900 mb-1">Leistungen</div>
			<div class="text-sm text-ink-700">Vorsorge, Diagnostik, ambulante Eingriffe — alles in einer Praxis.</div>
		</a>
		<a href="/team" class="group p-6 rounded-xl bg-white border border-ink-200 hover:border-praxis-300 transition">
			<div class="w-10 h-10 rounded-lg bg-praxis-100 grid place-items-center mb-4 group-hover:bg-praxis-200 transition">
				<ClipboardList size={20} class="text-praxis-700" />
			</div>
			<div class="font-semibold text-praxis-900 mb-1">Praxis & Team</div>
			<div class="text-sm text-ink-700">Zwei Fachärzt:innen, ein eingespieltes Team. Lernen Sie uns kennen.</div>
		</a>
		<a href="/booking" class="group p-6 rounded-xl bg-praxis-700 text-white hover:bg-praxis-800 transition">
			<div class="w-10 h-10 rounded-lg bg-praxis-600 grid place-items-center mb-4">
				<Calendar size={20} class="text-white" />
			</div>
			<div class="font-semibold mb-1">Termin online</div>
			<div class="text-sm text-praxis-100">Direkt anfragen — wir bestätigen am nächsten Werktag.</div>
		</a>
	</div>
</section>

<!-- Practice info strip -->
<section class="bg-praxis-50">
	<div class="max-w-6xl mx-auto px-4 md:px-6 py-12 grid gap-8 md:grid-cols-2 items-center">
		<div>
			<h2 class="text-2xl md:text-3xl font-semibold text-praxis-900 mb-3">
				Persönliche Medizin in Karlsruhe
			</h2>
			<p class="text-ink-700">
				{practice.shortName} steht für sorgfältige Diagnostik und Zeit für die
				Sprechstunde. Wir arbeiten mit moderner Technik und konzentrieren uns
				auf das, was zählt: dass Sie gehört, untersucht und gut betreut werden.
			</p>
		</div>
		<div class="bg-white rounded-xl border border-ink-200 p-6">
			<div class="text-sm font-medium text-praxis-700 mb-3">Sprechzeiten</div>
			<div class="space-y-1.5 text-ink-900">
				{#each practice.hours as h}
					<div class="flex justify-between gap-4">
						<span class="text-ink-700">{h.days}</span>
						<span class="font-medium">{h.time}</span>
					</div>
				{/each}
			</div>
			<div class="mt-4 pt-4 border-t border-ink-200 text-sm text-ink-700">
				Telefonisch erreichen Sie uns unter <strong class="text-ink-900">{practice.contact.phone}</strong>.
			</div>
		</div>
	</div>
</section>
