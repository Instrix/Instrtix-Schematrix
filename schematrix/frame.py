"""Page frames: a drawing border with zone markers and a title block, made of ordinary (locked) elements.

    els, (w, h) = frame_elements('A4', 'landscape', {'title': 'Front end', 'author': 'A. M.', 'rev': 'B'})

Every generated element carries 'frame': True and 'locked': True, so the editor can regenerate the frame when the
page size or a title-block field changes, and nobody drags it by accident. Sizes are in drawing units (96 per inch).
"""
from __future__ import annotations

import datetime as dt

MM = 96 / 25.4
SIZES = {'A4': (297, 210), 'A3': (420, 297), 'A2': (594, 420), 'A1': (841, 594), 'A5': (210, 148),
         'Letter': (279.4, 215.9), 'Legal': (355.6, 215.9), 'Tabloid': (431.8, 279.4)}
FIELDS = ['title', 'subtitle', 'company', 'doc', 'rev', 'author', 'date', 'sheet']
CAPTIONS = {'title': 'TITLE', 'subtitle': '', 'company': 'COMPANY', 'doc': 'DOCUMENT', 'rev': 'REV', 'author': 'DRAWN',
            'date': 'DATE', 'sheet': 'SHEET'}


def page_size(size='A4', orientation='landscape') -> tuple:
    w, h = SIZES[size]
    if orientation == 'portrait':
        w, h = min(w, h), max(w, h)
    else:
        w, h = max(w, h), min(w, h)
    return round(w * MM), round(h * MM)


def _r(x, y, w, h, cls='frame'):
    return {'type': 'rect', 'x': round(x, 2), 'y': round(y, 2), 'w': round(w, 2), 'h': round(h, 2), 'cls': cls, 'rx': 0,
            'frame': True, 'locked': True}


def _t(x, y, s, cls='grplbl', anchor='start', field=None):
    el = {'type': 'text', 'x': round(x, 2), 'y': round(y, 2), 'text': s, 'cls': cls, 'anchor': anchor, 'frame': True, 'locked': True}
    if field:
        el['field'] = field
    return el


def frame_elements(size='A4', orientation='landscape', fields=None, zones=True):
    """-> (elements, (width, height)) for a page of that size, origin at the page's top-left corner"""
    W, H = page_size(size, orientation)
    f = {k: '' for k in FIELDS}
    f.update({k: str(v) for k, v in (fields or {}).items() if v is not None})
    if not f['date']:
        f['date'] = dt.date.today().isoformat()
    m, z = 10 * MM, 4 * MM                         # outer margin, zone strip
    els = [_r(m, m, W - 2 * m, H - 2 * m), _r(m + z, m + z, W - 2 * (m + z), H - 2 * (m + z))]
    if zones:
        nx, ny = max(2, round((W - 2 * m) / (50 * MM))), max(2, round((H - 2 * m) / (50 * MM)))
        zw, zh = (W - 2 * m) / nx, (H - 2 * m) / ny
        for i in range(nx):
            x = m + zw * (i + 0.5)
            els += [_t(x, m + z - 3.5, str(i + 1), anchor='middle'), _t(x, H - m - 4, str(i + 1), anchor='middle')]
            if i:
                xx = m + zw * i
                els += [_r(xx, m, 0.01, z), _r(xx, H - m - z, 0.01, z)]
        for j in range(ny):
            y = m + zh * (j + 0.5) + 3.5
            letter = chr(ord('A') + j)
            els += [_t(m + z / 2, y, letter, anchor='middle'), _t(W - m - z / 2, y, letter, anchor='middle')]
            if j:
                yy = m + zh * j
                els += [_r(m, yy, z, 0.01), _r(W - m - z, yy, z, 0.01)]
    # title block, bottom right
    bw, rh = 100 * MM, 8 * MM
    x0, y0 = W - m - z - bw, H - m - z - 4 * rh
    els.append(_r(x0, y0, bw, 4 * rh, 'box'))
    els += [_r(x0, y0 + 2 * rh, bw, 0.01), _r(x0, y0 + 3 * rh, bw, 0.01)]
    c1, c2 = x0 + bw * 0.45, x0 + bw * 0.75
    els += [_r(c1, y0 + 2 * rh, 0.01, 2 * rh), _r(c2, y0 + 2 * rh, 0.01, 2 * rh)]
    pad = 2 * MM
    els += [_t(x0 + pad, y0 + 12, CAPTIONS['title']), _t(x0 + pad, y0 + 1.3 * rh + 6, f['title'], 'title', field='title'),
            _t(x0 + bw - pad, y0 + 13, f['subtitle'], 'note', 'end', field='subtitle')]
    cells = [(x0, y0 + 2 * rh, 'company'), (c1, y0 + 2 * rh, 'doc'), (c2, y0 + 2 * rh, 'rev'),
             (x0, y0 + 3 * rh, 'author'), (c1, y0 + 3 * rh, 'date'), (c2, y0 + 3 * rh, 'sheet')]
    for x, y, k in cells:
        els += [_t(x + pad, y + 11, CAPTIONS[k]), _t(x + pad, y + rh - 5, f[k], 'lbl', field=k)]
    return els, (W, H)


def apply(doc, size='A4', orientation='landscape', fields=None):
    """put a frame on a document (replacing any previous one) and size its page to match; size None removes it"""
    doc['elements'] = [e for e in doc['elements'] if not e.get('frame')]
    pg = doc.setdefault('page', {})
    if not size:
        pg.pop('frame', None)
        return doc
    els, (w, h) = frame_elements(size, orientation, fields)
    for i, e in enumerate(els):
        e['id'] = f'frame{i + 1}'
    doc['elements'] = els + doc['elements']
    pg.update(auto=False, x=0, y=0, width=w, height=h)
    pg['frame'] = {'size': size, 'orientation': orientation, 'fields': {k: v for k, v in (fields or {}).items() if v}}
    return doc
