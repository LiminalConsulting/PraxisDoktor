/**
 * Public-site API client. Talks to the practice server's /api/public/* endpoints
 * over the Cloudflare Tunnel (host: app.{practice-domain}).
 *
 * The PUBLIC_KEY is *not* secret — it's a friction-reducer against drive-by
 * spam, not a security boundary. Real auth happens at the tunnel layer
 * (Cloudflare Access optional) and at the rate-limit in the FastAPI route.
 */

const API_BASE: string = (import.meta.env.VITE_PRACTICE_API ?? '').replace(/\/$/, '');
const PUBLIC_KEY: string = import.meta.env.VITE_PUBLIC_API_KEY ?? '';

async function post<T = unknown>(path: string, body: unknown): Promise<T> {
	if (!API_BASE) throw new Error('VITE_PRACTICE_API not configured');
	const res = await fetch(`${API_BASE}${path}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-Public-Key': PUBLIC_KEY
		},
		body: JSON.stringify(body)
	});
	if (!res.ok) {
		const text = await res.text().catch(() => '');
		throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
	}
	return res.json();
}

export interface BookingRequest {
	name: string;
	contact: string;
	reason?: string;
	desired_slot?: string;
	is_new_patient?: boolean;
}

export interface AnamneseSubmission {
	name: string;
	dob?: string;
	answers: Record<string, string | number | boolean | null>;
}

export const api = {
	bookingRequest: (body: BookingRequest) =>
		post<{ id: string; ok: true }>('/api/public/booking-request', body),

	anamneseSubmit: (body: AnamneseSubmission) =>
		post<{ id: string; ok: true }>('/api/public/anamnese-submit', body),

	anamneseStart: (name?: string) =>
		post<{ id: string; ok: true }>('/api/public/anamnese-start', { name: name ?? '' })
};
