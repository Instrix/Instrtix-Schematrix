// Schematrix editor entry point. Geometry comes from the Python symbol library over /api/geometry; everything else is local.
import * as G from './geom.js';
import { cmd } from './commands.js';
import { openWorkspaceFile } from './files.js';
import { buildPalette } from './palette.js';
import { refreshScripts, SAMPLE } from './panes.js';
import { geoKey, newDoc, openTab, restore, S } from './state.js';
import { setTool } from './tools.js';
import { FULL_ONLY, fullOnlyHtml, toast } from './ui.js';
import { $, api } from './util.js';
import { render, scopeCss } from './view.js';

// ---------------------------------------------------------------- boot
export async function boot() {
  try {
    [S.info, S.catList] = await Promise.all([api.get('/api/info'), api.get('/api/symbols')]);
  } catch (err) {
    document.body.innerHTML = `<p style="padding:40px;font-family:sans-serif">Schematrix could not reach its server: ${G.esc(err.message)}</p>`;
    return;
  }
  for (const e of S.catList) {
    S.cat[e.name] = e; S.geo.set(geoKey(e.name, {}), e.geometry);
    for (const p of e.presets || []) S.geo.set(geoKey(e.name, p.props), p.geometry);
  }
  const pst = document.createElement('style');           // palette thumbnails always use the light theme
  pst.textContent = scopeCss(S.info.css.instrix, '.schp');
  document.head.append(pst);
  buildPalette();
  $('#code').value = localStorage.getItem('schematrix-script') || SAMPLE;
  if (!S.info.scripts) { $('#runscript').disabled = true; $('#runscript').title = 'Script execution is disabled on this server'; }
  if (S.info.public) {                       // anonymous public server: say what it does not offer
    document.body.classList.add('public');
    $('#pane-script').insertAdjacentHTML('afterbegin', `<div class="fullonly">${fullOnlyHtml('Running Python scripts')}</div>`);
    $('#runscript').disabled = $('#savescript').disabled = true;
    let seen = false;
    try { seen = localStorage.getItem('schematrix-public-banner') === '1'; } catch { /* storage blocked */ }
    if (!seen) {
      const b = document.createElement('div');
      b.id = 'banner';
      b.innerHTML = `<span>Public demo: ${fullOnlyHtml(FULL_ONLY)}</span><button class="x" title="Dismiss">×</button>`;
      b.querySelector('button').onclick = () => {
        b.remove(); document.body.classList.remove('banner');
        try { localStorage.setItem('schematrix-public-banner', '1'); } catch { /* storage blocked */ }
      };
      document.body.prepend(b); document.body.classList.add('banner');
    }
    try {
      if (!localStorage.getItem('schematrix-public-notice')) {
        toast('Public server: nothing is stored here. Your sheets are kept in this browser; File > Save downloads them.');
        localStorage.setItem('schematrix-public-notice', '1');
      }
    } catch { /* storage blocked */ }
  }
  if (!restore()) openTab(newDoc());
  setTool('select');
  refreshScripts();
  const q = new URLSearchParams(location.search).get('open');
  if (q) openWorkspaceFile(q);
  window.schematrix = { S, api, cmd, openTab, render };   // for debugging from the console
}
boot();
