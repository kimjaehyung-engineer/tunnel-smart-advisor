from fastapi.testclient import TestClient

import backend.main as main
from backend.services.data_loader import load_data


def test_admin_cache_reload_clears_cache_and_returns_counts() -> None:
    client = TestClient(main.app)

    before = load_data.cache_info()
    response = client.post("/admin/cache/reload")
    after = load_data.cache_info()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "reloaded"
    assert body["data"]["risk"] > 0
    assert after.currsize == 1
    assert after.misses >= before.misses
