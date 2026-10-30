// The properties inspector.
import * as G from './geom.js';
import { del, reorder, transformSel } from './selection.js';
import { D, edit, pinsOf, S, selected } from './state.js';
import { $ } from './util.js';
import { docBBox, pageBox } from './view.js';

// ---------------------------------------------------------------- inspector
export function field(label, input) {
  const d = document.createElement('div');
  d.className = 'f';
  const l = document.createElement('label'); l.textContent = label;
  if (!input.dataset.k) input.dataset.k = label;
  d.append(l, input);
  return d;
}

// the inspector is rebuilt after every edit: put the caret back in the input that was being typed in
function keepFocus(build) {
  const a = document.activeElement, k = a?.closest?.('#pane-props') ? a.dataset.k : null;
  const range = k && 'selectionStart' in a ? [a.selectionStart, a.selectionEnd] : null;
  build();
  if (!k) return;
  const b = $(`#pane-props [data-k="${CSS.escape(k)}"]`);
  if (!b) return;
  b.focus();
  if (range) try { b.setSelectionRange(...range); } catch { /* not a text input */ }
}

// user fields (tolerance, voltage rating, ...): name, value, and whether the value prints on the sheet
function fieldsEditor(e, c) {
  const wrap = document.createElement('div');
  wrap.append(sect('Fields'));
  const fs = e.fields || [];
  fs.forEach((f, i) => {
    const row = document.createElement('div'); row.className = 'fieldrow';
    const name = inp(f.name, (v) => edit(() => { e.fields[i].name = v.trim() || f.name; }));
    name.placeholder = 'Name'; name.dataset.k = `field:${i}:name`;
    const val = inp(f.value, (v, co) => edit(() => { e.fields[i].value = v; }, co ? `${e.id}.f.${i}` : undefined), { mono: true, coalesce: true });
    val.placeholder = 'Value'; val.dataset.k = `field:${i}:value`;
    const show = chk(f.show, (v) => edit(() => { e.fields[i].show = v; })); show.title = 'Show the value on the sheet';
    const rm = document.createElement('button'); rm.textContent = '×'; rm.title = 'Remove field';
    rm.onclick = () => edit(() => { e.fields.splice(i, 1); if (!e.fields.length) delete e.fields; });
    row.append(name, val, show, rm);
    wrap.append(row);
  });
  const add = (name) => edit(() => { (e.fields ||= []).push({ name, value: '', show: false }); });
  const have = new Set(fs.map((f) => f.name));
  const chips = document.createElement('div'); chips.className = 'chips';
  for (const n of (c?.fields || []).filter((n) => !have.has(n))) {
    const b = document.createElement('button'); b.textContent = '+ ' + n; b.onclick = () => add(n); chips.append(b);
  }
  const b = document.createElement('button'); b.textContent = '+ Field…';
  b.onclick = () => { let n = 'Field', k = 1; while (have.has(n)) n = `Field ${++k}`; add(n); };
  chips.append(b);
  wrap.append(chips);
  return wrap;
}
export function inp(value, onChange, { type = 'text', mono = false, step, coalesce } = {}) {
  const i = document.createElement('input');
  i.type = type; i.value = value ?? '';
  if (mono) i.className = 'mono';
  if (step) i.step = step;
  i.onchange = () => onChange(type === 'number' ? Number(i.value) : i.value);
  if (coalesce) i.oninput = () => onChange(type === 'number' ? Number(i.value) : i.value, true);
  i.onkeydown = (ev) => { ev.stopPropagation(); if (ev.key === 'Enter') i.blur(); };
  return i;
}
export function sel_(value, options, onChange) {
  const s = document.createElement('select');
  for (const o of options) { const [v, t] = Array.isArray(o) ? o : [o, o]; const op = new Option(t, v); if (String(v) === String(value)) op.selected = true; s.append(op); }
  s.onchange = () => onChange(s.value);
  return s;
}
export function chk(value, onChange) {
  const c = document.createElement('input');
  c.type = 'checkbox'; c.checked = !!value; c.onchange = () => onChange(c.checked);
  return c;
}
export function pair(a, b) { const d = document.createElement('div'); d.className = 'pair'; d.append(a, b); return d; }
export function btns(list) {
  const d = document.createElement('div'); d.className = 'btns';
  for (const [t, fn, cls] of list) { const b = document.createElement('button'); b.textContent = t; b.onclick = fn; if (cls) b.className = cls; d.append(b); }
  return d;
}
export function seg(value, options, onChange) {
  const d = document.createElement('div'); d.className = 'seg';
  for (const [v, t] of options) { const b = document.createElement('button'); b.textContent = t; if (v === value) b.className = 'on'; b.onclick = () => onChange(v); d.append(b); }
  return d;
}
export const STYLES = [['', 'Ink'], ['acc', 'Accent'], ['para', 'Dash'], ['acc para', 'Acc·dash']];
export const sect = (t) => { const d = document.createElement('div'); d.className = 'sect'; d.textContent = t; return d; };

export function renderInspector() { keepFocus(buildInspector); }

