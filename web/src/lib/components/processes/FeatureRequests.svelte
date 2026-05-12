<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { ChevronUp, Plus, X, Loader2 } from 'lucide-svelte';

	type FR = {
		id: string;
		title: string;
		body: string;
		category: string;
		status: string;
		submitted_by: string;
		submitted_by_role: string;
		created_at: string;
		vote_count: number;
		user_voted: boolean;
	};

	const STATUS_LABEL: Record<string, string> = {
		open: 'Offen',
		planned: 'Geplant',
		in_progress: 'In Bearbeitung',
		done: 'Erledigt',
		declined: 'Abgelehnt',
	};
	const STATUS_CLASSES: Record<string, string> = {
		open: 'bg-praxis-100 text-praxis-700 ring-praxis-200',
		planned: 'bg-blue-50 text-blue-700 ring-blue-200',
		in_progress: 'bg-amber-50 text-amber-800 ring-amber-200',
		done: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
		declined: 'bg-ink-100 text-ink-500 ring-ink-200',
	};
	const STATUS_OPTIONS = ['open', 'planned', 'in_progress', 'done', 'declined'];

	const CATEGORIES = [
		'Anamnese / Patientenaufnahme',
		'Rechnungsprüfung / Abrechnung',
		'Termine / Disposition',
		'Briefe / KIM',
		'Material / Bestellung',
		'Personal / Schichtplan',
		'Patientenakte / Dokumentation',
		'Sonstiges',
	];

	let requests = $state<FR[]>([]);
	let loading = $state(false);
	let showNew = $state(false);
	let newTitle = $state('');
	let newBody = $state('');
	let newCategory = $state('');
	let filterStatus = $state<string>('alle');

	async function load() {
		loading = true;
		try {
			requests = await api.featureRequests.list();
		} finally {
			loading = false;
		}
	}

	async function submit() {
		if (!newTitle.trim()) return;
		await api.featureRequests.submit(newTitle.trim(), newBody.trim(), newCategory);
		newTitle = '';
		newBody = '';
		newCategory = '';
		showNew = false;
		await load();
	}

	async function toggleVote(fr: FR) {
		// optimistic
		fr.user_voted = !fr.user_voted;
		fr.vote_count = fr.user_voted ? fr.vote_count + 1 : fr.vote_count - 1;
		requests = [...requests];
		try {
			await api.featureRequests.toggleVote(fr.id);
		} catch {
			// rollback
			fr.user_voted = !fr.user_voted;
			fr.vote_count = fr.user_voted ? fr.vote_count + 1 : fr.vote_count - 1;
			requests = [...requests];
		}
	}

	async function setStatus(fr: FR, status: string) {
		const old = fr.status;
		fr.status = status;
		requests = [...requests];
		try {
			await api.featureRequests.changeStatus(fr.id, status);
		} catch {
			fr.status = old;
			requests = [...requests];
		}
	}

	const filteredRequests = $derived(
		filterStatus === 'alle' ? requests : requests.filter((r) => r.status === filterStatus)
	);

	onMount(load);
</script>

