// Single WebSocket connection, multiplexed by channel.

type Listener = (event: any) => void;

class WSClient {
	private ws: WebSocket | null = null;
	private listeners = new Map<string, Set<Listener>>();
	private subscribed = new Set<string>();
	private connecting = false;
	private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

	connect() {
		if (this.ws || this.connecting) return;
		this.connecting = true;
		const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		this.ws = new WebSocket(`${proto}//${window.location.host}/ws`);
		this.ws.onopen = () => {
			this.connecting = false;
			// re-subscribe on reconnect
			for (const ch of this.subscribed) {
				this.ws?.send(JSON.stringify({ action: 'subscribe', channel: ch }));
			}
		};
		this.ws.onmessage = (e) => {
			try {
				const { channel, event } = JSON.parse(e.data);
				this.listeners.get(channel)?.forEach((fn) => fn(event));
			} catch {}
		};
		this.ws.onclose = () => {
			this.ws = null;
			this.connecting = false;
			if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
			this.reconnectTimer = setTimeout(() => this.connect(), 1500);
		};
		this.ws.onerror = () => {
			this.ws?.close();
		};
	}

	subscribe(channel: string, fn: Listener): () => void {
		if (!this.listeners.has(channel)) this.listeners.set(channel, new Set());
		this.listeners.get(channel)!.add(fn);
		if (!this.subscribed.has(channel)) {
			this.subscribed.add(channel);
			if (this.ws?.readyState === WebSocket.OPEN) {
				this.ws.send(JSON.stringify({ action: 'subscribe', channel }));
			}
		}
		this.connect();
		return () => {
			this.listeners.get(channel)?.delete(fn);
			if (this.listeners.get(channel)?.size === 0) {
				this.subscribed.delete(channel);
				if (this.ws?.readyState === WebSocket.OPEN) {
					this.ws.send(JSON.stringify({ action: 'unsubscribe', channel }));
				}
			}
		};
	}
}

export const wsClient = new WSClient();
