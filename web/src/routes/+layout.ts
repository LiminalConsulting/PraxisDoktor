// Pure SPA — no SSR, no prerendering. The whole app boots client-side and
// talks to the FastAPI backend via /api and /ws.
export const ssr = false;
export const prerender = false;
export const trailingSlash = 'ignore';
