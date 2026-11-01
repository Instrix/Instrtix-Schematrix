// The export dialog: format, area (sheet or selection, cropped), background, bitmap scale, margin.
// Vector formats and TikZ come from the server (/api/export); bitmaps are drawn in the browser from the server's
// SVG, so PNG / JPEG / WebP work even without cairosvg.
import { download, fileBase } from './files.js';
import { D, T } from './state.js';
import { closeModal, modal, toast } from './ui.js';
import { api } from './util.js';

const FORMATS = [
  ['svg', 'SVG — vector, for the web and Inkscape', 'svg'],
  ['png', 'PNG — bitmap, lossless, transparency', 'png'],
  ['jpeg', 'JPEG — bitmap, photos / slides', 'jpg'],
  ['webp', 'WebP — bitmap, small', 'webp'],
  ['pdf', 'PDF — vector, print', 'pdf'],
  ['eps', 'EPS — vector, legacy LaTeX / Word', 'eps'],
  ['tikz', 'TikZ — \\input into a LaTeX document', 'tikz'],
  ['tikz-standalone', 'LaTeX standalone (TikZ) — compiles on its own', 'tex'],
];
const BITMAP = { png: 'image/png', jpeg: 'image/jpeg', webp: 'image/webp' };
const KEY = 'schematrix-export';

function saved() { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch { return {}; } }
function remember(o) { try { localStorage.setItem(KEY, JSON.stringify(o)); } catch { /* best effort */ } }

const el = (html) => { const d = document.createElement('div'); d.innerHTML = html.trim(); return d.firstElementChild; };

export function exportDialog(onlySelection) {
  const sel = [...T().sel], o = { format: 'png', bg: 'paper', scale: 2, margin: 20, fonts: true, ...saved() };
  const area = onlySelection && sel.length ? 'selection' : 'sheet';
  const form = el(`<form class="exportdlg">
    <label>Format<select name="format">${FORMATS.map(([v, t]) => `<option value="${v}">${t}</option>`).join('')}</select></label>
    <fieldset><legend>Area</legend>
      <label><input type="radio" name="area" value="sheet"> Whole sheet</label>
      <label><input type="radio" name="area" value="selection" ${sel.length ? '' : 'disabled'}> Selection only, cropped
        <small>${sel.length ? `${sel.length} element${sel.length > 1 ? 's' : ''}` : 'nothing selected'}</small></label>
    </fieldset>
    <fieldset><legend>Background</legend>
      <label><input type="radio" name="bg" value="paper"> Theme paper</label>
      <label><input type="radio" name="bg" value="white"> White</label>
      <label><input type="radio" name="bg" value="none"> Transparent</label>
    </fieldset>
    <div class="row2">
      <label class="bmp">Scale<select name="scale">${[1, 2, 3, 4, 6, 8].map((k) => `<option value="${k}">${k}× · ${96 * k} dpi</option>`).join('')}</select></label>
      <label>Margin<input name="margin" type="number" min="0" step="5"></label>
    </div>
    <label class="svgonly"><input type="checkbox" name="fonts"> Embed fonts (portable SVG, ~200 kB)</label>
    <label>File name<input name="name"></label>
    <p class="note" hidden></p>
    <div class="btns"><button type="button" data-act="copy">Copy</button><button type="submit" class="primary">Export</button></div>
  </form>`);
  const f = form.elements;
  f.format.value = o.format; f.area.value = area; f.bg.value = o.bg; f.scale.value = o.scale; f.margin.value = o.margin;
  f.fonts.checked = o.fonts; f.name.value = fileBase() + (area === 'selection' ? '-selection' : '');
  const sync = () => {
    const fmt = f.format.value, jpeg = fmt === 'jpeg';
    form.querySelector('.bmp').hidden = !BITMAP[fmt];
    form.querySelector('.svgonly').hidden = fmt !== 'svg';
    form.querySelector('[value="none"]').disabled = jpeg;
    if (jpeg && f.bg.value === 'none') f.bg.value = 'paper';
    form.querySelector('[data-act="copy"]').hidden = !['svg', 'tikz', 'tikz-standalone'].includes(fmt);
    const note = form.querySelector('.note');
    note.hidden = !fmt.startsWith('tikz');
    note.textContent = 'TikZ uses the LaTeX document\'s font; the "formal" theme matches Times / Latin Modern best.';
  };
  form.onchange = sync; sync();
  form.onkeydown = (ev) => ev.stopPropagation();
  const opts = () => {
    const r = { format: f.format.value, bg: f.bg.value, scale: Number(f.scale.value), margin: Number(f.margin.value), fonts: f.fonts.checked };
    remember(r);
    return { ...r, ids: f.area.value === 'selection' ? sel : null, name: f.name.value.trim() || fileBase() };
  };
  form.onsubmit = async (ev) => { ev.preventDefault(); const x = opts(); closeModal(); await doExport(x); };
  form.querySelector('[data-act="copy"]').onclick = async () => {
    try { const b = await serverBlob(opts(), opts().format); await navigator.clipboard.writeText(await b.text()); toast('Copied'); closeModal(); } catch (err) { toast(err.message, true); }
  };
  modal('Export', form);
}

