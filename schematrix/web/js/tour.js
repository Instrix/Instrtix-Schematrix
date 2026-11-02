// The guided tour: a spotlight on each part of the editor with a short explanation. The first time the editor opens
// it offers the tour (the answer is remembered in this browser); Help > Tutorial starts it any time.
// ?tour=0 keeps the offer away (screenshots, tests).
import { showPane } from './commands.js';
import { renderInspector } from './inspector.js';
import { newDoc, openTab, renderTabs, S, switchTab } from './state.js';
import { closeModal, modal, toast } from './ui.js';
import { $ } from './util.js';
import { render } from './view.js';

const KEY = 'schematrix-tour-done';
const WIKI = 'https://instrix.github.io/Instrtix-Schematrix/wiki/Home.html';
const menu = (name) => [...document.querySelectorAll('.menus .menu')].find((m) => m.firstElementChild?.textContent.trim() === name);

// throw-away example sheets, removed when their step ends: one selected diode (where a part's type is chosen), or a
// small circuit with nothing selected (the document's settings and themes)
const comp = (id, sym, x, y, rot, props) => ({ id, type: 'comp', sym, x, y, rot, props });
const wire = (id, ...points) => ({ id, type: 'wire', points, style: '' });
const DEMOS = {
  diode: { sel: ['e1'], elements: [comp('e1', 'diode', 120, 80, 0, { kind: 'zener', ref: 'D1', value: '5V1' })] },
  circuit: { sel: [], elements: [
    comp('e1', 'vsrc', 40, 110, 90, { length: 60, kind: 'ac', ref: 'V1', value: 'AC 1' }),
    comp('e2', 'resistor', 110, 80, 0, { ref: 'R1', value: '10 k\\ohm' }),
    comp('e3', 'capacitor', 180, 110, 90, { ref: 'C1', value: '10 nF' }),
    comp('e4', 'ground', 40, 140, 0, {}), comp('e5', 'ground', 180, 140, 0, {}),
    comp('e6', 'flag', 250, 80, 0, { label: 'V_{OUT}', side: 'right' }),
    wire('e7', [40, 80], [80, 80]), wire('e8', [140, 80], [250, 80]),
    { id: 'e9', type: 'text', x: 30, y: 185, text: '$f_c = \\frac{1}{2\\pi RC} \\approx 1.6\\,\\mathrm{kHz}$', cls: 'note', anchor: 'start' },
  ] },
};
let demo = null;
function openDemo(kind = 'diode') {
  if (demo) return;
  const prev = S.cur, doc = newDoc(), d = DEMOS[kind];
  doc.meta.title = 'Tour example';
  doc.page = { ...doc.page, auto: true, margin: 30 };      // the page hugs the drawing, so the view zooms in on it
  doc.elements.push(...structuredClone(d.elements));
  const t = openTab(doc);
  t.sel = new Set(d.sel);
  showPane('props'); renderInspector();
  demo = { t, prev };
}
// the theme step: the example sheet runs through every theme, the card names the current one
let cycle = 0;
function cycleThemes() {
  const names = Object.keys(S.info.themes || {});
  let i = 0;
  const step = () => {
    if (!demo) return;
    demo.t.doc.theme = names[i % names.length];
    const n = document.getElementById('tour-theme');
    if (n) n.textContent = names[i % names.length];
    i++; render(); renderInspector(); place();
  };
  step();
  cycle = setInterval(step, 1600);
}
function stopCycle() { clearInterval(cycle); cycle = 0; }
function closeDemo() {
  if (!demo) return;
  const { t, prev } = demo;
  demo = null;
  S.tabs.splice(S.tabs.indexOf(t), 1);
  if (S.tabs.includes(prev)) switchTab(prev);
  else if (S.tabs.length) switchTab(S.tabs[0]);
  else openTab(newDoc());
  renderTabs();
}
const field = (label) => [...document.querySelectorAll('#pane-props .f')].find((f) => f.firstElementChild?.textContent === label);

