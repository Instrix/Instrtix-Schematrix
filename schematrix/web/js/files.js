// Workspace files, saving, export and import.
import * as G from './geom.js';
import { showPane } from './commands.js';
import { refreshScripts, showRun } from './panes.js';
import { D, openTab, persist, persistSoon, renderTabs, S, switchTab, T, tabTitle } from './state.js';
import { ask, closeModal, confirmBox, modal, toast } from './ui.js';
import { $, api, svg } from './util.js';
import { render } from './view.js';

// ---------------------------------------------------------------- files
export async function filesDialog() {
  let files;
  try { files = await api.get('/api/files'); } catch (err) { toast(err.message, true); return; }
  const body = document.createElement('div');
  body.className = 'files';
  if (!files.length) body.innerHTML = '<div class="sub">The workspace is empty. Saved schematics and scripts appear here.</div>';
  for (const f of files) {
    const d = document.createElement('div');
    d.className = 'file';
    const ext = f.path.split('.').pop();
    d.innerHTML = `<span class="ic">${ext.toUpperCase()}</span><span>${G.esc(f.path)}</span><span class="m">${f.modified.replace('T', ' ').slice(0, 16)}</span><button title="Delete">✕</button>`;
    d.onclick = async (ev) => {
      if (ev.target.tagName === 'BUTTON') {
        if (await confirmBox(`Delete ${f.path} from the workspace?`, 'Delete')) { await api.del('/api/files/' + encodeURI(f.path)); filesDialog(); }
        return;
      }
      closeModal();
      openWorkspaceFile(f.path);
    };
    body.append(d);
  }
  modal(`Workspace <small style="font-weight:400;color:var(--faint);font-family:var(--mono);font-size:11px">${G.esc(S.info.workspace || '')}</small>`, body);
}
export async function openWorkspaceFile(path) {
  const r = await fetch('/api/files/' + encodeURI(path));
  if (!r.ok) { toast('could not open ' + path, true); return; }
  if (path.endsWith('.json')) {
    const open = S.tabs.find((t) => t.path === path);
    if (open) { switchTab(open); return; }
    const doc = await r.json();
    openTab(doc, path);
  } else if (path.endsWith('.py')) {
    $('#code').value = await r.text();
    await refreshScripts(path);
    showPane('script');
  } else if (path.endsWith('.svg')) window.open('/api/files/' + encodeURI(path), '_blank');
  persistSoon();
}
export async function save(as = false) {
  const t = T();
  let path = t.path;
  if (as || !path) {
    const name = await ask('Save as (in the workspace)', path || (G.esc(tabTitle(t)).replace(/[^\w\- ]+/g, '').trim().replace(/\s+/g, '-').toLowerCase() || 'schematic') + '.json');
    if (!name) return;
    path = name.endsWith('.json') ? name : name + '.json';
  }
  try {
    await api.put('/api/files/' + encodeURI(path), JSON.stringify(t.doc, null, 1));
    t.path = path; t.dirty = false; t.fromScript = null;
    renderTabs(); persist(); toast('Saved ' + path);
  } catch (err) { toast(err.message, true); }
}

export function download(blob, name) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
export const fileBase = () => (tabTitle(T()).replace(/[^\w\-]+/g, '-').replace(/^-|-$/g, '') || 'schematic');
export async function exportAs(fmt) {
  try {
    if (fmt === 'json') return download(new Blob([JSON.stringify(D(), null, 1)], { type: 'application/json' }), fileBase() + '.json');
    if (fmt === 'png' && !S.info.pdf) return exportPngClient();
    const q = fmt === 'svg-plain' ? 'format=svg&fonts=false' : `format=${fmt}`;
    const b = await api.blob('/api/render?' + q, { doc: D() });
    download(b, fileBase() + '.' + (fmt === 'svg-plain' ? 'svg' : fmt === 'spice' ? 'cir' : fmt));
  } catch (err) { toast(err.message, true); }
}
export async function exportPngClient() {
  const b = await api.blob('/api/render?format=svg&fonts=true', { doc: D() });
  const url = URL.createObjectURL(b), img = new Image();
  img.onload = () => {
    const c = document.createElement('canvas'); c.width = img.width * 2; c.height = img.height * 2;
    const ctx = c.getContext('2d'); ctx.scale(2, 2); ctx.drawImage(img, 0, 0);
    c.toBlob((png) => download(png, fileBase() + '.png'));
    URL.revokeObjectURL(url);
  };
  img.src = url;
}

export async function exportNetlist(fmt) {
  try {
    const b = await api.blob('/api/netlist/export?format=' + fmt, { doc: D() });
    const ext = (S.info.netlist_formats || []).find((f) => f.name === fmt)?.default_ext || '.net';
    download(b, fileBase() + ext);
  } catch (err) { toast(err.message, true); }
}

const NETLIST_EXT = /\.(cir|sp|spi|spice|ckt|net|netlist)$/i;

// a netlist file (SPICE, KiCad .net, Schematrix netlist JSON) opens as a new sheet with every net labelled
export async function importNetlist(text, filename) {
  try {
    const r = await api.post('/api/netlist/import', { text, filename });
    openTab(r.doc);
    toast(`Imported ${r.format} netlist: ${r.doc.elements.filter((e) => e.type === 'comp' && S.cat[e.sym]?.is_part).length} parts`
      + (r.warnings.length ? ` · ${r.warnings.length} warning(s): ${r.warnings[0]}` : ''), r.warnings.length > 0);
  } catch (err) { toast(err.message, true); }
}

export async function importFile(file, forceLegacy) {
  const text = await file.text();
  if (NETLIST_EXT.test(file.name)) return importNetlist(text, file.name);
  if (file.name.endsWith('.json')) {
    try {
      const doc = JSON.parse(text);
      if (doc.format === 'schematrix-netlist') return importNetlist(text, file.name);
      if (!doc.elements) throw new Error('not a Schematrix document');
      openTab(doc);
    } catch (err) { toast(err.message, true); }
    return;
  }
  if (file.name.endsWith('.py')) {
    const legacy = forceLegacy || (/class\s+S\b/.test(text) && /def\s+svg\(/.test(text));
    if (legacy) {
      toast('Importing figures from ' + file.name + '…');
      try { showRun(await api.post('/api/import-legacy', { code: text, filename: file.name }), true); showPane('script'); } catch (err) { toast(err.message, true); }
    } else { $('#code').value = text; showPane('script'); $('#scriptfile').value = ''; }
  }
}
