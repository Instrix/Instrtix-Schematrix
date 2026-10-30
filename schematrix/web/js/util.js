// Small shared helpers: DOM lookup, cloning, snapping and the HTTP client.

export const $ = (s, el = document) => el.querySelector(s);
export const $$ = (s, el = document) => [...el.querySelectorAll(s)];
export const NS = 'http://www.w3.org/2000/svg';
export const clone = (o) => JSON.parse(JSON.stringify(o));
export const snapTo = (v, g) => Math.round(v / g) * g;

// ---------------------------------------------------------------- api
export const api = {
  async req(method, url, body, raw) {
    const r = await fetch(url, { method, headers: body !== undefined && !raw ? { 'Content-Type': 'application/json' } : {},
      body: body === undefined ? undefined : raw ? body : JSON.stringify(body) });
    if (!r.ok) {
      let msg = r.statusText;
      try { msg = (await r.json()).detail || msg; } catch { /* not json */ }
      throw new Error(msg);
    }
    return r;
  },
  get: (u) => api.req('GET', u).then((r) => r.json()),
  post: (u, b) => api.req('POST', u, b).then((r) => r.json()),
  blob: (u, b) => api.req('POST', u, b).then((r) => r.blob()),
  put: (u, text) => api.req('PUT', u, text, true).then((r) => r.json()),
  del: (u) => api.req('DELETE', u).then((r) => r.json()),
};


export const svg = $('#canvas');
