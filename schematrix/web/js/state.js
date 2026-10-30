// Editor state, the geometry cache, tabs, undo/redo and browser autosave.
import * as G from './geom.js';
import { cmd } from './commands.js';
import { renderInspector } from './inspector.js';
import { confirmBox, toast } from './ui.js';
import { $, api } from './util.js';
import { applyView, fit, render } from './view.js';

// ---------------------------------------------------------------- state
export const S = {
  info: {}, cat: {}, catList: [], geo: new Map(), geoQueue: new Map(), geoTimer: 0,
  tabs: [], cur: null, tool: 'select', placing: null, draft: null, drag: null, style: '',
  mouse: [0, 0], space: false, grid: true, lastFlag: 'NET', wireMode: 'auto', rawBB: new Map(), netHL: null,
};
export const T = () => S.cur;
export const D = () => S.cur.doc;

export function newDoc(title = 'Untitled') {
  return { version: 1, meta: { title, description: '' }, page: { width: 800, height: 500, auto: false, margin: 20, grid: 5, junctions: true },
    theme: 'instrix', elements: [] };
}

// ---------------------------------------------------------------- geometry cache
export function geoKey(sym, props) {
  const c = S.cat[sym];
  if (!c) return sym;
  return sym + '|' + c.geom_keys.map((k) => String(props?.[k] ?? c.props[k].default)).join('|');
}
export function geoOf(e) {
  const k = geoKey(e.sym, e.props);
  const g = S.geo.get(k);
  if (g) return g;
  if (!S.geoQueue.has(k)) {
    const c = S.cat[e.sym];
    const props = {};
    if (c) for (const gk of c.geom_keys) if (e.props && gk in e.props) props[gk] = e.props[gk];
    S.geoQueue.set(k, { sym: e.sym, props });
    clearTimeout(S.geoTimer);
    S.geoTimer = setTimeout(flushGeo, 15);
  }
  return null;
}
export async function flushGeo() {
  const items = [...S.geoQueue];
  if (!items.length) return;
  S.geoQueue.clear();
  try {
    const res = await api.post('/api/geometry', { items: items.map(([, v]) => v) });
    res.forEach((g, i) => { if (!g.error) S.geo.set(items[i][0], g); else toast(g.error, true); });
  } catch (err) { toast('geometry: ' + err.message, true); }
  render();
  if (S.cur?.fitPending) fit();
}
export const pinsOf = (e) => G.compPins(e, geoOf(e));

// ---------------------------------------------------------------- tabs & history
export let tabSeq = 0;
export function openTab(doc, path = null, focus = true) {
  const t = { id: ++tabSeq, doc, path, undo: [], redo: [], dirty: false, sel: new Set(), view: null };
  // replace the blank start-up tab instead of piling up "Untitled"s
  const blank = S.tabs.find((o) => !o.path && !o.dirty && !o.doc.elements.length && !o.undo.length);
  if (blank && doc.elements.length) S.tabs.splice(S.tabs.indexOf(blank), 1);
  S.tabs.push(t);
  if (focus) switchTab(t);
  return t;
}
export function switchTab(t) {
  S.cur = t; S.draft = null; S.netHL = null; S.rawBB.clear();
  render(); renderTabs(); renderInspector();
  if (!t.view) { t.fitPending = true; requestAnimationFrame(() => fit()); } else applyView();
}
export async function closeTab(t) {
  if (t.dirty && !(await confirmBox(`“${tabTitle(t)}” has unsaved changes. Close it anyway?`, 'Close'))) return;
  const i = S.tabs.indexOf(t);
  S.tabs.splice(i, 1);
  if (!S.tabs.length) openTab(newDoc());
  else if (S.cur === t) switchTab(S.tabs[Math.max(0, i - 1)]);
  renderTabs(); persist();
}
export const tabTitle = (t) => t.doc.meta?.title || (t.path ? t.path.replace(/\.json$/, '') : 'Untitled');
export function renderTabs() {
  const el = $('#tabs');
  el.innerHTML = '';
  for (const t of S.tabs) {
    const d = document.createElement('div');
    d.className = 'tab' + (t === S.cur ? ' on' : '');
    d.title = t.path || 'not saved yet';
    d.innerHTML = `<span>${G.esc(tabTitle(t))}</span>${t.dirty ? '<i class="d"></i>' : ''}<button title="Close">×</button>`;
    d.onclick = (ev) => { if (ev.target.tagName === 'BUTTON') closeTab(t); else if (t !== S.cur) switchTab(t); };
    d.onauxclick = (ev) => { if (ev.button === 1) closeTab(t); };
    el.append(d);
  }
  const nb = document.createElement('button');
  nb.className = 'newtab'; nb.textContent = '+'; nb.title = 'New schematic (Ctrl+N)';
  nb.onclick = () => cmd('new');
  el.append(nb);
  $('#savebtn').classList.toggle('dirty', !!S.cur?.dirty);
  document.title = (S.cur?.dirty ? '• ' : '') + (S.cur ? tabTitle(S.cur) + ' — ' : '') + 'Schematrix';
}

