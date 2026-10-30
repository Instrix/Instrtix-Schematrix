// The symbol palette.
import * as G from './geom.js';
import { S } from './state.js';
import { startPlacing } from './tools.js';
import { $, svg } from './util.js';

// ---------------------------------------------------------------- palette
export function symThumb(entry, props) {
  const g = entry.geometry;
  const c = { id: 't', type: 'comp', sym: entry.name, x: 0, y: 0, rot: 0, props: props || {}, hide_labels: true };
  const body = g.prims.map((p) => G.primSvg(p, c, '')).join('');
  const [x0, y0, x1, y1] = g.bbox, pad = 4;
  return `<svg class="schp" viewBox="${x0 - pad} ${y0 - pad} ${x1 - x0 + 2 * pad} ${y1 - y0 + 2 * pad}" preserveAspectRatio="xMidYMid meet">${body}</svg>`;
}
export function buildPalette(filter = '') {
  const pal = $('#palette'), f = filter.trim().toLowerCase();
  pal.innerHTML = '';
  let lastCat = null, grid = null;
  for (const e of S.catList) {
    if (f && !(e.title.toLowerCase().includes(f) || e.name.includes(f) || e.category.toLowerCase().includes(f))) continue;
    if (e.category !== lastCat) {
      lastCat = e.category;
      pal.insertAdjacentHTML('beforeend', `<div class="cat">${G.esc(e.category)}</div>`);
      grid = document.createElement('div'); grid.className = 'syms'; pal.append(grid);
    }
    const b = document.createElement('div');
    b.className = 'sym' + (S.placing?.sym === e.name ? ' on' : '');
    b.title = `${e.title}${e.help ? ' — ' + e.help : ''}\npins: ${Object.keys(e.geometry.pins).join(', ')}`;
    b.innerHTML = symThumb(e) + `<span>${G.esc(e.title)}</span>`;
    b.onclick = () => startPlacing(e.name);
    grid.append(b);
  }
}
