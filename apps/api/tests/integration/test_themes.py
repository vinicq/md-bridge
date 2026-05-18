def test_themes_lists_default(client):
    resp = client.get("/api/themes")
    assert resp.status_code == 200, resp.text
    themes = resp.json()
    assert isinstance(themes, list)
    ids = {t["id"] for t in themes}
    assert "default" in ids
    default = next(t for t in themes if t["id"] == "default")
    assert default["name"]
