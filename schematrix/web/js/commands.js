// Commands, menus, keyboard shortcuts and resizable panels.
import { exportDialog, quickExport } from './exporter.js';
import { exportAs, exportNetlist, filesDialog, importFile, save } from './files.js';
import { renderInspector } from './inspector.js';
import { buildPalette } from './palette.js';
import { refreshNetlist, refreshScripts, runScript } from './panes.js';
import { copySel, del, nudge, paste, reorder, step, toggleAccent, transformSel } from './selection.js';
import { D, edit, newDoc, openTab, persist, redo, S, T, undo } from './state.js';
import { finishDraft, setTool } from './tools.js';
import { ask, closeModal, helpDialog, modal, toast } from './ui.js';
import { $, $$, api, svg } from './util.js';
import { fit, render, renderOverlay, zoomAt } from './view.js';

// ---------------------------------------------------------------- commands, menus, keys
export function showPane(name) {
  $$('.ptabs button').forEach((b) => b.classList.toggle('on', b.dataset.pane === name));
  $$('.pane').forEach((p) => { p.hidden = p.id !== 'pane-' + name; });
  if (name === 'netlist') refreshNetlist(); else { S.netHL = null; renderOverlay(); }
}
export function setStyle(st) { S.style = st; $$('#stylepick button').forEach((b) => b.classList.toggle('on', b.dataset.style === st)); }
export function closeMenus() { $$('.menu').forEach((m) => m.classList.remove('open')); $$('.ctx').forEach((m) => m.remove()); }

export const COMMANDS = {
  new: () => openTab(newDoc()), open: filesDialog, upload: () => { $('#fileinput').dataset.legacy = ''; $('#fileinput').click(); },
  'import-legacy': () => { $('#fileinput').dataset.legacy = '1'; $('#fileinput').click(); },
  save: () => save(false), saveas: () => save(true), undo, redo,
  cut: () => { if (copySel()) del(); }, copy: copySel, paste, duplicate: () => { if (copySel()) paste(); }, delete: del,
  selectall: () => { T().sel = new Set(D().elements.map((e) => e.id)); render(); renderInspector(); },
  rotate: () => transformSel('rot'), mirror: () => transformSel('mir'), accent: toggleAccent, front: () => reorder(true), back: () => reorder(false),
  forward: () => step(1), backward: () => step(-1),
  fit, zoomin: () => zoomAt(1.25), zoomout: () => zoomAt(0.8), zoom100: () => zoomAt(1 / T().view.k),
  grid: () => { S.grid = !S.grid; render(); }, help: helpDialog,
  junctions: () => edit((d) => { d.page.junctions = d.page.junctions === false; }),
  hops: () => edit((d) => { d.page.hops = !d.page.hops; }),
  export: () => exportDialog(false), 'export-selection': () => exportDialog(true),
  'export-svg': () => quickExport('svg'), 'export-svg-plain': () => quickExport('svg-plain'), 'export-png': () => quickExport('png'),
  'export-jpeg': () => quickExport('jpeg'), 'export-pdf': () => quickExport('pdf'), 'export-eps': () => quickExport('eps'),
  'export-tikz': () => quickExport('tikz'), 'export-spice': () => exportNetlist('spice'), 'export-kicad': () => exportNetlist('kicad'), 'export-netjson': () => exportNetlist('json'),
  'import-netlist': () => { $('#fileinput').dataset.legacy = ''; $('#fileinput').click(); }, 'export-json': () => exportAs('json'),
  'copy-svg': async () => { try { const b = await api.blob('/api/render?format=svg&fonts=false', { doc: D() }); await navigator.clipboard.writeText(await b.text()); toast('SVG copied'); } catch (err) { toast(err.message, true); } },
};
export function cmd(name) { closeMenus(); COMMANDS[name]?.(); }

document.addEventListener('click', (ev) => {
  const c = ev.target.closest('[data-cmd]');
  if (c) { cmd(c.dataset.cmd); return; }
  const m = ev.target.closest('.menu > button');
  if (m) { const open = m.parentElement.classList.contains('open'); closeMenus(); if (!open) m.parentElement.classList.add('open'); return; }
  if (!ev.target.closest('.menu')) closeMenus();
});
$$('.menu > button').forEach((b) => b.addEventListener('pointerenter', () => { if ($('.menu.open') && !b.parentElement.classList.contains('open')) { closeMenus(); b.parentElement.classList.add('open'); } }));
$$('#tools button').forEach((b) => { b.onclick = () => setTool(b.dataset.tool); });
$$('#stylepick button').forEach((b) => { b.onclick = () => setStyle(b.dataset.style); });
$$('.ptabs button').forEach((b) => { b.onclick = () => showPane(b.dataset.pane); });
$('#symsearch').addEventListener('input', (ev) => buildPalette(ev.target.value));
$('#symsearch').addEventListener('keydown', (ev) => {
  ev.stopPropagation();
  if (ev.key === 'Enter') { const first = $('#palette .sym'); first?.click(); }
  if (ev.key === 'Escape') { ev.target.value = ''; buildPalette(); svg.focus(); }
});
$('#fileinput').addEventListener('change', (ev) => { const f = ev.target.files[0]; if (f) importFile(f, ev.target.dataset.legacy === '1'); ev.target.value = ''; });
$('#netrefresh').onclick = refreshNetlist;
$('#netdl').onclick = () => exportNetlist($('#netfmt').value);
$('#runscript').onclick = runScript;
$('#savescript').onclick = async () => {
  const cur = $('#scriptfile').value;
  const name = cur || (await ask('Save script as', 'script.py'));
  if (!name) return;
  const path = name.endsWith('.py') ? name : name + '.py';
  try { await api.put('/api/files/' + encodeURI(path), $('#code').value); await refreshScripts(path); toast('Saved ' + path); } catch (err) { toast(err.message, true); }
};
$('#scriptfile').onchange = async (ev) => { if (ev.target.value) { const r = await fetch('/api/files/' + encodeURI(ev.target.value)); $('#code').value = await r.text(); } };
$('#code').addEventListener('keydown', (ev) => {
  ev.stopPropagation();
  const ta = ev.target;
  if (ev.key === 'Enter' && (ev.ctrlKey || ev.metaKey)) { ev.preventDefault(); runScript(); return; }
  if (ev.key === 'Tab') {
    ev.preventDefault();
    const { selectionStart: a, selectionEnd: b, value } = ta;
    ta.value = value.slice(0, a) + '    ' + value.slice(b); ta.selectionStart = ta.selectionEnd = a + 4;
  }
  if (ev.key === 's' && (ev.ctrlKey || ev.metaKey)) { ev.preventDefault(); $('#savescript').click(); }
});
$('#code').addEventListener('input', () => { try { localStorage.setItem('schematrix-script', $('#code').value); } catch { /* best effort */ } });
document.addEventListener('dragover', (ev) => ev.preventDefault());
document.addEventListener('drop', (ev) => { ev.preventDefault(); for (const f of ev.dataTransfer.files) importFile(f); });
window.addEventListener('beforeunload', (ev) => { persist(); if (S.tabs.some((t) => t.dirty && t.path)) { ev.preventDefault(); } });