const STEPS = [
  { title: 'Welcome to Schematrix',
    text: 'A quick tour of the editor: where the parts are, how to wire them, and how to get figures, netlists and '
      + 'LaTeX out. It takes about a minute. Use <kbd>→</kbd> / <kbd>←</kbd> or the buttons; <kbd>Esc</kbd> ends it. '
      + 'You can replay it any time from <b>Help › Tutorial</b>.' },
  { el: () => $('#palette').parentElement, side: 'right', title: 'The symbol palette',
    text: 'Every part, by category: passives, semiconductors, op-amps, logic, sources, nets, annotations and timing '
      + 'diagrams. <b>Drag</b> one onto the sheet, or <b>click</b> it and click on the sheet (repeatable). '
      + 'Press <kbd>/</kbd> to search. Right-click a tile to customise it in the symbol editor.' },
  { el: () => field('Kind') || $('#right'), side: 'left', before: () => openDemo('diode'), after: closeDemo, title: 'Choosing a type',
    text: 'Many parts come in several types, chosen in <b>Properties</b> once the part is selected. A <b>Diode</b> '
      + 'is one tile in the palette: place it, then pick its <b>Kind</b> here — Zener, Schottky, LED, TVS, photodiode, '
      + 'varactor… The same goes for gates (inputs, shape), sources (DC, AC, pulse…) and transistors. Searching the '
      + 'palette for a type (<code>zener</code>) also finds it.' },
  { el: () => $('#tools'), side: 'right', title: 'Tools',
    text: '<kbd>V</kbd> select, <kbd>W</kbd> wire, <kbd>L</kbd> net label, <kbd>T</kbd> text, <kbd>B</kbd> box, '
      + '<kbd>A</kbd> arrow. Each tool shows its keys in the hint bar at the bottom of the sheet.' },
  { el: () => $('#stage'), side: 'inside', title: 'The sheet',
    text: '<b>Wires</b> snap to pins and follow parts when you move them; drag a wire end to stretch it, a segment to '
      + 'slide it. Junction dots appear on their own. <b>Pan</b> with the right or middle mouse button, <b>zoom</b> '
      + 'with the wheel, <kbd>F</kbd> fits the page. <kbd>R</kbd> rotates, <kbd>M</kbd> mirrors. Boxes, braces and '
      + 'blocks resize by their handles. <b>Right-click</b> for align, order, auto-route and copy as image.' },
  { el: () => $('#right'), side: 'left', before: () => showPane('props'), title: 'Properties',
    text: 'Everything about the selection: reference, value, part number, the symbol\'s settings and your own fields. '
      + 'With nothing selected: the page, grid, theme and SPICE lines. Text takes <b>markup</b> — <code>10 k\\ohm</code>, '
      + '<code>V_{OUT}</code>, <code>~{RST}</code> — and <code>$\\frac{R_2}{R_1}$</code> LaTeX maths (<kbd>F1</kbd> for the list).' },
  { el: () => $('#pane-props'), side: 'left', before: () => openDemo('circuit'), after: closeDemo, title: 'The document',
    text: 'Click empty space and Properties shows the <b>document</b>: its title and description, the page — '
      + '<b>Auto size</b> crops it to the drawing, or set a size and margin —, the grid, junction dots, wire hops, '
      + 'the <b>SPICE lines</b> used for simulation, the <b>theme</b>, and a <b>page frame</b> with a title block '
      + '(A4, A3, Letter…) for printed drawings.' },
  { el: () => field('Theme') || $('#pane-props'), side: 'left', before: () => { openDemo('circuit'); cycleThemes(); },
    after: () => { stopCycle(); closeDemo(); }, title: 'Drawing styles',
    text: 'The <b>Theme</b> sets the colours, fonts and line weights of the whole sheet, in the editor and in every '
      + 'export. This example is cycling through them — now: <b id="tour-theme">instrix</b>.<br>'
      + '<b>formal</b>: Times, thin black lines, italic references — for LaTeX papers and theses. <b>technical</b>: '
      + 'Helvetica, datasheet look. <b>print-mono</b>: black on white. <b>instrix</b> (the house style), '
      + '<b>instrix-dark</b>, <b>blueprint</b> and <b>kicad</b>. The fonts ship with Schematrix, so exports look the '
      + 'same on every computer.' },
  { el: () => $('#stylepick'), side: 'below', title: 'Line styles',
    text: 'The style for new wires and parts: ink, accent colour, dashed or both. <kbd>E</kbd> toggles the accent on '
      + 'the selection.' },
  { el: () => $('#right'), side: 'left', before: () => showPane('netlist'), title: 'Netlist',
    text: 'The connectivity of the sheet: nets, pins and warnings (unconnected pins, clashing names), as SPICE, KiCad '
      + 'or JSON. SPICE decks run in ngspice as they are; netlists also import as new sheets (File menu).' },
  { el: () => $('#right'), side: 'left', before: () => showPane('script'), title: 'Python scripts',
    text: () => (S.info?.scripts
      ? 'Build schematics in Python: <code>from schematrix import Schematic</code>, place parts, wire pins, run '
        + '(<kbd>Ctrl Enter</kbd>). Results open as tabs you can keep editing by hand. The same library works in plain '
        + 'Python and Jupyter.'
      : 'Schematics can also be built in Python. Scripts run in the desktop app and on self-hosted servers, not on '
        + 'this one; the Python library itself works anywhere (pip).') },
  { el: () => menu('File'), side: 'below', before: () => showPane('props'), title: 'Files',
    text: '<kbd>Ctrl S</kbd> saves to your workspace (or downloads, on a public server); everything is also autosaved '
      + 'in this browser. Open files from your computer or drop them on the window: documents, SPICE / KiCad netlists, '
      + 'Python scripts.' },
  { el: () => menu('Export'), side: 'below', title: 'Exporting',
    text: 'SVG, PNG, PDF, EPS and <b>TikZ</b> for LaTeX, the whole sheet or only the selection, cropped, with or '
      + 'without background (<kbd>Ctrl E</kbd>). <b>Copy as image</b> (<kbd>Ctrl Shift C</kbd>) pastes straight into '
      + 'documents and chats.' },
  { el: () => menu('Help'), side: 'below', title: 'Help',
    text: 'Keyboard shortcuts (<kbd>?</kbd>), the text markup reference (<kbd>F1</kbd>) and this tour.' },
  { title: 'That\'s the tour',
    text: `Start by dragging a resistor onto the sheet, or open an example (<b>File › Open from workspace</b>). The `
      + `<a href="${WIKI}" target="_blank" rel="noopener">wiki</a> covers everything in depth: symbols, buses, `
      + 'netlists, simulation, LaTeX, scripting and deployment.' },
];

