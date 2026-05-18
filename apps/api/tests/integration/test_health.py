from app import __version__


def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body == {"status": "ok", "version": __version__}
