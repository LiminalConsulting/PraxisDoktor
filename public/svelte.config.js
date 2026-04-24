import adapter from '@sveltejs/adapter-cloudflare';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	compilerOptions: {
		runes: ({ filename }) => (filename.split(/[/\\]/).includes('node_modules') ? undefined : true)
	},
	kit: {
		adapter: adapter({
			// Single-page-app mode: every request that doesn't match a static asset
			// renders index.html, then the client takes over. Keeps the public
			// site latency near zero (Cloudflare edge cache) and means we don't
			// run Workers for routing — only when forms POST to the practice tunnel.
			routes: { include: ['/*'], exclude: ['<all>'] }
		}),
		prerender: { entries: ['*'] }
	}
};

export default config;
