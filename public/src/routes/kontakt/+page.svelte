<script lang="ts">
	import { practice } from '$lib/practice';
	import { Phone, Mail, MapPin, Clock } from 'lucide-svelte';
</script>

<section class="max-w-4xl mx-auto px-4 md:px-6 py-12 md:py-16">
	<h1 class="text-3xl md:text-4xl font-semibold text-praxis-900 mb-3">Kontakt</h1>
	<p class="text-ink-700 mb-10">So erreichen Sie uns.</p>

	<div class="grid gap-6 md:grid-cols-2">
		<div class="p-6 rounded-xl bg-white border border-ink-200">
			<div class="flex items-start gap-3 mb-4">
				<MapPin size={20} class="text-fresh-600 mt-0.5" />
				<div>
					<div class="font-semibold text-praxis-900">Adresse</div>
					<div class="text-ink-700 text-sm mt-1">
						{practice.address.street}<br />
						{practice.address.zip} {practice.address.city}
					</div>
				</div>
			</div>
			<div class="flex items-start gap-3 mb-4">
				<Phone size={20} class="text-fresh-600 mt-0.5" />
				<div>
					<div class="font-semibold text-praxis-900">Telefon</div>
					<a href="tel:{practice.contact.phone}" class="text-ink-700 text-sm mt-1 block hover:text-praxis-700">
						{practice.contact.phone}
					</a>
				</div>
			</div>
			<div class="flex items-start gap-3">
				<Mail size={20} class="text-fresh-600 mt-0.5" />
				<div>
					<div class="font-semibold text-praxis-900">E-Mail</div>
					<a href="mailto:{practice.contact.email}" class="text-ink-700 text-sm mt-1 block hover:text-praxis-700">
						{practice.contact.email}
					</a>
				</div>
			</div>
		</div>

		<div class="p-6 rounded-xl bg-praxis-50">
			<div class="flex items-center gap-3 mb-4">
				<Clock size={20} class="text-praxis-700" />
				<div class="font-semibold text-praxis-900">Sprechzeiten</div>
			</div>
			<div class="space-y-2">
				{#each practice.hours as h}
					<div class="flex justify-between text-sm">
						<span class="text-ink-700">{h.days}</span>
						<span class="font-medium text-ink-900">{h.time}</span>
					</div>
				{/each}
			</div>
			<a href="/booking" class="mt-6 inline-block w-full text-center px-4 py-3 rounded-md bg-fresh-400 text-praxis-900 font-medium hover:bg-fresh-500 transition">
				Termin online anfragen
			</a>
		</div>
	</div>
</section>
