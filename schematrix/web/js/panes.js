// The netlist and script side panes.
import * as G from './geom.js';
import { inp, renderInspector } from './inspector.js';
import { D, openTab, persistSoon, pinsOf, renderTabs, S, switchTab } from './state.js';
import { toast } from './ui.js';
import { $, $$, api } from './util.js';
import { render, renderOverlay } from './view.js';

// ---------------------------------------------------------------- netlist pane
export async function refreshNetlist() {
  try {
    const r = await api.post('/api/netlist', { doc: D() });
    $('#spice').textContent = r.spice;
    $('#netwarn').innerHTML = r.warnings.map((w) => `<div class="warn">${G.esc(w)}</div>`).join('');
    const box = $('#netlist');
    box.innerHTML = '';
    const pinMap = new Map(r.pins.map(([id, pin, net]) => [`${id}.${pin}`, net]));
    for (const [net, members] of Object.entries(r.nets).sort(([a], [b]) => a.localeCompare(b, undefined, { numeric: true }))) {
      const d = document.createElement('div');
      d.className = 'net';
      d.innerHTML = `<b>${G.esc(net)}</b><span>${members.map(([ref, pin]) => `${G.esc(ref)}.${G.esc(pin)}`).join('  ')}</span>`;
      d.onclick = () => {
        $$('.net').forEach((n) => n.classList.remove('on')); d.classList.add('on');
        S.netHL = [];
        for (const e of D().elements) if (e.type === 'comp') for (const [pin, q] of Object.entries(pinsOf(e))) if (pinMap.get(`${e.id}.${pin}`) === net) S.netHL.push(q);
        renderOverlay();
      };
      box.append(d);
    }
  } catch (err) { toast(err.message, true); }
}

// ---------------------------------------------------------------- script pane
export const SAMPLE = `# Build schematics in Python. Ctrl+Enter runs this; every schematic you
# create (or pass to show()) opens as a tab. Pins are reached as part['pin'].
from schematrix import Schematic

s = Schematic('RC filter and buffer', description='First-order low-pass into a follower')
vin = s.flag((60, 120), 'VIN', side='left')
r1 = s.resistor((130, 120), value='1 kΩ')
c1 = s.capacitor(anchor='1', at=(200, 120), rot=90, value='10 nF', part='C0G')
s.gnd(c1['2'])
u1 = s.opamp(anchor='inp', at=(280, 120), top='+', part='OPA210')
s.wire(vin['p'], r1['1'])
s.wire(r1['2'], u1['inp'])                     # passes over C1's pin: a junction dot appears

out = u1['out']
fb = s.wire(out, out.offset(20, 0), out.offset(20, 45), u1['inm'].offset(-14, 45 - 15), u1['inm'].offset(-14, 0), u1['inm'])
s.wire(out.offset(20, 0), out.offset(50, 0))
s.flag(out.offset(50, 0), 'VOUT', side='right')
s.note(60, 230, 'f_c = 1 / (2π · 1 kΩ · 10 nF) ≈ 15.9 kHz')

# a resistor ladder, drawn in a loop
lad = Schematic('Ladder')
top = lad.terminal((60, 40), 'I+')
prev = top['p']
for k, (r, tap) in enumerate([('10 mΩ', 't1'), ('90 mΩ', 't2'), ('900 mΩ', 't3')], 1):
    rk = lad.resistor(anchor='1', at=prev, rot=90, value=r, length=80, style='acc' if k == 3 else '')
    prev = rk['2']
    lad.wire(prev, prev.offset(60, 0))
    lad.flag(prev.offset(60, 0), tap.upper(), side='right')
print(lad.spice())
`;
export async function runScript() {
  if ($('#runscript').disabled) return;     // scripts are off on this server (the pane says why)
  const out = $('#runout');
  out.innerHTML = '<pre>running…</pre>';
  try {
    const r = await api.post('/api/run', { code: $('#code').value, filename: $('#scriptfile').value || 'script.py' });
    showRun(r);
  } catch (err) { out.innerHTML = `<pre class="err">${G.esc(err.message)}</pre>`; }
}
export function showRun(r, legacy = false) {
  const out = $('#runout');
  out.innerHTML = '';
  if (r.stdout) out.insertAdjacentHTML('beforeend', `<pre>${G.esc(r.stdout)}</pre>`);
  if (!r.ok) { out.insertAdjacentHTML('beforeend', `<pre class="err">${G.esc(r.traceback || r.error)}</pre>`); return; }
  if (!r.docs.length) { out.insertAdjacentHTML('beforeend', '<pre>no schematics were created</pre>'); return; }
  for (const { name, doc } of r.docs) {
    const existing = S.tabs.find((t) => t.fromScript === name && !t.path);
    if (existing) { pushUndoFor(existing); existing.doc = doc; existing.dirty = true; if (existing === S.cur) { render(); renderInspector(); } }
    else { const t = openTab(doc, null, false); t.fromScript = name; t.dirty = true; }
  }
  const first = S.tabs.find((t) => t.fromScript === r.docs[0].name && !t.path);
  if (first) switchTab(first);
  toast(`${r.docs.length} schematic${r.docs.length > 1 ? 's' : ''} ${legacy ? 'imported' : 'from the script'}`);
  renderTabs(); persistSoon();
}
export function pushUndoFor(t) { t.undo.push(JSON.stringify(t.doc)); t.redo = []; }
export async function refreshScripts(select) {
  try {
    const files = (await api.get('/api/files')).filter((f) => f.path.endsWith('.py'));
    const s = $('#scriptfile'), cur = select || s.value;
    s.innerHTML = '<option value="">(unsaved script)</option>' + files.map((f) => `<option>${G.esc(f.path)}</option>`).join('');
    s.value = files.some((f) => f.path === cur) ? cur : '';
  } catch { /* offline */ }
}
