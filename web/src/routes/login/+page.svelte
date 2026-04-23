<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { loadMe } from '$lib/stores/auth';
	import { Stethoscope } from 'lucide-svelte';

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

<div class="flex min-h-screen items-center justify-center bg-praxis-50 px-4">
	<div class="w-full max-w-sm">
		<div class="mb-6 flex items-center justify-center gap-2">
			<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-praxis-700 text-white">
				<Stethoscope size={22} />
			</div>
			<div>
				<div class="text-lg font-semibold leading-tight text-praxis-700">PraxisDoktor</div>
				<div class="text-xs uppercase tracking-wider text-ink-500">Urologie Karlsruhe</div>
			</div>
		</div>

		<div class="rounded-xl border border-praxis-300 bg-white p-7 shadow-[0_4px_24px_rgba(60,90,70,0.08)]">
			<h1 class="mb-1 text-base font-semibold text-ink-900">Anmeldung</h1>
			<p class="mb-5 text-sm text-ink-500">Melden Sie sich mit Ihrem Praxis-Konto an.</p>

			<form onsubmit={submit} class="space-y-4">
				<div>
					<label class="mb-1 block text-xs font-semibold uppercase tracking-wider text-praxis-700" for="u">
						Benutzername
					</label>
					<input
						id="u"
						type="text"
						autocomplete="username"
						class="w-full rounded-lg border border-praxis-300 bg-white px-3 py-2 text-sm transition focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20"
						bind:value={username}
					/>
				</div>
				<div>
					<label class="mb-1 block text-xs font-semibold uppercase tracking-wider text-praxis-700" for="p">
						Passwort
					</label>
					<input
						id="p"
						type="password"
						autocomplete="current-password"
						class="w-full rounded-lg border border-praxis-300 bg-white px-3 py-2 text-sm transition focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20"
						bind:value={password}
					/>
				</div>

				{#if error}
					<div class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
				{/if}

				<button
					type="submit"
					disabled={loading}
					class="w-full rounded-lg bg-praxis-700 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-praxis-800 disabled:opacity-60"
				>
					{loading ? 'Anmelden…' : 'Anmelden'}
				</button>
			</form>
		</div>

		<details class="mt-4 rounded-lg border border-praxis-200 bg-white px-4 py-3 text-xs text-ink-500">
			<summary class="cursor-pointer font-medium text-praxis-700">Test-Zugänge (Entwicklung)</summary>
			<ul class="mt-2 grid grid-cols-1 gap-y-1 leading-6">
				<li><code class="rounded bg-praxis-100 px-1.5 py-0.5 text-[11px] text-praxis-800">admin</code> — Praxisinhaber</li>
				<li><code class="rounded bg-praxis-100 px-1.5 py-0.5 text-[11px] text-praxis-800">dr_inhaber</code> — Praxisinhaber + Arzt</li>
				<li><code class="rounded bg-praxis-100 px-1.5 py-0.5 text-[11px] text-praxis-800">dr_angestellt</code> — Arzt</li>
				<li><code class="rounded bg-praxis-100 px-1.5 py-0.5 text-[11px] text-praxis-800">mfa_anna</code> — Empfang</li>
				<li><code class="rounded bg-praxis-100 px-1.5 py-0.5 text-[11px] text-praxis-800">mfa_bea</code> — Behandlung</li>
				<li><code class="rounded bg-praxis-100 px-1.5 py-0.5 text-[11px] text-praxis-800">mfa_clara</code> — Abrechnung</li>
				<li><code class="rounded bg-praxis-100 px-1.5 py-0.5 text-[11px] text-praxis-800">manager_dora</code> — Praxismanager</li>
			</ul>
			<p class="mt-2 text-[11px] text-ink-400">Passwort für alle: <code>praxis123</code></p>
		</details>
	</div>
</div>
