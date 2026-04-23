import { writable } from 'svelte/store';
import type { Me } from '$lib/api';
import { api } from '$lib/api';

export const me = writable<Me | null>(null);

export async function loadMe(): Promise<Me | null> {
	try {
		const m = await api.me();
		me.set(m);
		return m;
	} catch {
		me.set(null);
		return null;
	}
}

export async function logout() {
	try {
		await api.logout();
	} finally {
		me.set(null);
	}
}