document.addEventListener('keydown', (ev) => {
  if (!$('#modal').hidden) { if (ev.key === 'Escape') closeModal(); return; }
  const tag = document.activeElement?.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
  const mod = ev.ctrlKey || ev.metaKey, k = ev.key;
  if (mod) {
    const map = { z: ev.shiftKey ? 'redo' : 'undo', y: 'redo', c: 'copy', x: 'cut', v: 'paste', d: 'duplicate', a: 'selectall', s: ev.shiftKey ? 'saveas' : 'save', e: 'export', o: 'open', n: 'new', ']': 'front', '[': 'back' };
    const c = map[k.toLowerCase()];
    if (c) { ev.preventDefault(); cmd(c); }
    return;
  }
  if (k === ' ') { S.space = true; svg.classList.add('panning'); ev.preventDefault(); return; }
  if (k === 'Escape') {
    if (S.draft) finishDraft(); else if (S.tool !== 'select') setTool('select'); else { T().sel.clear(); render(); renderInspector(); }
    return;
  }
  if (k === 'Enter' && S.draft) { finishDraft(); return; }
  if (k === 'Backspace' && S.draft) { if (S.draft.pts.length > 1) S.draft.pts.pop(); else S.draft = null; renderOverlay(); ev.preventDefault(); return; }
  if (k === 'Delete' || k === 'Backspace') { del(); ev.preventDefault(); return; }
  if (k === 'PageUp' || k === 'PageDown') { cmd(k === 'PageUp' ? 'forward' : 'backward'); ev.preventDefault(); return; }
  if (k.startsWith('Arrow')) {
    const g = (D().page.grid || 5) * (ev.shiftKey ? 4 : 1);
    nudge(k === 'ArrowLeft' ? -g : k === 'ArrowRight' ? g : 0, k === 'ArrowUp' ? -g : k === 'ArrowDown' ? g : 0);
    ev.preventDefault(); return;
  }
  const keys = { v: () => setTool('select'), w: () => setTool('wire'), t: () => setTool('text'), b: () => setTool('rect'), a: () => setTool('arrow'),
    l: () => setTool('flag'), r: () => transformSel('rot'), m: () => transformSel('mir'), e: toggleAccent, f: fit, g: () => cmd('grid'),
    '+': () => zoomAt(1.25), '=': () => zoomAt(1.25), '-': () => zoomAt(0.8), '1': () => cmd('zoom100'), '?': helpDialog,
    '/': () => { if (S.draft) { S.wireMode = S.wireMode === 'hv' ? 'vh' : 'hv'; renderOverlay(); } else { ev.preventDefault(); $('#symsearch').focus(); } } };
  const fn = keys[k] || keys[k.toLowerCase()];
  if (fn) { fn(); ev.preventDefault(); }
});
document.addEventListener('keyup', (ev) => { if (ev.key === ' ') { S.space = false; svg.classList.remove('panning'); } });

// ---------------------------------------------------------------- resizable side panels
for (const [id, side] of [['#left', 'l'], ['#right', 'r']]) {
  const h = document.createElement('div');
  h.className = 'splitter ' + side;
  $(id).append(h);
  h.addEventListener('pointerdown', (ev) => {
    h.setPointerCapture(ev.pointerId);
    const x0 = ev.clientX, w0 = $(id).getBoundingClientRect().width;
    const mv = (e) => {
      const w = Math.max(180, Math.min(760, w0 + (side === 'l' ? e.clientX - x0 : x0 - e.clientX)));
      document.documentElement.style.setProperty(side === 'l' ? '--left-w' : '--right-w', w + 'px');
    };
    const up = () => { h.removeEventListener('pointermove', mv); h.removeEventListener('pointerup', up); };
    h.addEventListener('pointermove', mv); h.addEventListener('pointerup', up);
  });
}
