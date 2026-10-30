import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('SCHEMATRIX_WORKSPACE', str(tmp_path / 'ws'))
    from schematrix.server import create_app
    return TestClient(create_app())


def doc():
    from schematrix import Schematic
    s = Schematic('t'); r = s.resistor((0, 0), value='1k'); s.gnd(r['2'])
    return s.doc


def test_index_and_symbols(client):
    assert client.get('/').status_code == 200
    syms = client.get('/api/symbols').json()
    assert {'resistor', 'opamp', 'nmos', 'flag'} <= {s['name'] for s in syms}
    g = client.post('/api/geometry', json={'items': [{'sym': 'flag', 'props': {'label': 'LONGNAME'}}]}).json()[0]
    assert g['pins'] == {'p': [0, 0]}


def test_workspace_seeded_and_files(client):
    files = [f['path'] for f in client.get('/api/files').json()]
    assert 'examples/tr-0002/fig-chain.json' in files
    assert client.put('/api/files/a/b.json', content=json.dumps(doc())).status_code == 200
    assert client.get('/api/files/a/b.json').json()['meta']['title'] == 't'
    assert client.put('/api/files/../evil.json', content='{}').status_code in (400, 404)
    assert client.put('/api/files/x.sh', content='rm').status_code == 400
    assert client.put('/api/files/bad.json', content='{"x":1}').status_code == 400


def test_render_netlist(client):
    r = client.post('/api/render?format=svg', json={'doc': doc()})
    assert r.text.startswith('<svg') and '@font-face' in r.text
    n = client.post('/api/netlist', json={'doc': doc()}).json()
    assert 'R1' in n['spice']


def test_scripts_toggle(client, monkeypatch):
    r = client.post('/api/run', json={'code': "from schematrix import Schematic\nSchematic('x').resistor((0,0))"}).json()
    assert r['ok'] and r['docs']
    monkeypatch.setenv('SCHEMATRIX_SCRIPTS', '0')
    assert client.post('/api/run', json={'code': 'print(1)'}).status_code == 403


def test_token(tmp_path, monkeypatch):
    monkeypatch.setenv('SCHEMATRIX_WORKSPACE', str(tmp_path))
    monkeypatch.setenv('SCHEMATRIX_TOKEN', 'sekrit')
    from schematrix.server import create_app
    c = TestClient(create_app())
    assert c.get('/api/symbols').status_code == 401
    assert c.get('/api/symbols', headers={'Authorization': 'Bearer sekrit'}).status_code == 200
    assert c.get('/?token=sekrit').status_code == 200
    assert c.get('/api/symbols').status_code == 200          # cookie set


@pytest.mark.parametrize('fmt', ['spice', 'kicad', 'json'])
def test_netlist_export_import(client, fmt):
    r = client.post(f'/api/netlist/export?format={fmt}', json={'doc': doc()})
    assert r.status_code == 200 and 'attachment' in r.headers['content-disposition']
    back = client.post('/api/netlist/import', json={'text': r.text, 'filename': 'x' + {'spice': '.cir', 'kicad': '.net', 'json': '.json'}[fmt]}).json()
    assert back['format'] == fmt
    assert any(e.get('sym') == 'resistor' and e['props']['ref'] == 'R1' for e in back['doc']['elements'])
    assert client.post('/api/netlist/import', json={'text': ''}).status_code == 400
    assert {f['name'] for f in client.get('/api/info').json()['netlist_formats']} == {'spice', 'kicad', 'json'}
