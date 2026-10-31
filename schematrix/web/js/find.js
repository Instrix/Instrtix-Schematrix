// Find and replace across the sheet: part properties (reference, value, net names, ...), fields, texts, box labels.
import * as G from './geom.js';
import { plain } from './markup.js';
import { D, edit, S, T } from './state.js';
import { modal, toast } from './ui.js';
import { applyView, bboxOf, render } from './view.js';
import { renderInspector } from './inspector.js';
import { svg } from './util.js';

// every searchable string: [element, label, get, set]
function entries() {
  const out = [];
  for (const e of D().elements) {
    if (e.locked) continue;
    if (e.type === 'comp') {
      const c = S.cat[e.sym], ref = e.props?.ref || c?.title || e.sym;
      for (const [k, v] of Object.entries(e.props || {})) {
        if (typeof v !== 'string' || !v) continue;
        out.push([e, `${ref} · ${c?.props?.[k]?.label || k}`, () => e.props[k], (x) => { e.props = { ...e.props, [k]: x }; }]);
      }
      for (const f of e.fields || []) out.push([e, `${ref} · ${f.name}`, () => f.value, (x) => { f.value = x; }]);
    } else if (e.type === 'text') out.push([e, 'Text', () => e.text, (x) => { e.text = x; }]);
    else if (e.type === 'rect' && e.label) out.push([e, 'Box label', () => e.label, (x) => { e.label = x; }]);
  }
  return out;
}

const escRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

function pattern(q, o) {
  if (!q) return null;
  const body = o.whole ? `\\b${escRe(q)}\\b` : escRe(q);
  return new RegExp(body, o.case ? 'g' : 'gi');
}

function focusOn(e) {
  T().sel = new Set([e.id]);
  const b = bboxOf(e), t = T(), k = t.view.k, r = svg.getBoundingClientRect();
  if (b) { t.view.x = r.width / 2 - ((b[0] + b[2]) / 2) * k; t.view.y = r.height / 2 - ((b[1] + b[3]) / 2) * k; t.fitPending = false; applyView(); }
  render(); renderInspector();
}

export function findDialog() {
  const d = document.createElement('div'); d.className = 'finddlg';
  d.innerHTML = `<div class="row2"><label>Find<input name="q"></label><label>Replace with<input name="r"></label></div>
    <div class="opts"><label><input type="checkbox" name="case"> Match case</label><label><input type="checkbox" name="whole"> Whole word</label></div>
    <div class="hits"></div>
    <div class="btns"><button data-a="one">Replace</button><button data-a="all" class="primary">Replace all</button></div>`;
  const $q = d.querySelector('[name=q]'), $r = d.querySelector('[name=r]'), hits = d.querySelector('.hits');
  const opts = () => ({ case: d.querySelector('[name=case]').checked, whole: d.querySelector('[name=whole]').checked });
  let found = [], cur = -1;
  const run = () => {
    const re = pattern($q.value, opts());
    found = re ? entries().filter(([, , get]) => { re.lastIndex = 0; const v = String(get()); return re.test(v) || (re.lastIndex = 0, re.test(plain(v))); }) : [];
    cur = found.length ? 0 : -1;
    hits.innerHTML = found.length ? found.map(([, label, get], i) => `<div class="hit${i === cur ? ' on' : ''}" data-i="${i}"><b>${G.esc(label)}</b><span>${G.esc(String(get()))}</span></div>`).join('')
      : `<div class="sub">${$q.value ? 'No matches' : 'Type to search labels, values, fields and texts'}</div>`;
    hits.querySelectorAll('.hit').forEach((h) => { h.onclick = () => { cur = +h.dataset.i; hits.querySelectorAll('.hit').forEach((x) => x.classList.toggle('on', x === h)); focusOn(found[cur][0]); }; });
  };
  const replace = (all) => {
    const re = pattern($q.value, opts());
    if (!re || !found.length) return;
    const list = all ? found : [found[Math.max(cur, 0)]];
    edit(() => { for (const [, , get, set] of list) { re.lastIndex = 0; set(String(get()).replace(re, $r.value)); } });
    toast(`Replaced in ${list.length} place${list.length > 1 ? 's' : ''}`);
    run();
  };
  for (const i of d.querySelectorAll('input')) { i.oninput = run; i.onchange = run; i.onkeydown = (ev) => { ev.stopPropagation(); if (ev.key === 'Enter') replace(false); }; }
  d.querySelector('[data-a=one]').onclick = () => replace(false);
  d.querySelector('[data-a=all]').onclick = () => replace(true);
  modal('Find and replace', d);
  run();
  setTimeout(() => $q.focus(), 0);
}