export function snapshot() { return JSON.stringify(D()); }
export function pushUndo(snap, coalesce) {
  const t = T(), now = Date.now();
  if (coalesce && t.lastCo === coalesce && now - t.lastCoT < 1500) { t.lastCoT = now; return; }
  t.undo.push(snap);
  if (t.undo.length > 300) t.undo.shift();
  t.redo = []; t.lastCo = coalesce; t.lastCoT = now;
}
export function changed() {
  T().dirty = true; T().fitPending = false;
  render(); renderInspector(); renderTabs(); persistSoon();
}
export function edit(fn, coalesce) {
  const snap = snapshot();
  fn(D());
  if (snapshot() === snap) return;
  pushUndo(snap, coalesce);
  changed();
}
export function undo() {
  const t = T();
  if (!t.undo.length) return;
  t.redo.push(snapshot()); t.doc = JSON.parse(t.undo.pop()); t.lastCo = null;
  pruneSel(); changed();
}
export function redo() {
  const t = T();
  if (!t.redo.length) return;
  t.undo.push(snapshot()); t.doc = JSON.parse(t.redo.pop());
  pruneSel(); changed();
}
export function pruneSel() { const ids = new Set(D().elements.map((e) => e.id)); for (const id of [...T().sel]) if (!ids.has(id)) T().sel.delete(id); }

export function nextId(doc = D()) {
  let n = 0;
  for (const e of doc.elements) { const m = /^[a-z]+(\d+)$/.exec(e.id || ''); if (m) n = Math.max(n, +m[1]); }
  return 'e' + (n + 1);
}
export function nextRef(prefix, doc = D(), extra = new Set()) {
  if (!prefix) return '';
  const used = new Set(doc.elements.filter((e) => e.type === 'comp').map((e) => e.props?.ref));
  let i = 1;
  while (used.has(prefix + i) || extra.has(prefix + i)) i++;
  return prefix + i;
}
export const byId = (id) => D().elements.find((e) => e.id === id);
export const selected = () => D().elements.filter((e) => T().sel.has(e.id));

// ---------------------------------------------------------------- persistence (browser autosave)
export let persistTimer = 0;
export function persistSoon() { clearTimeout(persistTimer); persistTimer = setTimeout(persist, 800); }
export function persist() {
  try {
    localStorage.setItem('schematrix-session', JSON.stringify({ cur: S.tabs.indexOf(S.cur),
      tabs: S.tabs.map((t) => ({ doc: t.doc, path: t.path, dirty: t.dirty })) }));
  } catch { /* storage full or blocked: autosave is best effort */ }
}
export function restore() {
  try {
    const s = JSON.parse(localStorage.getItem('schematrix-session') || 'null');
    if (s?.tabs?.length) {
      for (const t of s.tabs) { const tab = openTab(t.doc, t.path, false); tab.dirty = t.dirty; }
      switchTab(S.tabs[Math.min(Math.max(0, s.cur), S.tabs.length - 1)]);
      return true;
    }
  } catch { /* ignore a corrupt session */ }
  return false;
}