function buildInspector() {
  const p = $('#pane-props');
  if (!S.cur) return;
  p.innerHTML = '';
  const sel = selected();
  const head = (title, sub) => { p.insertAdjacentHTML('beforeend', `<h3>${title}</h3>${sub ? `<div class="sub">${sub}</div>` : ''}`); };
  const set = (e, k, coalesce) => (v, co) => edit(() => { e[k] = v; }, co ? coalesce || `${e.id}.${k}` : undefined);
  const setp = (e, k) => (v, co) => edit(() => { e.props = { ...e.props, [k]: v }; }, co ? `${e.id}.p.${k}` : undefined);
  if (!sel.length) {
    const d = D(), pg = d.page;
    head('Document', `${d.elements.length} elements`);
    p.append(field('Title', inp(d.meta.title, (v) => edit(() => { d.meta.title = v; }))));
    const ta = document.createElement('textarea'); ta.value = d.meta.description || ''; ta.rows = 3;
    ta.onchange = () => edit(() => { d.meta.description = ta.value; }); ta.onkeydown = (ev) => ev.stopPropagation();
    p.append(field('Description', ta));
    p.append(sect('Page'));
    p.append(field('Auto size', chk(pg.auto, (v) => edit(() => { pg.auto = v; if (!v && !pg.width) { const b = pageBox(); Object.assign(pg, { x: b[0], y: b[1], width: b[2], height: b[3] }); } }))));
    if (!pg.auto) p.append(field('Size', pair(inp(pg.width, set(pg, 'width'), { type: 'number', mono: true }), inp(pg.height, set(pg, 'height'), { type: 'number', mono: true }))));
    if (!pg.auto) p.append(field('Origin', pair(inp(pg.x || 0, set(pg, 'x'), { type: 'number', mono: true }), inp(pg.y || 0, set(pg, 'y'), { type: 'number', mono: true }))));
    p.append(field('Margin', inp(pg.margin ?? 20, set(pg, 'margin'), { type: 'number', mono: true })));
    p.append(field('Grid', sel_(pg.grid || 5, [1, 2, 5, 10, 20], (v) => edit(() => { pg.grid = Number(v); }))));
    p.append(field('Junctions', chk(pg.junctions !== false, (v) => edit(() => { pg.junctions = v; }))));
    p.append(field('Wire hops', chk(!!pg.hops, (v) => edit(() => { pg.hops = v; }))));
    p.append(field('Theme', sel_(typeof d.theme === 'string' ? d.theme : 'custom', [...Object.keys(S.info.themes || {}), ...(typeof d.theme === 'object' ? ['custom'] : [])], (v) => edit(() => { d.theme = v; }))));
    p.append(btns([['Fit page to drawing', () => edit(() => {
      const bb = docBBox(), m = pg.margin ?? 20;
      Object.assign(pg, { auto: false, x: Math.floor(bb[0] - m), y: Math.floor(bb[1] - m), width: Math.ceil(bb[2] - bb[0] + 2 * m), height: Math.ceil(bb[3] - bb[1] + 2 * m) });
    })]]));
    p.insertAdjacentHTML('beforeend', `<div class="sect">Tips</div><div class="sub">Drag symbols from the left, <b>W</b> for wires (they snap to pins), <b>L</b> to name a net. Wires follow parts when you move them. Double-click any text to edit it. The <b>Script</b> tab builds schematics in Python.</div>`);
    return;
  }
  if (sel.length > 1) {
    head(`${sel.length} selected`, [...new Set(sel.map((e) => e.type === 'comp' ? S.cat[e.sym]?.title : e.type))].join(', '));
    const styled = sel.filter((e) => e.type === 'comp' || e.type === 'wire' || e.type === 'arrow');
    if (styled.length) p.append(field('Style', seg(styled[0].style || '', STYLES, (v) => edit(() => { for (const e of styled) e.style = v; }))));
    p.append(btns([['Rotate', () => transformSel('rot')], ['Mirror', () => transformSel('mir')], ['To front', () => reorder(true)], ['To back', () => reorder(false)], ['Delete', del, 'danger']]));
    return;
  }
  const e = sel[0];
  if (e.type === 'comp') {
    const c = S.cat[e.sym];
    head(`${G.esc(c?.title || e.sym)} <small>${e.sym}</small>`, '');
    for (const [k, spec] of Object.entries(c?.props || {})) {
      const v = e.props?.[k] ?? spec.default;
      let input;
      if (spec.type === 'bool') input = chk(v, setp(e, k));
      else if (spec.type === 'enum') input = sel_(v, spec.choices, setp(e, k));
      else if (spec.type === 'num') input = inp(v, setp(e, k), { type: 'number', mono: true });
      else if (spec.type === 'text') {
        input = document.createElement('textarea'); input.value = v; input.rows = 3;
        input.oninput = () => setp(e, k)(input.value, true); input.onkeydown = (ev) => ev.stopPropagation();
      } else input = inp(v, setp(e, k), { mono: k !== 'ref', coalesce: true });
      const f = field(spec.label.charAt(0).toUpperCase() + spec.label.slice(1), input);
      if (spec.help) f.title = spec.help;
      p.append(f);
    }
    if (c?.is_part !== false) p.append(fieldsEditor(e, c));
    p.append(sect('Placement'));
    p.append(field('Position', pair(inp(e.x, set(e, 'x'), { type: 'number', mono: true }), inp(e.y, set(e, 'y'), { type: 'number', mono: true }))));
    p.append(field('Rotation', seg(e.rot || 0, [[0, '0°'], [90, '90°'], [180, '180°'], [270, '270°']], set(e, 'rot'))));
    p.append(field('Mirror', chk(e.mirror, set(e, 'mirror'))));
    p.append(field('Style', seg(e.style || '', STYLES, set(e, 'style'))));
    if (c?.geometry?.lines?.length) {
      p.append(field('Labels', chk(!e.hide_labels, (v) => edit(() => { if (v) delete e.hide_labels; else e.hide_labels = true; }))));
    }
    const pins = pinsOf(e);
    p.insertAdjacentHTML('beforeend', `<div class="sect">Pins</div><div class="pinlist">${Object.entries(pins).map(([n, q]) => `<b>${G.esc(n)}</b> ${q[0]}, ${q[1]}`).join('<br>')}</div>`);
    const b = [['Rotate', () => transformSel('rot')], ['Mirror', () => transformSel('mir')]];
    if (e.label_offset) b.push(['Reset label', () => edit(() => { delete e.label_offset; })]);
    b.push(['To front', () => reorder(true)], ['To back', () => reorder(false)], ['Delete', del, 'danger']);
    p.append(btns(b));
  } else if (e.type === 'wire' || e.type === 'arrow') {
    head(e.type === 'wire' ? 'Wire' : 'Arrow', `${e.points.length} points · double-click a segment to add a corner`);
    p.append(field('Style', seg(e.style || '', STYLES, set(e, 'style'))));
    const ta = document.createElement('textarea'); ta.value = e.points.map((q) => q.join(', ')).join('\n'); ta.rows = Math.min(8, e.points.length + 1);
    ta.onchange = () => { const pts = ta.value.split('\n').map((l) => l.split(/[,\s]+/).filter(Boolean).map(Number)).filter((q) => q.length === 2 && q.every(Number.isFinite)); if (pts.length >= 2) edit(() => { e.points = pts; }); };
    ta.onkeydown = (ev) => ev.stopPropagation();
    p.append(field('Points', ta));
    p.append(btns([['Reverse', () => edit(() => { e.points.reverse(); })], ['Delete', del, 'danger']]));
  } else if (e.type === 'text') {
    head('Text', '');
    const ta = document.createElement('textarea'); ta.value = e.text; ta.rows = 3;
    ta.oninput = () => edit(() => { e.text = ta.value; }, e.id + '.text'); ta.onkeydown = (ev) => ev.stopPropagation();
    p.append(field('Text', ta));
    p.append(field('Class', sel_(e.cls || 'lbl', Object.entries(S.info.text_classes || {}).map(([k, v]) => [k, `${v} (${k})`]), set(e, 'cls'))));
    p.append(field('Anchor', seg(e.anchor || 'start', [['start', 'Start'], ['middle', 'Middle'], ['end', 'End']], set(e, 'anchor'))));
    p.append(field('Position', pair(inp(e.x, set(e, 'x'), { type: 'number', mono: true }), inp(e.y, set(e, 'y'), { type: 'number', mono: true }))));
    p.append(btns([['Delete', del, 'danger']]));
  } else if (e.type === 'rect') {
    head('Box', 'group shading, frame or block outline');
    p.append(field('Kind', sel_(e.cls || 'grp', [['grp', 'Group shading'], ['box', 'Box'], ['accbox', 'Accent box'], ['frame', 'Frame outline']], set(e, 'cls'))));
    p.append(field('Label', inp(e.label || '', set(e, 'label'), { coalesce: true })));
    p.append(field('Position', pair(inp(e.x, set(e, 'x'), { type: 'number', mono: true }), inp(e.y, set(e, 'y'), { type: 'number', mono: true }))));
    p.append(field('Size', pair(inp(e.w, set(e, 'w'), { type: 'number', mono: true }), inp(e.h, set(e, 'h'), { type: 'number', mono: true }))));
    p.append(field('Corner', inp(e.rx ?? 4, set(e, 'rx'), { type: 'number', mono: true })));
    p.append(btns([['To front', () => reorder(true)], ['To back', () => reorder(false)], ['Delete', del, 'danger']]));
  } else if (e.type === 'raw') {
    head('Raw SVG', 'markup kept verbatim (from an imported script)');
    p.append(field('Offset', pair(inp(e.x || 0, set(e, 'x'), { type: 'number', mono: true }), inp(e.y || 0, set(e, 'y'), { type: 'number', mono: true }))));
    const ta = document.createElement('textarea'); ta.value = e.svg; ta.rows = 6;
    ta.onchange = () => edit(() => { e.svg = ta.value; }); ta.onkeydown = (ev) => ev.stopPropagation();
    p.append(field('Markup', ta));
    p.append(btns([['Delete', del, 'danger']]));
  }
}