let state = null;          // { i, root, spot, card }

export function startTour() {
  endTour(false);
  const root = document.createElement('div');
  root.id = 'tour';
  root.innerHTML = '<div class="tour-spot"></div><div class="tour-card" role="dialog" aria-live="polite"></div>';
  document.body.append(root);
  state = { i: 0, root, spot: root.firstElementChild, card: root.lastElementChild };
  root.addEventListener('pointerdown', (ev) => { if (ev.target === root) ev.stopPropagation(); });
  window.addEventListener('keydown', onKey, true);
  window.addEventListener('resize', place);
  show(0);
}

export function endTour(done = true) {
  if (!state) return;
  STEPS[state.i]?.after?.();
  showPane('props');
  state.root.remove();
  window.removeEventListener('keydown', onKey, true);
  window.removeEventListener('resize', place);
  state = null;
  if (done) try { localStorage.setItem(KEY, '1'); } catch { /* storage blocked: it may show again */ }
}

// the first time the editor opens in this browser: offer the tour
export function maybeStartTour() {
  if (new URLSearchParams(location.search).get('tour') === '0') return;
  let seen = false;
  try { seen = !!localStorage.getItem(KEY); } catch { seen = true; }   // no storage: don't ask on every visit
  if (!seen) setTimeout(offerTour, 600);
}

