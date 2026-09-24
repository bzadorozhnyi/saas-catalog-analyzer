import pytest
from fastapi.testclient import TestClient
from pydantic_ai.models.test import TestModel

from app.ai.agents import classification_agent
from main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_classify_returns_structured_result(client: TestClient) -> None:
    with classification_agent.override(model=TestModel()):
        response = client.post(
            "/v1/classify",
            json={"name": "Slack", "description": "Team messaging and chat app"},
        )

    assert response.status_code == 200
    body = response.json()
    assert "category" in body
    assert "confidence" in body
    assert "reasoning" in body