<div class="space-y-4">
	<!-- Header + new-request button -->
	<section class="rounded-xl border border-praxis-200 bg-white p-5 shadow-sm">
		<div class="flex flex-wrap items-start justify-between gap-3">
			<div>
				<h2 class="text-sm font-semibold uppercase tracking-wider text-praxis-700">Verbesserungs-Wünsche</h2>
				<p class="mt-1 max-w-2xl text-sm text-ink-600">
					Sammeln Sie hier Ihre Wünsche, Schmerzpunkte und Ideen — was klemmt im Alltag, was würde
					Ihnen die Arbeit erleichtern? Andere im Team können abstimmen, damit wir wissen, was am
					meisten gebraucht wird.
				</p>
			</div>
			<button
				class="flex items-center gap-1.5 rounded-lg bg-praxis-700 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-praxis-800"
				onclick={() => (showNew = !showNew)}
			>
				{#if showNew}
					<X size={16} /> Abbrechen
				{:else}
					<Plus size={16} /> Neuer Wunsch
				{/if}
			</button>
		</div>

		<!-- Submission form -->
		{#if showNew}
			<form onsubmit={(e) => { e.preventDefault(); submit(); }} class="mt-5 space-y-3 rounded-lg border border-praxis-200 bg-praxis-50/40 p-4">
				<div>
					<label class="mb-1 block text-xs font-semibold uppercase tracking-wider text-praxis-700" for="fr-title">
						Worum geht's? (kurz)
					</label>
					<input
						id="fr-title"
						type="text"
						bind:value={newTitle}
						placeholder="z.B. Automatische Vorschläge für ePA-Ziffern"
						class="w-full rounded-lg border border-praxis-300 px-3 py-2 text-sm focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20"
					/>
				</div>
				<div>
					<label class="mb-1 block text-xs font-semibold uppercase tracking-wider text-praxis-700" for="fr-body">
						Beschreibung (optional, aber hilfreich)
					</label>
					<textarea
						id="fr-body"
						bind:value={newBody}
						rows="4"
						placeholder="Erklären Sie kurz, was momentan klemmt und was idealerweise passieren sollte."
						class="w-full rounded-lg border border-praxis-300 px-3 py-2 text-sm leading-relaxed focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20"
					></textarea>
				</div>
				<div>
					<label class="mb-1 block text-xs font-semibold uppercase tracking-wider text-praxis-700" for="fr-cat">
						Bereich (optional)
					</label>
					<select
						id="fr-cat"
						bind:value={newCategory}
						class="w-full rounded-lg border border-praxis-300 px-3 py-2 text-sm focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20"
					>
						<option value="">— bitte wählen —</option>
						{#each CATEGORIES as c (c)}
							<option value={c}>{c}</option>
						{/each}
					</select>
				</div>
				<div class="flex justify-end">
					<button
						class="rounded-lg bg-praxis-700 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-praxis-800 disabled:opacity-50"
						disabled={!newTitle.trim()}
					>
						Wunsch absenden →
					</button>
				</div>
			</form>
		{/if}
	</section>

	<!-- Filter bar -->
	<div class="flex flex-wrap items-center gap-2 text-xs">
		<span class="font-medium text-praxis-700">Filter:</span>
		<button
			class={`rounded-full px-3 py-1 ring-1 transition ${
				filterStatus === 'alle' ? 'bg-praxis-700 text-white ring-praxis-700' : 'bg-white text-ink-700 ring-praxis-300 hover:bg-praxis-50'
			}`}
			onclick={() => (filterStatus = 'alle')}
		>
			Alle ({requests.length})
		</button>
		{#each STATUS_OPTIONS as s (s)}
			<button
				class={`rounded-full px-3 py-1 ring-1 transition ${
					filterStatus === s ? 'bg-praxis-700 text-white ring-praxis-700' : 'bg-white text-ink-700 ring-praxis-300 hover:bg-praxis-50'
				}`}
				onclick={() => (filterStatus = s)}
			>
				{STATUS_LABEL[s]} ({requests.filter((r) => r.status === s).length})
			</button>
		{/each}
	</div>

	<!-- List -->
	{#if loading}
		<div class="flex items-center justify-center gap-2 py-12 text-sm text-ink-500">
			<Loader2 size={16} class="animate-spin" /> wird geladen…
		</div>
	{:else if filteredRequests.length === 0}
		<div class="rounded-xl border border-dashed border-praxis-300 bg-white p-10 text-center">
			<p class="text-sm text-ink-500">
				Noch keine Wünsche eingetragen. Starten Sie mit einem ersten Wunsch oben.
			</p>
		</div>
	{:else}
		<ul class="space-y-2">
			{#each filteredRequests as fr (fr.id)}
				<li class="flex gap-3 rounded-xl border border-praxis-200 bg-white p-4 shadow-sm transition hover:border-praxis-300">
					<!-- Vote button -->
					<button
						class={`flex h-16 w-14 flex-shrink-0 flex-col items-center justify-center rounded-lg border-2 transition ${
							fr.user_voted
								? 'border-emerald-500 bg-emerald-50 text-emerald-700'
								: 'border-praxis-300 bg-white text-ink-600 hover:border-praxis-500 hover:bg-praxis-50'
						}`}
						onclick={() => toggleVote(fr)}
						title={fr.user_voted ? 'Stimme zurücknehmen' : 'Abstimmen'}
					>
						<ChevronUp size={20} />
						<span class="text-sm font-bold">{fr.vote_count}</span>
					</button>

					<!-- Content -->
					<div class="min-w-0 flex-1">
						<div class="flex flex-wrap items-start justify-between gap-2">
							<h3 class="text-sm font-semibold text-ink-900">{fr.title}</h3>
							<span class={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ring-1 ${STATUS_CLASSES[fr.status] ?? STATUS_CLASSES.open}`}>
								{STATUS_LABEL[fr.status] ?? fr.status}
							</span>
						</div>
						{#if fr.body}
							<p class="mt-1.5 whitespace-pre-wrap text-sm leading-relaxed text-ink-700">{fr.body}</p>
						{/if}
						<div class="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-ink-500">
							<span>von <strong class="text-ink-700">{fr.submitted_by}</strong></span>
							{#if fr.category}
								<span class="inline-flex items-center rounded-full bg-praxis-100 px-2 py-0.5 font-medium text-praxis-700">
									{fr.category}
								</span>
							{/if}
							<span>· {new Date(fr.created_at).toLocaleDateString('de-DE')}</span>
						</div>

						<!-- Status-Änderung für Praxisinhaber/-manager -->
						<details class="mt-2">
							<summary class="cursor-pointer text-[11px] text-ink-400 hover:text-praxis-700">Status ändern</summary>
							<div class="mt-2 flex flex-wrap gap-1">
								{#each STATUS_OPTIONS as s (s)}
									<button
										class={`rounded px-2 py-0.5 text-[11px] ring-1 ring-praxis-200 transition hover:bg-praxis-100 ${
											fr.status === s ? 'bg-praxis-100 font-semibold' : 'bg-white'
										}`}
										onclick={() => setStatus(fr, s)}
									>
										{STATUS_LABEL[s]}
									</button>
								{/each}
							</div>
						</details>
					</div>
				</li>
			{/each}
		</ul>
	{/if}
</div>
