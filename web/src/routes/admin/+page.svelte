<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import { me } from '$lib/stores/auth';
	import { Trash2 } from 'lucide-svelte';

	let users = $state<{ id: string; display_name: string; roles: string[] }[]>([]);
	let roles = $state<{ id: string; display_name: string; description: string }[]>([]);
	let error = $state('');

	let nu_id = $state('');
	let nu_name = $state('');
	let nu_pw = $state('');
	let nu_roles = $state<Set<string>>(new Set());

	async function load() {
		try {
			[users, roles] = await Promise.all([api.listAdminUsers(), api.listAdminRoles()]);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Fehler beim Laden';
		}
	}
	onMount(load);

	async function setRoles(uid: string, has: string[]) {
		try {
			await api.setAdminUserRoles(uid, has);
			await load();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Fehler';
		}
	}
	function toggle(uid: string, role: string) {
		const u = users.find((x) => x.id === uid);
		if (!u) return;
		const has = new Set(u.roles);
		if (has.has(role)) has.delete(role);
		else has.add(role);
		setRoles(uid, [...has]);
	}

	async function createUser(e: Event) {
		e.preventDefault();
		try {
			await api.createAdminUser({
				id: nu_id.trim().toLowerCase(),
				display_name: nu_name.trim() || nu_id.trim(),
				password: nu_pw,
				roles: [...nu_roles]
			});
			nu_id = nu_name = nu_pw = '';
			nu_roles = new Set();
			await load();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Fehler';
		}
	}

	async function del(uid: string) {
		if (!confirm(`Benutzer "${uid}" wirklich löschen?`)) return;
		await api.deleteAdminUser(uid);
		await load();
	}

	let canSee = $derived(($me?.roles ?? []).includes('praxisinhaber'));
</script>

<div class="min-h-screen bg-stone-50">
	<AppHeader />

	<main class="mx-auto max-w-5xl p-6">
		<h1 class="mb-1 text-2xl font-semibold text-stone-900">Admin</h1>
		<p class="mb-6 text-sm text-stone-500">Benutzerkonten und Rollen.</p>

		{#if !canSee}
			<p class="text-sm text-red-600">Kein Zugriff.</p>
		{:else}
			{#if error}
				<p class="mb-4 rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>
			{/if}

			<section class="rounded-xl border border-stone-200 bg-white p-4">
				<h2 class="mb-3 text-sm font-medium text-stone-700">Benutzer</h2>
				<table class="w-full text-sm">
					<thead class="border-b border-stone-200 text-left text-xs text-stone-500">
						<tr>
							<th class="py-2">ID</th>
							<th class="py-2">Name</th>
							<th class="py-2">Rollen</th>
							<th></th>
						</tr>
					</thead>
					<tbody class="divide-y divide-stone-100">
						{#each users as u (u.id)}
							<tr>
								<td class="py-2 font-mono text-xs">{u.id}</td>
								<td class="py-2">{u.display_name}</td>
								<td class="py-2">
									<div class="flex flex-wrap gap-1">
										{#each roles as r (r.id)}
											<button
												class={`rounded border px-1.5 py-0.5 text-[10px] ${u.roles.includes(r.id) ? 'border-teal-300 bg-teal-50 text-teal-800' : 'border-stone-200 bg-white text-stone-500'}`}
												on:click={() => toggle(u.id, r.id)}
												title={r.description}
											>
												{r.display_name}
											</button>
										{/each}
									</div>
								</td>
								<td class="py-2 text-right">
									<button class="text-stone-400 hover:text-red-600" on:click={() => del(u.id)} title="Löschen">
										<Trash2 size={14} />
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</section>

			<section class="mt-6 rounded-xl border border-stone-200 bg-white p-4">
				<h2 class="mb-3 text-sm font-medium text-stone-700">Neuen Benutzer anlegen</h2>
				<form on:submit={createUser} class="grid grid-cols-1 gap-3 sm:grid-cols-3">
					<input
						type="text"
						bind:value={nu_id}
						required
						placeholder="benutzername"
						class="rounded-lg border border-stone-300 px-3 py-2 text-sm"
					/>
					<input
						type="text"
						bind:value={nu_name}
						placeholder="Anzeigename"
						class="rounded-lg border border-stone-300 px-3 py-2 text-sm"
					/>
					<input
						type="password"
						bind:value={nu_pw}
						required
						placeholder="Passwort"
						class="rounded-lg border border-stone-300 px-3 py-2 text-sm"
					/>

					<div class="sm:col-span-3">
						<div class="mb-1 text-xs text-stone-500">Rollen</div>
						<div class="flex flex-wrap gap-1">
							{#each roles as r (r.id)}
								<label class="flex items-center gap-1.5 rounded border border-stone-200 px-2 py-1 text-xs">
									<input
										type="checkbox"
										checked={nu_roles.has(r.id)}
										on:change={(e) => {
											const next = new Set(nu_roles);
											if ((e.target as HTMLInputElement).checked) next.add(r.id);
											else next.delete(r.id);
											nu_roles = next;
										}}
									/>
									{r.display_name}
								</label>
							{/each}
						</div>
					</div>

					<div class="sm:col-span-3">
						<button class="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800">
							Anlegen
						</button>
					</div>
				</form>
			</section>
		{/if}
	</main>
</div>
