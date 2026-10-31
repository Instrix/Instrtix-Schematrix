import json

import pytest
from fastapi.testclient import TestClient

from schematrix import Schematic, netio
from schematrix import symbols as SYM
from schematrix.document import normalize
from schematrix.symbols import custom

LDO = {'name': 'ldo_test', 'title': 'Test LDO', 'prefix': 'U', 'fields': ['Output voltage'],
       'prims': [{'k': 'rc', 'x': -30, 'y': -20, 'w': 60, 'h': 40, 'c': 'box', 'rx': 2},
                 {'k': 'pl', 'pts': [[-40, 0], [-30, 0]], 'c': 'w'}, {'k': 'pl', 'pts': [[30, 0], [40, 0]], 'c': 'w'},
                 {'k': 'pl', 'pts': [[0, 20], [0, 30]], 'c': 'w'}, {'k': 'tx', 'x': 0, 'y': 0, 's': 'LDO', 'c': 'valsm', 'ctr': True}],
       'pins': {'IN': [-40, 0], 'OUT': [40, 0], 'GND': [0, 30]}, 'spice': 'X {IN} {GND} {OUT} {model}'}


@pytest.fixture(autouse=True)
def cleanup():
    yield
    for n in ('ldo_test', 'ldo_moved'):
        custom.unregister(n)


def test_define_place_and_netlist():
    custom.define(**{k: v for k, v in LDO.items()})
    s = Schematic('c')
    u = s.ldo_test((100, 100), value='3.3 V')
    assert u.ref == 'U1' and set(u.pins) == {'IN', 'OUT', 'GND'}
    s.gnd(u['GND'])
    assert 'XU1 ' in s.spice() and '<rect' in s.to_svg()
    assert SYM.get('ldo_test').is_part and SYM.get('ldo_test').category == 'Custom'


def test_validation():
    with pytest.raises(custom.SymbolError):
        custom.register({**LDO, 'name': 'resistor'})            # built-in name
    with pytest.raises(custom.SymbolError):
        custom.register({**LDO, 'name': 'Bad Name'})
    with pytest.raises(custom.SymbolError):
        custom.register({**LDO, 'pins': {}})


def test_documents_carry_their_custom_symbols(tmp_path):
    custom.define(**LDO)
    s = Schematic('c'); s.ldo_test((0, 0))
    path = tmp_path / 'c.json'
    s.save(path)
    d = json.loads(path.read_text())
    assert 'ldo_test' in d['symbols']
    custom.unregister('ldo_test')
    with pytest.raises(KeyError):
        SYM.get('ldo_test')
    normalize(d)                                              # opening it registers the symbol again
    assert SYM.get('ldo_test').custom['pins']['OUT'] == [40, 0]


def test_copy_from_builtin():
    d = custom.from_builtin('npn', {'envelope': True}, 'npn_round')
    assert d['pins'] == {'C': [0, -30], 'B': [-30, 0], 'E': [0, 30]} and any(p['k'] == 'ci' for p in d['prims'])


def test_frame():
    s = Schematic('f')
    s.resistor((200, 200))
    s.frame('A4', title='Front end', rev='B', author='A. M.')
    pg = s.doc['page']
    assert (pg['width'], pg['height']) == (1123, 794) and pg['frame']['fields']['rev'] == 'B'
    texts = {e.get('field'): e['text'] for e in s.doc['elements'] if e.get('frame') and e['type'] == 'text' and e.get('field')}
    assert texts['title'] == 'Front end' and texts['rev'] == 'B'
    assert all(e['locked'] for e in s.doc['elements'] if e.get('frame'))
    s.frame('A3', 'portrait', title='Again')
    assert (s.doc['page']['width'], s.doc['page']['height']) == (1123, 1587)
    assert sum(1 for e in s.doc['elements'] if e.get('frame') and e.get('field') == 'title') == 1
    assert netio.from_doc(s.doc).parts[0].ref == 'R1'                # frames are not parts
    s.frame(None)
    assert not any(e.get('frame') for e in s.doc['elements']) and 'frame' not in s.doc['page']


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('SCHEMATRIX_WORKSPACE', str(tmp_path / 'ws'))
    from schematrix.server import create_app
    return TestClient(create_app(), base_url='http://localhost')


def test_symbol_endpoints(client, tmp_path):
    r = client.put('/api/symbols/custom/ldo_test', json=LDO)
    assert r.status_code == 200 and r.json()['custom']['title'] == 'Test LDO'
    assert (tmp_path / 'ws' / 'symbols' / 'ldo_test.json').exists()
    assert 'ldo_test' in {e['name'] for e in client.get('/api/symbols').json()}
    assert client.put('/api/symbols/custom/resistor', json=LDO).status_code == 400
    assert client.get('/api/symbols/copy/opamp').json()['pins']['out'] == [36, 0]
    assert client.delete('/api/symbols/custom/ldo_test').json() == {'ok': True}
    assert client.delete('/api/symbols/custom/resistor').status_code == 404
    assert client.post('/api/symbols/embedded', json={'symbols': {'ldo_moved': {**LDO, 'name': 'x'}}}).json() == {'added': ['ldo_moved']}
    f = client.post('/api/frame', json={'size': 'Letter', 'fields': {'title': 'T'}}).json()
    assert f['width'] == 1056 and any(e.get('field') == 'title' for e in f['elements'])
