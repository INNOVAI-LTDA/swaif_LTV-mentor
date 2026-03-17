from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthcheck_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_preflight_allows_frontend_origin() -> None:
    origin = "http://localhost:5173"
    response = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