const BG = { paper: true, white: '#ffffff', none: false };

function serverBlob(o, format) {
  return api.blob('/api/export', { doc: D(), format, ids: o.ids, background: BG[o.bg], scale: o.scale, margin: o.margin,
    fonts: format === 'svg' ? o.fonts : true, name: o.name });
}

// bitmaps: rasterise the server's SVG (fonts embedded) in the browser
async function rasterise(o) {
  const svg = await serverBlob({ ...o, fonts: true }, 'svg');
  const url = URL.createObjectURL(svg), img = new Image();
  await new Promise((ok, bad) => { img.onload = ok; img.onerror = () => bad(new Error('could not rasterise the drawing')); img.src = url; });
  const c = document.createElement('canvas');
  c.width = Math.round(img.width * o.scale); c.height = Math.round(img.height * o.scale);
  const ctx = c.getContext('2d');
  if (o.format === 'jpeg' && o.bg === 'none') { ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, c.width, c.height); }
  ctx.scale(o.scale, o.scale); ctx.drawImage(img, 0, 0);
  URL.revokeObjectURL(url);
  const blob = await new Promise((ok) => c.toBlob(ok, BITMAP[o.format], 0.92));
  if (!blob || (o.format === 'webp' && blob.type !== 'image/webp')) throw new Error(`this browser cannot write ${o.format.toUpperCase()}`);
  return blob;
}

export async function doExport(o) {
  try {
    const ext = FORMATS.find((x) => x[0] === o.format)?.[2] || o.format;
    download(BITMAP[o.format] ? await rasterise(o) : await serverBlob(o, o.format), `${o.name}.${ext}`);
  } catch (err) { toast(err.message, true); }
}

// Copy as image / SVG: the selection (or the whole sheet) onto the clipboard, to paste into documents and chats
export async function copyImage(kind = 'png') {
  const ids = T().sel.size ? [...T().sel] : null;
  const o = { bg: 'paper', scale: 2, margin: 20, ...saved(), format: 'png', ids, name: fileBase(), fonts: true };
  if (o.bg === 'none') o.bg = 'paper';              // pasted images look broken on a transparent background
  if (!navigator.clipboard || (kind === 'png' && typeof ClipboardItem === 'undefined')) {
    toast('This window cannot write images to the clipboard; use Export instead (the browser needs https or localhost)', true);
    return;
  }
  try {
    if (kind === 'svg') {
      await navigator.clipboard.writeText(await (await serverBlob(o, 'svg')).text());
    } else {                                        // a promise keeps the user gesture alive while the image renders
      await navigator.clipboard.write([new ClipboardItem({ 'image/png': rasterise(o) })]);
    }
    toast(`Copied ${ids ? 'the selection' : 'the sheet'} as ${kind === 'svg' ? 'SVG' : 'an image'}`);
  } catch (err) { toast(`Could not copy: ${err.message}`, true); }
}

// the quick Export-menu items: last used options, whole sheet
export function quickExport(format) {
  const o = { bg: 'paper', scale: 2, margin: 20, fonts: true, ...saved() };
  doExport({ ...o, format, ids: null, name: fileBase(), fonts: format === 'svg-plain' ? false : o.fonts, ...(format === 'svg-plain' ? { format: 'svg' } : {}) });
}
