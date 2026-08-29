from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_demo_status():
    r = client.get('/demo/status')
    assert r.status_code == 200
    data = r.json()
    assert 'demo_mode' in data
    assert 'message' in data


def test_demo_profiles_and_scenarios():
    r = client.get('/demo/profiles')
    assert r.status_code == 200
    d = r.json()
    assert 'profiles' in d and isinstance(d['profiles'], list)

    r2 = client.get('/demo/scenarios')
    assert r2.status_code == 200
    d2 = r2.json()
    assert 'scenarios' in d2 and isinstance(d2['scenarios'], list)
