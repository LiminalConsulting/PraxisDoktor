<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { loadMe } from '$lib/stores/auth';

	let username = $state('dr_inhaber');
	let password = $state('praxis123');
	let error = $state('');
	let loading = $state(false);

	async function submit(e: Event) {
		e.preventDefault();
		loading = true;
		error = '';
		try {
			await api.login(username.trim(), password);
			await loadMe();
			await goto('/dashboard');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Anmeldung fehlgeschlagen';
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center bg-stone-50 px-4">
	<div class="w-full max-w-sm rounded-2xl border border-stone-200 bg-white p-8 shadow-sm">
		<h1 class="mb-1 text-xl font-semibold text-stone-900">PraxisDoktor</h1>
		<p class="mb-6 text-sm text-stone-500">Bitte melden Sie sich an.</p>

		<form on:submit={submit} class="space-y-4">
			<div>
				<label class="block text-sm font-medium text-stone-700" for="u">Benutzername</label>
				<input
					id="u"
					type="text"
					autocomplete="username"
					class="mt-1 w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
					bind:value={username}
				/>
			</div>
			<div>
				<label class="block text-sm font-medium text-stone-700" for="p">Passwort</label>
				<input
					id="p"
					type="password"
					autocomplete="current-password"
					class="mt-1 w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
					bind:value={password}
				/>
			</div>

			{#if error}
				<p class="text-sm text-red-600">{error}</p>
			{/if}

			<button
				type="submit"
				disabled={loading}
				class="w-full rounded-lg bg-teal-700 py-2 text-sm font-medium text-white hover:bg-teal-800 disabled:opacity-50"
			>
				{loading ? 'Anmelden…' : 'Anmelden'}
			</button>
		</form>

		<details class="mt-6 text-xs text-stone-500">
			<summary class="cursor-pointer">Test-Zugänge (nur Entwicklung)</summary>
			<ul class="mt-2 list-disc pl-5 leading-6">
				<li><code>admin</code> / praxis123 — Praxisinhaber</li>
				<li><code>dr_inhaber</code> / praxis123 — Praxisinhaber + Arzt</li>
				<li><code>dr_angestellt</code> / praxis123 — Arzt</li>
				<li><code>mfa_anna</code> / praxis123 — Empfang</li>
				<li><code>mfa_bea</code> / praxis123 — Behandlung</li>
				<li><code>mfa_clara</code> / praxis123 — Abrechnung</li>
				<li><code>manager_dora</code> / praxis123 — Praxismanager</li>
			</ul>
		</details>
	</div>
</div>
