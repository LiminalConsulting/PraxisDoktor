<script lang="ts">
	import { goto } from '$app/navigation';
	import { logout, me } from '$lib/stores/auth';
	import { Home, LogOut, Settings, Stethoscope, RotateCcw } from 'lucide-svelte';

	let showAdmin = $derived(($me?.roles ?? []).includes('praxisinhaber'));
	let resetBusy = $state(false);
	let resetMsg = $state<string | null>(null);

	async function doLogout() {
		await logout();
		await goto('/login');
	}

	async function resetDemo() {
		const ok = window.confirm(
			'Demo zurücksetzen?\n\nAlle Eingaben in Anamnesebögen, Verbesserungs-Wünsche und Patientenaufnahme werden gelöscht.\nDie Werkzeuge und Konten bleiben bestehen.'
		);
		if (!ok) return;
		resetBusy = true;
		resetMsg = null;
		try {
			const res = await fetch('/api/demo/reset', {
				method: 'POST',
				credentials: 'include',
			});
			if (!res.ok) throw new Error(await res.text());
			const data = await res.json();
			const total = Object.values(data.wiped_instances ?? {}).reduce((a: number, b: any) => a + Number(b), 0);
			resetMsg = `${total} Einträge gelöscht`;
			setTimeout(() => (resetMsg = null), 3000);
			// reload current page to reflect cleared state
			window.location.reload();
		} catch (e) {
			resetMsg = 'Fehler beim Zurücksetzen';
			setTimeout(() => (resetMsg = null), 3000);
		} finally {
			resetBusy = false;
		}
	}
</script>

<header class="flex h-14 items-center justify-between bg-praxis-700 px-5 text-white shadow-[0_2px_8px_rgba(0,0,0,0.10)]">
	<div class="flex items-center gap-4">
		<button
			class="flex items-center gap-2"
			onclick={() => goto('/dashboard')}
			title="Zum Dashboard"
		>
			<div class="flex h-8 w-8 items-center justify-center rounded-md bg-white/10">
				<Stethoscope size={18} />
			</div>
			<div class="text-left">
				<div class="text-sm font-semibold leading-tight">PraxisDoktor</div>
				<div class="text-[10px] uppercase tracking-wider opacity-70">Urologie Karlsruhe</div>
			</div>
		</button>
		<button
			class="ml-2 flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-white/80 transition hover:bg-white/10 hover:text-white"
			onclick={() => goto('/dashboard')}
			title="Dashboard"
		>
			<Home size={15} /> Dashboard
		</button>
	</div>

	<div class="flex items-center gap-1.5 text-sm">
		{#if showAdmin}
			{#if resetMsg}
				<span class="rounded-md bg-white/15 px-2 py-1 text-[11px]">{resetMsg}</span>
			{/if}
			<button
				class="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-white/80 transition hover:bg-white/10 hover:text-white disabled:opacity-50"
				onclick={resetDemo}
				disabled={resetBusy}
				title="Demo zurücksetzen (löscht Eingaben in Anamnesebögen, Verbesserungs-Wünsche, Patientenaufnahme)"
			>
				<RotateCcw size={15} class={resetBusy ? 'animate-spin' : ''} /> Demo zurücksetzen
			</button>
			<button
				class="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-white/80 transition hover:bg-white/10 hover:text-white"
				onclick={() => goto('/admin')}
			>
				<Settings size={15} /> Admin
			</button>
		{/if}
		<button
			class="ml-2 mr-1 flex items-center gap-2 rounded-md bg-white/10 px-3 py-1.5 text-xs transition hover:bg-white/20"
			onclick={() => goto('/account')}
			title="Mein Konto"
		>
			<div class="flex h-6 w-6 items-center justify-center rounded-full bg-white/20 text-[10px] font-semibold uppercase">
				{$me?.display_name?.[0] ?? '?'}
			</div>
			<span class="opacity-90">{$me?.display_name}</span>
		</button>
		<button
			class="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-white/80 transition hover:bg-white/10 hover:text-white"
			onclick={doLogout}
			title="Abmelden"
		>
			<LogOut size={15} />
		</button>
	</div>
</header>
