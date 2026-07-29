import os

import pytest
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = 5


@pytest.mark.regression
def test_health_endpoint_is_available():
    response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.regression
def test_stages_contract_remains_compatible():
    response = requests.get(f"{BASE_URL}/api/stages", timeout=TIMEOUT)
    body = response.json()

    assert response.status_code == 200
    assert body["count"] == 5
    assert body["items"][0] == {"id": 1, "name": "Código"}
    assert body["items"][-1] == {"id": 5, "name": "Despliegue"}


@pytest.mark.regression
def test_progress_calculation_through_http():
    response = requests.get(
        f"{BASE_URL}/api/progress",
        params={"completed": 3},
        timeout=TIMEOUT,
    )

    assert response.status_code == 200
    assert response.json() == {"completed": 3, "percentage": 60, "total": 5}


@pytest.mark.regression
def test_invalid_progress_keeps_the_error_contract():
    response = requests.get(
        f"{BASE_URL}/api/progress",
        params={"completed": "invalido"},
        timeout=TIMEOUT,
    )

    assert response.status_code == 400
    assert response.json() == {"error": "completed debe ser un número entero"}
