import json
import os

import pytest
from fastapi.testclient import TestClient

from schematrix import Schematic, public as PUB

HERE = os.path.dirname(__file__)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('SCHEMATRIX_PUBLIC', '1')
    monkeypatch.setenv('SCHEMATRIX_SCRIPTS', '1')                 # public mode must override this
    monkeypatch.setenv('SCHEMATRIX_WORKSPACE', str(tmp_path / 'ws'))
    monkeypatch.delenv('SCHEMATRIX_TOKEN', raising=False)
    monkeypatch.setitem(PUB.LIMITS, 'rate', 10_000)
    monkeypatch.setitem(PUB.LIMITS, 'heavy_rate', 10_000)
    from schematrix.server import create_app
    c = TestClient(create_app(), base_url='http://localhost')
    c.ws = tmp_path / 'ws'
    return c


def doc():
    s = Schematic('t'); r = s.resistor((0, 0), value='1k'); s.gnd(r['2'])
    return s.doc


def test_no_token_needed_and_info(client):
    assert client.get('/').status_code == 200
    info = client.get('/api/info').json()
    assert info['public'] is True and info['scripts'] is False


def test_no_code_execution(client):
    for url in ('/api/run', '/api/import-legacy'):
        r = client.post(url, json={'code': 'import os; os.system("id")'})
        assert r.status_code == 403 and 'public' in r.json()['detail']


def test_no_server_storage(client):
    files = client.get('/api/files').json()
    assert files and all(f['path'].startswith('examples/') and f['readonly'] for f in files)
    assert client.get('/api/files/examples/analog/inverting-amplifier.json').json()['elements']
    assert client.put('/api/files/x.json', content=json.dumps(doc())).status_code == 403
    assert client.delete('/api/files/examples/rc-filter.py').status_code == 403
    for bad in ('examples/../../server.py', '../pyproject.toml', 'examples/../public.py', 'server.py'):
        assert client.get('/api/files/' + bad).status_code in (400, 404)
    assert not client.ws.exists()                                  # nothing was created on disk


def test_no_shared_symbol_library(client):
    d = {'prims': [{'k': 'rc', 'x': 0, 'y': 0, 'w': 10, 'h': 10, 'c': 'box'}], 'pins': {'1': [0, 0]}}
    assert client.put('/api/symbols/custom/mine', json=d).status_code == 403
    assert client.delete('/api/symbols/custom/mine').status_code == 403
    assert client.post('/api/symbols/embedded', json={'symbols': {'mine': d}}).status_code == 403
    dd = {**doc(), 'symbols': {'mine': d}}
    r = client.post('/api/export', json={'doc': dd, 'format': 'svg'})
    assert r.status_code == 400 and 'custom symbols' in r.json()['detail']


def test_export_still_works_and_is_sandboxed(client):
    r = client.post('/api/export', json={'doc': doc(), 'format': 'svg'})
    assert r.status_code == 200 and r.headers['content-security-policy'].startswith('sandbox')
    assert client.post('/api/netlist/export?format=kicad', json={'doc': doc()}).status_code == 200
    assert 'default-src' in client.get('/').headers['content-security-policy']


def test_raw_svg_is_cleaned(client):
    d = doc()
    d['elements'].append({'type': 'raw', 'svg': '<g onclick="alert(1)"><script>alert(2)</script><a href="javascript:x()"><rect/></a></g>'})
    svg = client.post('/api/export', json={'doc': d, 'format': 'svg', 'fonts': False}).text
    assert 'script' not in svg and 'onclick' not in svg and 'javascript' not in svg and '<rect' in svg


def test_limits(client, monkeypatch):
    monkeypatch.setitem(PUB.LIMITS, 'max_elements', 3)
    assert client.post('/api/export', json={'doc': doc(), 'format': 'svg'}).status_code == 200
    big = doc(); big['elements'] *= 3
    assert client.post('/api/export', json={'doc': big, 'format': 'svg'}).status_code == 400
    monkeypatch.setitem(PUB.LIMITS, 'max_body', 100)
    assert client.post('/api/export', json={'doc': doc(), 'format': 'svg'}).status_code == 413
    monkeypatch.setitem(PUB.LIMITS, 'max_body', 4 << 20)
    monkeypatch.setitem(PUB.LIMITS, 'max_pixels', 1000)
    pytest.importorskip('cairosvg')
    r = client.post('/api/export', json={'doc': doc(), 'format': 'png', 'scale': 8})
    assert r.status_code == 400 and 'too large' in r.json()['detail']


def test_rate_limit(client, monkeypatch):
    monkeypatch.setitem(PUB.LIMITS, 'heavy_rate', 3)
    codes = [client.post('/api/export', json={'doc': doc(), 'format': 'svg'}).status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200] and codes[3] == 429
    assert client.get('/api/health').status_code == 200            # never limited


def test_private_mode_unchanged(tmp_path, monkeypatch):
    monkeypatch.delenv('SCHEMATRIX_PUBLIC', raising=False)
    monkeypatch.setenv('SCHEMATRIX_WORKSPACE', str(tmp_path / 'ws'))
    from schematrix.server import create_app
    c = TestClient(create_app(), base_url='http://localhost')
    assert c.get('/api/info').json()['public'] is False
    assert c.put('/api/files/x.json', content=json.dumps(doc())).status_code == 200
