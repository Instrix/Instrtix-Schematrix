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
export function helpDialog() {
  const k = [['V', 'Select'], ['W', 'Wire'], ['L', 'Net label'], ['T', 'Text'], ['B', 'Group box'], ['A', 'Arrow'], ['/', 'Find symbol'],
    ['R', 'Rotate 90°'], ['M', 'Mirror'], ['E', 'Accent style'], ['Del', 'Delete'], ['Arrows', 'Nudge (Shift: ×4)'],
    ['Ctrl Z / Y', 'Undo / redo'], ['Ctrl C / V / D', 'Copy / paste / duplicate'], ['Ctrl S', 'Save'], ['Ctrl Enter', 'Run script'],
    ['F', 'Fit'], ['G', 'Grid'], ['Space + drag', 'Pan'], ['Right / middle drag', 'Pan'], ['Alt + drag', 'Move a whole wire'], ['Wheel', 'Zoom'], ['Esc', 'Cancel / finish'], ['Dbl-click', 'Edit text / add wire corner']];
  const d = document.createElement('div'); d.className = 'keys';
  d.innerHTML = k.map(([a, b]) => `<kbd>${a}</kbd><span>${b}</span>`).join('');
  modal('Keyboard shortcuts', d);
}
