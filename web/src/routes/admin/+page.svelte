<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import { me } from '$lib/stores/auth';
	import { Trash2, UserPlus, ShieldOff } from 'lucide-svelte';

	let users = $state<{ id: string; display_name: string; roles: string[] }[]>([]);
	let roles = $state<{ id: string; display_name: string; description: string }[]>([]);
	let error = $state('');

	let nu_id = $state('');
	let nu_name = $state('');
	let nu_pw = $state('');
	let nu_roles = $state<Set<string>>(new Set());

	async function load() {
		try { [users, roles] = await Promise.all([api.listAdminUsers(), api.listAdminRoles()]); }
		catch (e) { error = e instanceof Error ? e.message : 'Fehler beim Laden'; }
	}
	onMount(load);

	async function setRoles(uid: string, has: string[]) {
		try { await api.setAdminUserRoles(uid, has); await load(); }
		catch (e) { error = e instanceof Error ? e.message : 'Fehler'; }
	}
	function toggle(uid: string, role: string) {
		const u = users.find((x) => x.id === uid);
		if (!u) return;
		const has = new Set(u.roles);
		has.has(role) ? has.delete(role) : has.add(role);
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
		} catch (e) { error = e instanceof Error ? e.message : 'Fehler'; }
	}

	async function del(uid: string) {
		if (!confirm(`Benutzer "${uid}" wirklich löschen?`)) return;
		await api.deleteAdminUser(uid);
		await load();
	}

	let canSee = $derived(($me?.roles ?? []).includes('praxisinhaber'));
</script>

<div class="flex min-h-screen flex-col bg-praxis-50">
	<AppHeader />

	<main class="mx-auto w-full max-w-5xl flex-1 px-6 py-8">
		<div class="mb-6">
			<h1 class="text-[22px] font-semibold tracking-tight text-praxis-800">Administration</h1>
			<p class="mt-1 text-sm text-ink-500">Benutzerkonten verwalten und Rollen zuweisen.</p>
		</div>

		{#if !canSee}
			<div class="rounded-xl border border-praxis-200 bg-white p-10 text-center">
				<ShieldOff class="mx-auto mb-3 text-ink-400" size={32} />
				<p class="text-sm text-ink-600">Diese Ansicht ist nur für Praxisinhaber sichtbar.</p>
			</div>
		{:else}
			{#if error}
				<div class="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">{error}</div>
			{/if}

			<section class="rounded-xl border border-praxis-200 bg-white shadow-sm">
				<div class="border-b border-praxis-200 bg-praxis-50 px-5 py-3">
					<h2 class="text-xs font-semibold uppercase tracking-wider text-praxis-700">Benutzer</h2>
				</div>
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="text-left text-[11px] font-semibold uppercase tracking-wider text-ink-500">
								<th class="px-5 py-2.5">ID</th>
								<th class="px-5 py-2.5">Name</th>
								<th class="px-5 py-2.5">Rollen</th>
								<th></th>
							</tr>
						</thead>
						<tbody class="divide-y divide-praxis-100">
							{#each users as u (u.id)}
								<tr class="transition hover:bg-praxis-50/40">
									<td class="px-5 py-3 font-mono text-xs text-ink-700">{u.id}</td>
									<td class="px-5 py-3 font-medium text-ink-900">{u.display_name}</td>
									<td class="px-5 py-3">
										<div class="flex flex-wrap gap-1">
											{#each roles as r (r.id)}
												<button
													class={`rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider transition ${
														u.roles.includes(r.id)
															? 'border-praxis-400 bg-praxis-100 text-praxis-800'
															: 'border-praxis-200 bg-white text-ink-400 hover:border-praxis-300 hover:text-ink-700'
													}`}
													onclick={() => toggle(u.id, r.id)}
													title={r.description}
												>
													{r.display_name}
												</button>
											{/each}
										</div>
									</td>
									<td class="px-5 py-3 text-right">
										<button
											class="text-ink-400 transition hover:text-red-600"
											onclick={() => del(u.id)}
											title="Löschen"
										>
											<Trash2 size={15} />
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>

			<section class="mt-6 rounded-xl border border-praxis-200 bg-white shadow-sm">
				<div class="border-b border-praxis-200 bg-praxis-50 px-5 py-3">
					<h2 class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-praxis-700">
						<UserPlus size={13} /> Neuen Benutzer anlegen
					</h2>
				</div>
				<form onsubmit={createUser} class="grid grid-cols-1 gap-4 p-5 sm:grid-cols-3">
					<div>
						<label class="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-praxis-700" for="nu_id">Benutzername</label>
						<input id="nu_id" type="text" bind:value={nu_id} required placeholder="benutzername"
							class="w-full rounded-lg border border-praxis-300 px-3 py-2 text-sm focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20" />
					</div>
					<div>
						<label class="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-praxis-700" for="nu_name">Anzeigename</label>
						<input id="nu_name" type="text" bind:value={nu_name} placeholder="Max Mustermann"
							class="w-full rounded-lg border border-praxis-300 px-3 py-2 text-sm focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20" />
					</div>
					<div>
						<label class="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-praxis-700" for="nu_pw">Passwort</label>
						<input id="nu_pw" type="password" bind:value={nu_pw} required placeholder="••••••"
							class="w-full rounded-lg border border-praxis-300 px-3 py-2 text-sm focus:border-praxis-500 focus:outline-none focus:ring-2 focus:ring-praxis-500/20" />
					</div>

					<div class="sm:col-span-3">
						<div class="mb-2 text-[11px] font-semibold uppercase tracking-wider text-praxis-700">Rollen</div>
						<div class="flex flex-wrap gap-1.5">
							{#each roles as r (r.id)}
								<label class={`flex cursor-pointer items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-xs transition ${
									nu_roles.has(r.id)
										? 'border-praxis-400 bg-praxis-100 text-praxis-800'
										: 'border-praxis-200 bg-white text-ink-600 hover:border-praxis-300'
								}`}>
									<input
										type="checkbox"
										class="hidden"
										checked={nu_roles.has(r.id)}
										onchange={(e) => {
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

					<div class="sm:col-span-3 flex justify-end">
						<button class="rounded-lg bg-praxis-700 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-praxis-800">
							Anlegen
						</button>
					</div>
				</form>
			</section>
		{/if}
	</main>
</div>
