def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] is True
    assert set(body.keys()) == {
        "status",
        "database",
        "ffmpeg",
        "openaiConfigured",
        "runwayConfigured",
        "storageConfigured",
        "instagramConfigured",
    }
    # Never expose secret values, only booleans/strings describing configuration state.
    assert body["openaiConfigured"] is False
    assert body["runwayConfigured"] is False
