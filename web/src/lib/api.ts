// Typed API client. Backend runs on :8080; Vite proxies /api and /ws.

export type Process = {
	id: string;
	display_name: string;
	icon: string;
	surface: 'tool' | 'conversation' | 'dashboard_only';
	phase: 'decline' | 'dashboard_only' | 'placeholder' | 'co_pilot' | 'autonomous';
	chat_attached: boolean;
	inputs: string[];
	outputs: string[];
	transition_types?: Record<string, { feeds_back?: boolean }>;
	position?: number;
	chat_count?: number;
};

export type Me = { id: string; display_name: string; roles: string[] };

export type Transition = {
	id: string;
	actor: string;
	type: string;
	payload: Record<string, unknown>;
	feeds_back: boolean;
	retracted_by: string | null;
	timestamp: string;
};

export type ChatMessage = {
	id: string;
	process_id: string;
	user_id: string;
	body: string;
	created_at: string;
};

export type ProcessInstance = {
	id: string;
	process_id: string;
	title: string;
	status: string;
	created_at: string;
	updated_at: string;
	current_state: Record<string, any>;
};

async function jfetch<T>(url: string, init: RequestInit = {}): Promise<T> {
	const res = await fetch(url, {
		credentials: 'include',
		headers: { 'Content-Type': 'application/json', ...(init.headers || {}) },
		...init
	});
	if (!res.ok) {
		const text = await res.text();
		throw new Error(`${res.status} ${res.statusText}: ${text}`);
	}
	if (res.status === 204) return undefined as T;
	return (await res.json()) as T;
}

export const api = {
	async login(username: string, password: string): Promise<{ ok: boolean; user: { id: string; display_name: string } }> {
		const fd = new FormData();
		fd.append('username', username);
		fd.append('password', password);
		const res = await fetch('/api/auth/login', { method: 'POST', body: fd, credentials: 'include' });
		if (!res.ok) throw new Error((await res.text()) || 'Login fehlgeschlagen');
		return res.json();
	},
	logout: () => jfetch('/api/auth/logout', { method: 'POST' }),
	me: () => jfetch<Me>('/api/auth/me'),
	changePassword: (old_password: string, new_password: string) =>
		jfetch('/api/auth/change-password', {
			method: 'POST',
			body: JSON.stringify({ old_password, new_password })
		}),

	intakeHealth: () => jfetch<{ ollama: { reachable: boolean; model_present?: boolean; expected_model: string; available_models?: string[]; error?: string } }>('/api/intake/health'),

	markSeen: (pid: string) =>
		jfetch<{ ok: boolean; last_seen_at: string }>(`/api/dashboard/seen/${pid}`, { method: 'POST' }),

	dashboard: () => jfetch<{ processes: Process[] }>('/api/dashboard'),
	saveLayout: (order: string[]) =>
		jfetch('/api/dashboard/layout', { method: 'POST', body: JSON.stringify({ order }) }),

	processMeta: (pid: string) => jfetch<Process>(`/api/processes/${pid}`),

	listInstances: (pid: string) =>
		jfetch<ProcessInstance[]>(`/api/processes/${pid}/instances`),
	createInstance: (pid: string, title: string) =>
		jfetch<ProcessInstance>(`/api/processes/${pid}/instances`, {
			method: 'POST',
			body: JSON.stringify({ title })
		}),
	getInstance: (pid: string, iid: string) =>
		jfetch<ProcessInstance>(`/api/processes/${pid}/instances/${iid}`),
	listTransitions: (pid: string, iid: string) =>
		jfetch<Transition[]>(`/api/processes/${pid}/instances/${iid}/transitions`),
	appendTransition: (pid: string, iid: string, type: string, payload: Record<string, unknown>) =>
		jfetch<{ id: string }>(`/api/processes/${pid}/instances/${iid}/transitions`, {
			method: 'POST',
			body: JSON.stringify({ type, payload })
		}),
	undo: (pid: string, iid: string) =>
		jfetch<{ id: string; undid: string; undid_type: string }>(
			`/api/processes/${pid}/instances/${iid}/undo`,
			{ method: 'POST' }
		),

	listMessages: (pid: string) => jfetch<ChatMessage[]>(`/api/chat/${pid}/messages`),
	sendMessage: (pid: string, body: string) =>
		jfetch<ChatMessage>(`/api/chat/${pid}/messages`, {
			method: 'POST',
			body: JSON.stringify({ body })
		}),

	uploadAudio: async (iid: string, file: File | Blob, filename = 'audio.webm') => {
		const fd = new FormData();
		fd.append('file', file, filename);
		const res = await fetch(`/api/intake/${iid}/audio`, {
			method: 'POST',
			body: fd,
			credentials: 'include'
		});
		if (!res.ok) throw new Error(await res.text());
		return res.json();
	},
	uploadForm: async (iid: string, file: File | Blob, filename = 'form.png') => {
		const fd = new FormData();
		fd.append('file', file, filename);
		const res = await fetch(`/api/intake/${iid}/form`, {
			method: 'POST',
			body: fd,
			credentials: 'include'
		});
		if (!res.ok) throw new Error(await res.text());
		return res.json();
	},

	listAdminUsers: () =>
		jfetch<{ id: string; display_name: string; roles: string[] }[]>('/api/admin/users'),
	listAdminRoles: () =>
		jfetch<{ id: string; display_name: string; description: string }[]>('/api/admin/roles'),
	createAdminUser: (payload: { id: string; display_name: string; password: string; roles: string[] }) =>
		jfetch('/api/admin/users', { method: 'POST', body: JSON.stringify(payload) }),
	setAdminUserRoles: (uid: string, roles: string[]) =>
		jfetch(`/api/admin/users/${uid}/roles`, { method: 'PUT', body: JSON.stringify({ roles }) }),
	deleteAdminUser: (uid: string) =>
		jfetch(`/api/admin/users/${uid}`, { method: 'DELETE' })
};
