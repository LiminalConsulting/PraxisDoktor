<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { logout, me } from '$lib/stores/auth';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import { KeyRound, ShieldCheck } from 'lucide-svelte';

	let oldP = $state('');
	let newP = $state('');
	let confirmP = $state('');
	let error = $state('');
	let success = $state(false);
	let loading = $state(false);

	async function submit(e: Event) {
		e.preventDefault();
		error = '';
		success = false;
		if (newP !== confirmP) {
			error = 'Die neuen Passwörter stimmen nicht überein.';
			return;
		}
		if (newP.length < 6) {
			error = 'Neues Passwort muss mindestens 6 Zeichen haben.';
			return;
		}
		loading = true;
		try {
			await api.changePassword(oldP, newP);
			success = true;
			setTimeout(async () => {
				await logout();
				await goto('/login');
			}, 1400);
		} catch (e) {
			error = e instanceof Error ? e.message.replace(/^\d+\s\w+:\s*/, '') : 'Fehler';
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex min-h-screen flex-col bg-praxis-50">
	<AppHeader />

	<main class="mx-auto w-full max-w-xl flex-1 px-6 py-10">
		<h1 class="mb-1 text-[22px] font-semibold tracking-tight text-praxis-800">Mein Konto</h1>
		<p class="mb-6 text-sm text-ink-500">Angemeldet als <span class="font-medium text-ink-700">{$me?.display_name}</span> · <code class="rounded bg-praxis-100 px-1.5 py-0.5 text-[11px] text-praxis-800">{$me?.id}</code></p>

		<section class="rounded-xl border border-praxis-200 bg-white shadow-sm">
			<div class="flex items-center gap-2 border-b border-praxis-200 bg-praxis-50 px-5 py-3">
				<KeyRound size={14} class="text-praxis-700" />
				<h2 class="text-xs font-semibold uppercase tracking-wider text-praxis-700">Passwort ändern</h2>
			</div>
			<form onsubmit={submit} class="space-y-4 p-5">
				<div>
					<label class="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-praxis-700" for="oldp">Aktuelles Passwort</label>
					<input id="oldp" type="password" bind:value={oldP} required autocomplete="current-password"
						class="w-full rounded-lg border border-praxis-300 px-3 py-2 text-sm focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20" />
				</div>
				<div>
					<label class="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-praxis-700" for="newp">Neues Passwort</label>
					<input id="newp" type="password" bind:value={newP} required minlength="6" autocomplete="new-password"
						class="w-full rounded-lg border border-praxis-300 px-3 py-2 text-sm focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20" />
				</div>
				<div>
					<label class="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-praxis-700" for="confp">Neues Passwort bestätigen</label>
					<input id="confp" type="password" bind:value={confirmP} required minlength="6" autocomplete="new-password"
						class="w-full rounded-lg border border-praxis-300 px-3 py-2 text-sm focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20" />
				</div>

				{#if error}
					<div class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">{error}</div>
				{/if}
				{#if success}
					<div class="flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700 ring-1 ring-emerald-200">
						<ShieldCheck size={14} /> Passwort geändert. Sie werden abgemeldet…
					</div>
				{/if}

				<div class="flex justify-end">
					<button class="rounded-lg bg-praxis-700 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-praxis-800 disabled:opacity-60" disabled={loading}>
						{loading ? 'Speichern…' : 'Passwort ändern'}
					</button>
				</div>
			</form>
		</section>

		<p class="mt-4 text-[11px] text-ink-500">
			Hinweis: Nach erfolgreicher Änderung werden alle Ihre aktiven Sitzungen (auch auf anderen Geräten) abgemeldet.
		</p>
	</main>
</div>
