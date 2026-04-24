<script lang="ts">
	import { api } from '$lib/api';
	import { Calendar, Loader2, CheckCircle2 } from 'lucide-svelte';

	let name = $state('');
	let contact = $state('');
	let reason = $state('');
	let desired = $state('');
	let isNew = $state(false);
	let busy = $state(false);
	let done = $state(false);
	let err = $state('');

	async function submit(e: Event) {
		e.preventDefault();
		busy = true;
		err = '';
		try {
			await api.bookingRequest({
				name,
				contact,
				reason,
				desired_slot: desired,
				is_new_patient: isNew
			});
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
		<Calendar size={28} class="text-praxis-700" />
		<h1 class="text-3xl md:text-4xl font-semibold text-praxis-900">Termin anfragen</h1>
	</div>
	<p class="text-ink-700 mb-8">
		Senden Sie uns Ihre Terminwunsch — wir melden uns am nächsten Werktag mit
		einer Bestätigung. In dringenden Fällen rufen Sie uns bitte direkt an.
	</p>

	{#if done}
		<div class="p-6 rounded-xl bg-praxis-50 border border-praxis-200 flex gap-3">
			<CheckCircle2 size={24} class="text-praxis-700 mt-0.5 shrink-0" />
			<div>
				<div class="font-semibold text-praxis-900 mb-1">Vielen Dank!</div>
				<div class="text-sm text-ink-700">
					Ihre Anfrage ist bei uns eingegangen. Wir melden uns am nächsten Werktag.
				</div>
			</div>
		</div>
	{:else}
		<form onsubmit={submit} class="space-y-5">
			<div>
				<label for="name" class="block text-sm font-medium text-ink-900 mb-1">Name *</label>
				<input
					id="name"
					type="text"
					required
					bind:value={name}
					class="w-full px-4 py-3 rounded-md border border-ink-300 focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/30"
				/>
			</div>

			<div>
				<label for="contact" class="block text-sm font-medium text-ink-900 mb-1">Telefon oder E-Mail *</label>
				<input
					id="contact"
					type="text"
					required
					bind:value={contact}
					placeholder="z. B. 0721 1234567"
					class="w-full px-4 py-3 rounded-md border border-ink-300 focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/30"
				/>
			</div>

			<div>
				<label for="reason" class="block text-sm font-medium text-ink-900 mb-1">Anlass (optional)</label>
				<textarea
					id="reason"
					rows="3"
					bind:value={reason}
					placeholder="Vorsorge, Beschwerden, …"
					class="w-full px-4 py-3 rounded-md border border-ink-300 focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/30"
				></textarea>
			</div>

			<div>
				<label for="desired" class="block text-sm font-medium text-ink-900 mb-1">Wunschtermin (optional)</label>
				<input
					id="desired"
					type="text"
					bind:value={desired}
					placeholder="z. B. nächste Woche vormittags"
					class="w-full px-4 py-3 rounded-md border border-ink-300 focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/30"
				/>
			</div>

			<label class="flex items-start gap-3 cursor-pointer">
				<input
					type="checkbox"
					bind:checked={isNew}
					class="mt-1 w-5 h-5 rounded border-ink-300 text-praxis-700 focus:ring-praxis-500"
				/>
				<span class="text-sm text-ink-700">
					Ich bin <strong>neu</strong> in der Praxis. (Wir senden Ihnen vorab den Anamnesebogen.)
				</span>
			</label>

			{#if err}
				<div class="p-4 rounded-md bg-red-50 border border-red-200 text-red-800 text-sm">{err}</div>
			{/if}

			<button
				type="submit"
				disabled={busy}
				class="w-full inline-flex items-center justify-center gap-2 px-5 py-3.5 rounded-md bg-praxis-700 text-white font-medium hover:bg-praxis-800 transition disabled:opacity-60"
			>
				{#if busy}<Loader2 size={18} class="animate-spin" />{/if}
				{busy ? 'Wird gesendet …' : 'Anfrage senden'}
			</button>
		</form>
	{/if}
</section>
