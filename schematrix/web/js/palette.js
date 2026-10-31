// The symbol palette.
import * as G from './geom.js';
import { S } from './state.js';
import { renderInspector } from './inspector.js';
import { openSymbolEditor } from './symedit.js';
import { placeAt, setTool, startPlacing } from './tools.js';
import { fullOnly } from './ui.js';
import { toWorld } from './view.js';
import { $, svg } from './util.js';

// ---------------------------------------------------------------- palette
export function symThumb(entry, props, g = entry.geometry) {
  const c = { id: 't', type: 'comp', sym: entry.name, x: 0, y: 0, rot: 0, props: props || {}, hide_labels: true };
  const body = g.prims.map((p) => G.primSvg(p, c, '')).join('');
  const [x0, y0, x1, y1] = g.bbox, pad = 4;
  return `<svg class="schp" viewBox="${x0 - pad} ${y0 - pad} ${x1 - x0 + 2 * pad} ${y1 - y0 + 2 * pad}" preserveAspectRatio="xMidYMid meet">${body}</svg>`;
}
const FOLD_KEY = 'schematrix-palette-folded';
function folded() { try { return new Set(JSON.parse(localStorage.getItem(FOLD_KEY) || '[]')); } catch { return new Set(); } }
function setFolded(s) { try { localStorage.setItem(FOLD_KEY, JSON.stringify([...s])); } catch { /* best effort */ } }

export function buildPalette(filter = '') {
  const pal = $('#palette'), f = filter.trim().toLowerCase(), fold = folded();
  pal.innerHTML = '';
  let lastCat = null, grid = null;
  const same = (a, b) => JSON.stringify(a || {}) === JSON.stringify(b || {});
  for (const e of S.catList) {
    // one tile per preset (Zener diode, NAND gate, ...); the bare symbol too unless a preset stands for it
    const tiles = (e.presets || []).some((p) => same(p.props, {})) ? [] : [{ name: e.name, title: e.title, props: {}, geometry: e.geometry }];
    tiles.push(...(e.presets || []));
    const shown = tiles.filter((t) => !f || t.title.toLowerCase().includes(f) || t.name.includes(f) || e.name.includes(f)
      || e.category.toLowerCase().includes(f));
    if (!shown.length) continue;
    if (e.category !== lastCat) {
      lastCat = e.category;
      const cat = e.category, head = document.createElement('div');
      head.className = 'cat' + (!f && fold.has(cat) ? ' folded' : ''); head.textContent = cat; head.title = 'Click to fold';
      head.onclick = () => { const s = folded(); if (s.has(cat)) s.delete(cat); else s.add(cat); setFolded(s); buildPalette($('#symsearch').value); };
      grid = document.createElement('div'); grid.className = 'syms'; grid.hidden = !f && fold.has(cat);
      pal.append(head, grid);
    }
    for (const t of shown) {
      const b = document.createElement('div');
      b.className = 'sym' + (S.placing?.sym === e.name && same(S.placing.props, t.props) ? ' on' : '');
      b.title = `${t.title}${e.help ? ' — ' + e.help : ''}\npins: ${Object.keys(t.geometry.pins).join(', ')}`;
      b.innerHTML = symThumb(e, t.props, t.geometry) + `<span>${G.esc(t.title)}</span>`;
      // press and drag onto the sheet drops one part; a plain click enters click-to-place mode (repeatable)
      b.oncontextmenu = (ev) => {                   // right-click: edit a custom symbol, or start a custom copy
        ev.preventDefault();
        if (S.info.public) return fullOnly('The symbol editor');
        openSymbolEditor(e.custom ? { edit: e.name } : { copy: e.name, props: t.props });
      };
      if (e.custom) b.classList.add('custom');
      b.onpointerdown = (ev) => {
        if (ev.button !== 0) return;
        ev.preventDefault();
        startPlacing(e.name, { ...t.props });
        S.dragPlace = { x: ev.clientX, y: ev.clientY };
      };
      grid.append(b);
    }
  }
}

// the end of a palette drag: dropped on the sheet -> place one part there and go back to selecting
document.addEventListener('pointerup', (ev) => {
  const dp = S.dragPlace;
  if (!dp) return;
  S.dragPlace = null;
  if (Math.hypot(ev.clientX - dp.x, ev.clientY - dp.y) < 6 || !S.placing) return;     // a click: stay in place mode
  const r = svg.getBoundingClientRect();
  if (ev.clientX < r.left || ev.clientX > r.right || ev.clientY < r.top || ev.clientY > r.bottom) { setTool('select'); return; }
  placeAt(toWorld(ev));
  setTool('select');
  renderInspector();
}, true);
