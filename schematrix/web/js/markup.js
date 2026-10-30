// Text markup: the JS twin of schematrix/markup.py (keep the two in step).
//   ~{RST} overbar · R_{DS(on)} subscript · x^{2} superscript · \ohm \mu \deg \pm \times \alpha … named symbols

const GREEK = { alpha: 'α', beta: 'β', gamma: 'γ', delta: 'δ', epsilon: 'ε', zeta: 'ζ', eta: 'η', theta: 'θ', iota: 'ι',
  kappa: 'κ', lambda: 'λ', mu: 'µ', nu: 'ν', xi: 'ξ', pi: 'π', rho: 'ρ', sigma: 'σ', tau: 'τ', upsilon: 'υ', phi: 'φ',
  chi: 'χ', psi: 'ψ', omega: 'ω', Gamma: 'Γ', Delta: 'Δ', Theta: 'Θ', Lambda: 'Λ', Xi: 'Ξ', Pi: 'Π', Sigma: 'Σ',
  Phi: 'Φ', Psi: 'Ψ', Omega: 'Ω' };
export const SYMBOLS = { ...GREEK, ohm: 'Ω', Ohm: 'Ω', u: 'µ', micro: 'µ', deg: '°', pm: '±', times: '×', cdot: '·',
  div: '÷', le: '≤', ge: '≥', ne: '≠', approx: '≈', inf: '∞', infty: '∞', sqrt: '√', to: '→', rarrow: '→', larrow: '←',
  uarrow: '↑', darrow: '↓', parallel: '∥', angle: '∠', propto: '∝', partial: '∂', int: '∫', sum: 'Σ', prod: 'Π',
  degree: '°', permil: '‰', Re: 'ℜ', Im: 'ℑ', hbar: 'ℏ', bullet: '•', dots: '…', '-': '−' };
const ESCAPES = { '\\': '\\', '{': '{', '}': '}', '~': '~', _: '_', '^': '^', $: '$' };
const FLAGS = { '~': 'over', _: 'sub', '^': 'sup' };

function close(s, i) {
  let depth = 0;
  for (let j = i; j < s.length; j++) {
    if (s[j] === '\\') continue;
    if (s[j] === '{' && (j === 0 || s[j - 1] !== '\\')) depth++;
    else if (s[j] === '}' && s[j - 1] !== '\\') { depth--; if (depth === 0) return j; }
  }
  return -1;
}

const key = (f) => [...f].sort().join(',');

// -> [[text, Set of 'over' | 'sub' | 'sup']], adjacent runs with the same flags merged
export function parse(s, flags = new Set()) {
  s = String(s ?? '');
  const out = [];
  let buf = '';
  const flush = () => { if (buf) { out.push([buf, flags]); buf = ''; } };
  let i = 0;
  while (i < s.length) {
    const c = s[i];
    if (FLAGS[c] && s[i + 1] === '{') {
      const j = close(s, i + 1);
      if (j > 0) { flush(); out.push(...parse(s.slice(i + 2, j), new Set([...flags, FLAGS[c]]))); i = j + 1; continue; }
    }
    if (c === '\\' && i + 1 < s.length) {
      const nxt = s[i + 1];
      if (nxt in ESCAPES) { buf += ESCAPES[nxt]; i += 2; continue; }
      if (nxt === '-') { buf += '−'; i += 2; continue; }
      const m = /^[A-Za-z]+/.exec(s.slice(i + 1));
      let name = null;
      if (m) for (let k = m[0].length; k > 0; k--) if (m[0].slice(0, k) in SYMBOLS) { name = m[0].slice(0, k); break; }
      if (name) { buf += SYMBOLS[name]; i += 1 + name.length; if (s.slice(i, i + 2) === '{}') i += 2; continue; }
    }
    buf += c; i++;
  }
  flush();
  const merged = [];
  for (const [t, f] of out) {
    if (merged.length && key(merged.at(-1)[1]) === key(f)) merged.at(-1)[0] += t; else merged.push([t, f]);
  }
  return merged;
}

export const plain = (s) => parse(s).map(([t]) => t).join('');
export const widthChars = (s) => parse(s).reduce((n, [t, f]) => n + t.length * (f.has('sub') || f.has('sup') ? 0.72 : 1), 0);

const r2 = (v) => Math.round(v * 100) / 100;

export function svgInner(s, fs, esc) {
  const runs = parse(s);
  if (!runs.length) return '';
  if (runs.length === 1 && !runs[0][1].size) return esc(runs[0][0]);
  let base = 0;
  return runs.map(([t, f]) => {
    const off = f.has('sub') ? 0.32 * fs : f.has('sup') ? -0.38 * fs : 0;
    const dy = r2(off - base); base = off;
    const st = [...(f.has('sub') || f.has('sup') ? [`font-size:${r2(fs * 0.72)}px`] : []), ...(f.has('over') ? ['text-decoration:overline'] : [])];
    const attrs = (dy ? ` dy="${dy}"` : '') + (st.length ? ` style="${st.join(';')}"` : '');
    return attrs ? `<tspan${attrs}>${esc(t)}</tspan>` : esc(t);
  }).join('');
}
