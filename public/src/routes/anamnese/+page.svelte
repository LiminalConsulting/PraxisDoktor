<script lang="ts">
	import { api } from '$lib/api';
	import { ClipboardList, Loader2, CheckCircle2 } from 'lucide-svelte';

	let name = $state('');
	let dob = $state('');
	let answers = $state<Record<string, string>>({});
	let busy = $state(false);
	let done = $state(false);
	let err = $state('');

	const questions = [
		{ id: 'reason', label: 'Was führt Sie zu uns?', type: 'textarea' },
		{ id: 'duration', label: 'Seit wann bestehen die Beschwerden?', type: 'text' },
		{ id: 'medications', label: 'Welche Medikamente nehmen Sie regelmäßig?', type: 'textarea' },
		{ id: 'allergies', label: 'Bekannte Allergien?', type: 'text' },
		{ id: 'previous_ops', label: 'Voroperationen?', type: 'textarea' },
		{ id: 'family_history', label: 'Krankheiten in der Familie (Krebs, Nieren, Prostata)?', type: 'textarea' },
		{ id: 'lifestyle', label: 'Rauchen, Alkohol, Sport — kurz beschreiben.', type: 'text' }
	];

	async function submit(e: Event) {
		e.preventDefault();
		busy = true;
		err = '';
		try {
			await api.anamneseSubmit({ name, dob, answers });
			done = true;
		} catch (e2) {
			err = (e2 instanceof Error ? e2.message : String(e2));
		} finally {
			busy = false;
		}
	}
</script>

<section class="max-w-2xl mx-auto px-4 md:px-6 py-12 md:py-16">
	<div class="flex items-center gap-3 mb-3">
		<ClipboardList size={28} class="text-fresh-600" />
		<h1 class="text-3xl md:text-4xl font-semibold text-praxis-900">Anamnesebogen</h1>
	</div>
	<p class="text-ink-700 mb-8">
		Bitte füllen Sie diesen Bogen vor Ihrem Termin aus. Ihre Angaben gehen
		direkt in unsere Praxis-Software — niemand sonst sieht sie.
	</p>

	{#if done}
		<div class="p-6 rounded-xl bg-fresh-300/30 border border-fresh-400 flex gap-3">
			<CheckCircle2 size={24} class="text-fresh-600 mt-0.5 shrink-0" />
			<div>
				<div class="font-semibold text-praxis-900 mb-1">Vielen Dank!</div>
				<div class="text-sm text-ink-700">
					Ihr Anamnesebogen ist bei uns eingegangen. Wir bereiten Ihren Termin
					entsprechend vor.
				</div>
			</div>
		</div>
	{:else}
		<form onsubmit={submit} class="space-y-5">
			<div class="grid gap-5 md:grid-cols-2">
				<div>
					<label for="name" class="block text-sm font-medium text-ink-900 mb-1">Name *</label>
					<input
						id="name" type="text" required bind:value={name}
						class="w-full px-4 py-3 rounded-md border border-ink-300 focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/30"
					/>
				</div>
				<div>
					<label for="dob" class="block text-sm font-medium text-ink-900 mb-1">Geburtsdatum</label>
					<input
						id="dob" type="date" bind:value={dob}
						class="w-full px-4 py-3 rounded-md border border-ink-300 focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/30"
					/>
				</div>
			</div>

			{#each questions as q}
				<div>
					<label for={q.id} class="block text-sm font-medium text-ink-900 mb-1">{q.label}</label>
					{#if q.type === 'textarea'}
						<textarea
							id={q.id} rows="3" bind:value={answers[q.id]}
							class="w-full px-4 py-3 rounded-md border border-ink-300 focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/30"
						></textarea>
					{:else}
						<input
							id={q.id} type="text" bind:value={answers[q.id]}
							class="w-full px-4 py-3 rounded-md border border-ink-300 focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/30"
						/>
					{/if}
				</div>
			{/each}

			{#if err}
				<div class="p-4 rounded-md bg-red-50 border border-red-200 text-red-800 text-sm">{err}</div>
			{/if}

			<button
				type="submit"
				disabled={busy}
				class="w-full inline-flex items-center justify-center gap-2 px-5 py-3.5 rounded-md bg-fresh-400 text-praxis-900 font-medium hover:bg-fresh-500 transition disabled:opacity-60"
			>
				{#if busy}<Loader2 size={18} class="animate-spin" />{/if}
				{busy ? 'Wird gesendet …' : 'Anamnesebogen absenden'}
			</button>
		</form>
	{/if}
</section>