function offerTour() {
  if (!$('#modal').hidden) return;                  // something else is open (a file dialog): ask another time
  const remember = () => { try { localStorage.setItem(KEY, '1'); } catch { /* best effort */ } };
  const d = document.createElement('div');
  d.innerHTML = '<p style="margin:0 0 6px">Would you like a quick tour of the editor? It shows where everything is — '
    + 'the parts, wiring, properties, netlists, scripts and exporting — in about a minute.</p>'
    + '<p style="margin:0 0 14px;color:var(--faint);font-size:12px">You can start it later from <b>Help › Tutorial</b>.</p>'
    + '<div class="row" style="justify-content:flex-end"><button class="ghost" data-t="no">Not now</button>'
    + '<button class="primary" data-t="yes">Take the tour</button></div>';
  d.querySelector('[data-t=no]').onclick = () => { remember(); closeModal(); toast('The tour is in the Help menu whenever you want it'); };
  d.querySelector('[data-t=yes]').onclick = () => { remember(); closeModal(); startTour(); };
  modal('Welcome to Schematrix', d);
  // closing the dialog with × or a click outside counts as "not now"
  const obs = new MutationObserver(() => { if ($('#modal').hidden) { obs.disconnect(); remember(); } });
  obs.observe($('#modal'), { attributes: true });
  setTimeout(() => d.querySelector('[data-t=yes]').focus(), 0);
}

function onKey(ev) {
  if (!state) return;
  const k = ev.key;
  if (k === 'Escape') endTour();
  else if (k === 'ArrowRight' || k === 'Enter') show(state.i + 1);
  else if (k === 'ArrowLeft') show(state.i - 1);
  else return;
  ev.preventDefault(); ev.stopPropagation();
}

function show(i) {
  if (!state) return;
  if (i >= STEPS.length) { endTour(); return; }
  if (i < 0) return;
  STEPS[state.i]?.after?.();
  state.i = i;
  const st = STEPS[i];
  st.before?.();
  const text = typeof st.text === 'function' ? st.text() : st.text;
  const last = i === STEPS.length - 1;
  state.card.innerHTML = `<div class="tour-n">${i + 1} / ${STEPS.length}</div><h3>${st.title}</h3><p>${text}</p>`
    + '<div class="tour-btns"><button class="ghost" data-t="skip">Skip tour</button><span></span>'
    + `${i ? '<button class="ghost" data-t="back">Back</button>' : ''}<button class="primary" data-t="next">${last ? 'Done' : 'Next'}</button></div>`;
  state.card.querySelector('[data-t=skip]').onclick = () => endTour();
  state.card.querySelector('[data-t=next]').onclick = () => show(state.i + 1);
  const back = state.card.querySelector('[data-t=back]');
  if (back) back.onclick = () => show(state.i - 1);
  place();
  state.card.querySelector('[data-t=next]').focus();
}

// the spotlight over the step's element, the card beside it (kept inside the window)
function place() {
  if (!state) return;
  const st = STEPS[state.i], el = st.el?.(), { spot, card } = state;
  const W = innerWidth, H = innerHeight, cw = card.offsetWidth, ch = card.offsetHeight, gap = 14;
  if (!el) {
    spot.style.display = 'none';
    state.root.classList.add('dim');
    card.style.left = `${(W - cw) / 2}px`; card.style.top = `${(H - ch) / 2}px`;
    return;
  }
  state.root.classList.remove('dim');
  const r = el.getBoundingClientRect(), pad = 6;
  Object.assign(spot.style, { display: 'block', left: `${r.left - pad}px`, top: `${r.top - pad}px`,
    width: `${r.width + 2 * pad}px`, height: `${r.height + 2 * pad}px` });
  let x, y;
  if (st.side === 'right') { x = r.right + gap; y = r.top + 40; }
  else if (st.side === 'left') { x = r.left - cw - gap; y = r.top + 40; }
  else if (st.side === 'below') { x = r.left; y = r.bottom + gap; }
  else { x = r.left + (r.width - cw) / 2; y = r.top + (r.height - ch) / 2; }    // inside: centred on it
  card.style.left = `${Math.max(12, Math.min(x, W - cw - 12))}px`;
  card.style.top = `${Math.max(12, Math.min(y, H - ch - 12))}px`;
}
