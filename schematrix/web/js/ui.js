// Modal dialogs and toasts.
import * as G from './geom.js';
import { paste } from './selection.js';
import { D, redo, S, T } from './state.js';
import { $, $$, svg } from './util.js';

// ---------------------------------------------------------------- context menu
// items: [label, command, shortcut] or null for a divider; commands run through the global [data-cmd] handler
export function contextMenu(x, y, items) {
  $$('.ctx').forEach((m) => m.remove());
  const m = document.createElement('div');
  m.className = 'drop ctx';
  m.innerHTML = items.map((it) => (it ? `<button data-cmd="${it[1]}">${it[0]}${it[2] ? `<kbd>${it[2]}</kbd>` : ''}</button>` : '<hr>')).join('');
  document.body.append(m);
  const r = m.getBoundingClientRect();
  m.style.left = Math.min(x, innerWidth - r.width - 4) + 'px';
  m.style.top = Math.min(y, innerHeight - r.height - 4) + 'px';
}

// ---------------------------------------------------------------- modal helpers
export function modal(title, body) {
  $('#modal-title').innerHTML = title;
  const mb = $('#modal-body'); mb.innerHTML = ''; mb.append(body);
  $('#modal').hidden = false;
}
export function closeModal() { $('#modal').hidden = true; svg.focus(); }
$('#modal').addEventListener('pointerdown', (ev) => { if (ev.target.id === 'modal' || ev.target.closest('[data-close]')) closeModal(); });
export function ask(title, value = '') {
  return new Promise((resolve) => {
    const d = document.createElement('div');
    d.innerHTML = `<div class="askrow"><input value="${G.esc(value)}"><button class="primary">OK</button></div>`;
    const i = $('input', d);
    const done = (v) => { closeModal(); resolve(v); };
    $('button', d).onclick = () => done(i.value.trim());
    i.onkeydown = (ev) => { ev.stopPropagation(); if (ev.key === 'Enter') done(i.value.trim()); if (ev.key === 'Escape') done(null); };
    modal(G.esc(title), d);
    const obs = new MutationObserver(() => { if ($('#modal').hidden) { obs.disconnect(); resolve(null); } });
    obs.observe($('#modal'), { attributes: true });
    setTimeout(() => { i.focus(); i.select(); }, 0);
  });
}
export function confirmBox(text, ok = 'OK') {
  return new Promise((resolve) => {
    const d = document.createElement('div');
    d.innerHTML = `<p style="margin:0 0 14px">${G.esc(text)}</p><div class="row" style="justify-content:flex-end"><button class="ghost">Cancel</button><button class="primary">${G.esc(ok)}</button></div>`;
    const [c, o] = $$('button', d);
    c.onclick = () => { closeModal(); resolve(false); };
    o.onclick = () => { closeModal(); resolve(true); };
    modal('Schematrix', d);
    setTimeout(() => o.focus(), 0);
  });
}
export let toastTimer = 0;
export function toast(msg, err = false) {
  const t = $('#toast');
  t.textContent = msg; t.className = err ? 'err' : ''; t.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.hidden = true; }, err ? 5000 : 2200);
}
// ---------------------------------------------------------------- text markup reference
// a row click inserts its example into the field that had focus before the window opened
const MARKUP = [   // [what, example, how, inserted text ('|' = where the caret goes)]
  ['Negation / active low', '~{RST}', '~{text}: overbar', '~{|}'],
  ['Subscript', 'V_{CC}', '_{text}', '_{|}'],
  ['Superscript', 'x^{2}', '^{text}', '^{|}'],
  ['Mixed', 'R_{DS(on)} = 10 m\\ohm', 'markers nest: ~{CS_{1}}', 'R_{DS(on)}'],
  ['Ohm', '4.7 k\\ohm', '\\ohm or \\Omega', '\\ohm'],
  ['Micro', '10 \\uF', '\\u or \\mu', '\\u'],
  ['Degree', '25 \\deg{}C', '\\deg; {} ends a name', '\\deg{}'],
  ['Plus-minus, times', '\\pm1 % \\times 10', '\\pm \\times \\cdot \\div', '\\pm'],
  ['Comparisons', 'V \\ge 3.3, I \\le 1 A', '\\le \\ge \\ne \\approx', '\\ge'],
  ['Greek', '\\alpha \\beta \\theta \\tau \\phi \\Delta', 'any \\name, capitalised for upper case', '\\alpha'],
  ['Others', '\\inf \\sqrt{}2 \\to \\parallel \\angle', '\\inf \\sqrt \\to \\parallel \\angle \\partial', '\\inf'],
  ['Minus sign', '\\-5 V', '\\- typographic minus', '\\-'],
  ['Literal characters', '\\~\\{ x \\} a\\_b', '\\~ \\{ \\} \\_ \\^ \\\\', '\\{'],
];
let markupTarget = null;
export function markupHelp() {
  const a = document.activeElement;
  if (a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA') && !a.closest('#modal')) markupTarget = a;
  const pv = (s) => `<svg class="sch mkpv" viewBox="-2 -14 340 20" preserveAspectRatio="xMinYMid meet">${G.textSvg(0, 0, s, 'lbl', 'start')}</svg>`;
  const d = document.createElement('div'); d.className = 'markup';
  d.innerHTML = `<p class="sub">Works in every label, value, field, net name and note. Markers only count with a brace: <code>f_c</code> stays as typed.
    Click a row to insert it${markupTarget ? ' into the field you were editing (a selection is wrapped)' : ' below'}.</p>
    <table>${MARKUP.map(([t, ex, how], i) => `<tr data-i="${i}" title="Insert"><td>${t}</td><td><code>${G.esc(ex)}</code></td><td>${pv(ex)}</td><td class="how">${G.esc(how)}</td></tr>`).join('')}</table>
    <label class="try">Try it<input value="I_{OUT} = 5 m\\A \\pm2 %, ~{OE}"></label><div class="tryout"></div>`;
  const inp = d.querySelector('.try input'), out = d.querySelector('.tryout');
  const upd = () => { out.innerHTML = pv(inp.value); };
  inp.oninput = upd; inp.onkeydown = (ev) => ev.stopPropagation(); upd();
  d.querySelectorAll('tr').forEach((tr) => {
    tr.onclick = () => {
      const ins = MARKUP[+tr.dataset.i][3], caret = ins.includes('|') ? ins.indexOf('|') : ins.length, text = ins.replace('|', '');
      const t = markupTarget && document.contains(markupTarget) ? markupTarget : inp;
      const [s0, s1] = [t.selectionStart ?? t.value.length, t.selectionEnd ?? t.value.length];
      const picked = t.value.slice(s0, s1);           // wrap a selection: ~{selected}
      t.value = t.value.slice(0, s0) + text.slice(0, caret) + picked + text.slice(caret) + t.value.slice(s1);
      const pos = s0 + caret + picked.length;
      if (t === inp) { upd(); t.focus(); t.setSelectionRange(pos, pos); return; }
      t.dispatchEvent(new Event('input', { bubbles: true })); t.dispatchEvent(new Event('change', { bubbles: true }));
      closeModal(); t.focus(); t.setSelectionRange?.(pos, pos);
    };
  });
  modal('Text markup', d);
}

export function helpDialog() {
  const k = [['V', 'Select'], ['W', 'Wire'], ['L', 'Net label'], ['T', 'Text'], ['B', 'Group box'], ['A', 'Arrow'], ['/', 'Find symbol'],
    ['R', 'Rotate 90°'], ['M', 'Mirror'], ['E', 'Accent style'], ['Del', 'Delete'], ['Arrows', 'Nudge (Shift: ×4)'],
    ['Ctrl Z / Y', 'Undo / redo'], ['Ctrl C / V / D', 'Copy / paste / duplicate'], ['Ctrl S', 'Save'], ['Ctrl Enter', 'Run script'],
    ['F', 'Fit'], ['G', 'Grid'], ['Space + drag', 'Pan'], ['Right / middle drag', 'Pan'], ['Alt + drag', 'Move a whole wire'], ['Wheel', 'Zoom'], ['Esc', 'Cancel / finish'], ['Dbl-click', 'Edit text / add wire corner']];
  const d = document.createElement('div'); d.className = 'keys';
  d.innerHTML = k.map(([a, b]) => `<kbd>${a}</kbd><span>${b}</span>`).join('') + '<kbd>F1</kbd><span>Text markup reference</span>';
  modal('Keyboard shortcuts', d);
}
