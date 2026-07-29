import pytest

from app import STAGES, calculate_progress, create_app


@pytest.fixture
def client():
    return create_app().test_client()


def test_health_reports_a_healthy_service(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_stages_preserve_the_pipeline_contract(client):
    response = client.get("/api/stages")
    body = response.get_json()

    assert response.status_code == 200
    assert body["count"] == 5
    assert [stage["name"] for stage in body["items"]] == [
        "Código",
        "Análisis",
        "Construcción",
        "Regresión",
        "Despliegue",
    ]


@pytest.mark.parametrize(
    ("completed", "expected"),
    [(0, 0), (2, 40), (5, 100), (-1, 0), (9, 100)],
)
def test_calculate_progress_limits_the_result(completed, expected):
    assert calculate_progress(completed, len(STAGES)) == expected


def test_progress_returns_bad_request_for_invalid_input(client):
    response = client.get("/api/progress?completed=no-es-un-numero")

    assert response.status_code == 400
    assert "error" in response.get_json()
