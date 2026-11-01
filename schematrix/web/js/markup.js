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

// $...$ LaTeX maths -> this markup, for drawing (fractions become a/b); TikZ export gets the LaTeX itself
const MATH_TEXT = new Set(['mathrm', 'text', 'mathit', 'mathbf', 'mathsf', 'mathtt', 'textrm', 'textit', 'textbf', 'mbox',
  'operatorname', 'mathcal', 'boldsymbol']);
const MATH_SPACE = { ',': ' ', ';': ' ', ':': ' ', '!': '', ' ': ' ', quad: '  ', qquad: '   ' };
const MATH_DROP = new Set(['left', 'right', 'big', 'Big', 'bigl', 'bigr', 'Bigl', 'Bigr', 'displaystyle', 'textstyle', 'limits']);
const MATH_SYMBOLS = { ldots: '…', cdots: '⋯', leq: '≤', geq: '≥', neq: '≠', rightarrow: '→', leftarrow: '←', varphi: 'φ',
  varepsilon: 'ε', ell: 'ℓ', sim: '∼', mp: '∓', circ: '°', prime: '′' };

function mathArg(t, i) {
  while (i < t.length && t[i] === ' ') i++;
  if (i >= t.length) return ['', i];
  if (t[i] === '{') {
    let depth = 0;
    for (let j = i; j < t.length; j++) {
      if (t[j] === '\\') continue;
      if (t[j] === '{' && t[j - 1] !== '\\') depth++;
      else if (t[j] === '}' && t[j - 1] !== '\\') { depth--; if (depth === 0) return [t.slice(i + 1, j), j + 1]; }
    }
    return [t.slice(i + 1), t.length];
  }
  if (t[i] === '\\') { const m = /^\\([A-Za-z]+|.)/.exec(t.slice(i)); return [m[0], i + m[0].length]; }
  return [t[i], i + 1];
}
const paren = (s) => ((s.match(/(?:\d+(?:\.\d+)?|\\[A-Za-z]+\{\}|[^\s_^~{}])(?:[_^]\{[^{}]*\})*/g) || []).length > 1
  && !(s.startsWith('(') && s.endsWith(')')) ? `(${s})` : s);

const MATH_REL = { '=': '=', '<': '<', '>': '>', approx: '≈', le: '≤', ge: '≥', ne: '≠', leq: '≤', geq: '≥', neq: '≠',
  sim: '∼', to: '→', rightarrow: '→', leftarrow: '←', propto: '∝' };
const MATH_BIN = { '+': '+', '-': '−', pm: '±', mp: '∓', times: '×', cdot: '·', div: '÷' };

// like TeX: spaces in the source are ignored; relations / binary operators get their own (a leading minus stays unary)
export function mathMarkup(t, text = false) {
  let out = '', i = 0, a, b;
  const op = (sym, rel) => {
    const prev = out.trimEnd();
    if ((rel && prev) || (prev && !'(=<>≈≤≥≠∼→←∝+−±∓×·÷,'.includes(prev.at(-1)))) out = `${prev} ${sym} `;
    else out += sym;                                       // unary: -x, = -x
  };
  while (i < t.length) {
    const c = t[i];
    if (c === ' ' && !text) { i++; continue; }
    if (!text && (c in MATH_REL || c in MATH_BIN)) { op(MATH_REL[c] ?? MATH_BIN[c], c in MATH_REL); i++; continue; }
    if (c === ',' && !text) { out += ', '; i++; continue; }
    if (c === '\\') {
      const m = /^([A-Za-z]+|.)/.exec(t.slice(i + 1)), name = m ? m[0] : '';
      i += 1 + name.length;
      if (name in MATH_SPACE) out += MATH_SPACE[name];
      else if (MATH_DROP.has(name)) { /* sizing only */ }
      else if (name in MATH_REL || name in MATH_BIN) op(MATH_REL[name] ?? MATH_BIN[name], name in MATH_REL);
      else if (MATH_TEXT.has(name)) { [a, i] = mathArg(t, i); out += mathMarkup(a, name.startsWith('text') || name === 'mbox'); }
      else if (['frac', 'dfrac', 'tfrac'].includes(name)) { [a, i] = mathArg(t, i); [b, i] = mathArg(t, i); out += `${paren(mathMarkup(a))}/${paren(mathMarkup(b))}\u2009`; }
      else if (name === 'sqrt') { [a, i] = mathArg(t, i); out += '√' + paren(mathMarkup(a)); }
      else if (name === 'overline' || name === 'bar') { [a, i] = mathArg(t, i); out += '~{' + mathMarkup(a) + '}'; }
      else if (name in MATH_SYMBOLS) out += MATH_SYMBOLS[name];
      else if (name in SYMBOLS) out += '\\' + name + '{}';
      else if (name in ESCAPES || '%&#'.includes(name)) out += name in ESCAPES ? '\\' + name : name;
      else out += name;                                    // \sin, \log, \max: the name itself
      continue;
    }
    if (c === '_' || c === '^') { [a, i] = mathArg(t, i + 1); out += c + '{' + mathMarkup(a) + '}'; continue; }
    if (c === '{') { [a, i] = mathArg(t, i); out += mathMarkup(a); continue; }
    out += { '~': ' ', '}': '' }[c] ?? c; i++;
  }
  return text ? out : out.trim();
}

function mathEnd(s, i) {
  for (let j = i + 1; j < s.length; j++) {
    if (s[j] === '\\') { j++; continue; }
    if (s[j] === '$') return j > i + 1 ? j : -1;
  }
  return -1;
}

// -> [[text, Set of 'over' | 'sub' | 'sup']], adjacent runs with the same flags merged
export function parse(s, flags = new Set()) {
  s = String(s ?? '');
  const out = [];
  let buf = '';
  const flush = () => { if (buf) { out.push([buf, flags]); buf = ''; } };
  let i = 0;
  while (i < s.length) {
    const c = s[i];
    if (c === '$') {
      const j = mathEnd(s, i);
      if (j > 0) { flush(); out.push(...parse(mathMarkup(s.slice(i + 1, j)), flags)); i = j + 1; continue; }
    }
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
