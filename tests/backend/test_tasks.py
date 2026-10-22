"""
Tests for the /api/tasks endpoints used by the profile Tasks modal.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def reset_tasks():
    """Tasks are module-level state; isolate each test."""
    main.tasks.clear()
    main.task_counter = 0
    yield
    main.tasks.clear()
    main.task_counter = 0


def create(client, **overrides):
    payload = {"title": "Review Q4 inventory", "priority": "high", "dueDate": "2025-10-08"}
    payload.update(overrides)
    return client.post("/api/tasks", json=payload)


class TestTaskCrud:
    """Create, list, toggle and delete tasks."""

    def test_list_starts_empty(self, client):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_returns_client_shape(self, client):
        response = create(client)
        assert response.status_code == 201
        assert response.json() == {
            "id": "TASK-0001",
            "title": "Review Q4 inventory",
            "priority": "high",
            "dueDate": "2025-10-08",
            "status": "pending",
        }

    def test_ids_are_strings_not_mock_numbers(self, client):
        # The client's mock tasks use numeric ids 1-4; API ids must never equal them
        task = create(client).json()
        assert isinstance(task["id"], str)
        assert task["id"] not in {1, 2, 3, 4}

    def test_list_is_newest_first(self, client):
        create(client, title="first")
        create(client, title="second")
        titles = [t["title"] for t in client.get("/api/tasks").json()]
        assert titles == ["second", "first"]

    def test_toggle_flips_status_both_ways(self, client):
        task_id = create(client).json()["id"]
        first = client.patch(f"/api/tasks/{task_id}")
        assert first.status_code == 200
        assert first.json()["status"] == "completed"
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "pending"

    def test_delete_removes_task(self, client):
        task_id = create(client).json()["id"]
        assert client.delete(f"/api/tasks/{task_id}").status_code == 204
        assert client.get("/api/tasks").json() == []

    def test_title_is_trimmed(self, client):
        assert create(client, title="  padded  ").json()["title"] == "padded"

    def test_priority_defaults_to_medium(self, client):
        response = client.post("/api/tasks", json={"title": "x", "dueDate": "2025-10-08"})
        assert response.json()["priority"] == "medium"


class TestTaskErrors:
    """Validation and not-found handling."""

    @pytest.mark.parametrize("method", ["patch", "delete"])
    def test_unknown_task_returns_404(self, client, method):
        response = getattr(client, method)("/api/tasks/TASK-9999")
        assert response.status_code == 404

    @pytest.mark.parametrize("overrides", [
        {"title": ""},
        {"title": "   "},
        {"priority": "urgent"},
        {"dueDate": "not-a-date"},
        {"dueDate": "2025-13-01"},
    ])
    def test_invalid_payload_returns_422(self, client, overrides):
        assert create(client, **overrides).status_code == 422

    def test_missing_due_date_returns_422(self, client):
        response = client.post("/api/tasks", json={"title": "x", "priority": "low"})
        assert response.status_code == 422
