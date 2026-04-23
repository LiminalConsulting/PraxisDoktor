import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	compilerOptions: {
		runes: ({ filename }) => (filename.split(/[/\\]/).includes('node_modules') ? undefined : true)
	},
	kit: {
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			fallback: 'index.html', // SPA fallback — every route renders client-side
			precompress: false,
			strict: false
		}),
		// All routes are SPA-rendered (we use $page on every page); SSR is off so
		// session-cookie checks happen client-side only.
		prerender: { entries: [] }
	}
};

export default config;
