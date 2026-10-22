"""
Tests for restocking recommendation and restock order endpoints.
"""
from datetime import datetime, timedelta

import pytest

import main

TREND_RANK = {"increasing": 0, "stable": 1, "decreasing": 2}


@pytest.fixture(autouse=True)
def reset_restock_orders():
    """Restock orders are module-level state; isolate each test."""
    main.restock_orders.clear()
    yield
    main.restock_orders.clear()


def get_plan(client, budget):
    response = client.get(f"/api/restock/recommendations?budget={budget}")
    assert response.status_code == 200
    return response.json()


class TestRestockRecommendations:
    """Test suite for GET /api/restock/recommendations."""

    def test_zero_budget_returns_no_items(self, client):
        plan = get_plan(client, 0)
        assert plan["items"] == []
        assert plan["total_cost"] == 0
        assert plan["max_budget"] > 0

    def test_max_budget_buys_everything_in_full(self, client):
        max_budget = get_plan(client, 0)["max_budget"]
        plan = get_plan(client, max_budget)

        assert plan["total_cost"] == pytest.approx(max_budget)
        assert plan["remaining"] == pytest.approx(0, abs=0.01)
        assert all(not item["partial"] for item in plan["items"])
        assert all(item["quantity"] == item["target_quantity"] for item in plan["items"])

    def test_total_never_exceeds_budget(self, client):
        max_budget = get_plan(client, 0)["max_budget"]
        for fraction in (0.05, 0.25, 0.5, 0.75, 0.99):
            budget = round(max_budget * fraction, 2)
            plan = get_plan(client, budget)
            assert plan["total_cost"] <= budget
            assert plan["remaining"] == pytest.approx(budget - plan["total_cost"], abs=0.01)

    def test_full_lines_follow_priority_order(self, client):
        max_budget = get_plan(client, 0)["max_budget"]
        items = get_plan(client, max_budget)["items"]
        ranks = [TREND_RANK[item["trend"].lower()] for item in items]
        assert ranks == sorted(ranks)

    def test_mid_budget_produces_a_partial_line(self, client):
        max_budget = get_plan(client, 0)["max_budget"]
        plan = get_plan(client, round(max_budget * 0.3, 2))
        assert any(item["partial"] for item in plan["items"])

    def test_line_totals_match_quantity_times_cost(self, client):
        max_budget = get_plan(client, 0)["max_budget"]
        for item in get_plan(client, max_budget / 2)["items"]:
            assert item["line_total"] == pytest.approx(item["quantity"] * item["unit_cost"], abs=0.01)

    def test_negative_budget_rejected(self, client):
        response = client.get("/api/restock/recommendations?budget=-1")
        assert response.status_code == 400


class TestRestockOrders:
    """Test suite for /api/restock/orders."""

    def test_orders_start_empty(self, client):
        response = client.get("/api/restock/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_and_list_order(self, client):
        response = client.post("/api/restock/orders", json={"budget": 20000})
        assert response.status_code == 201

        order = response.json()
        assert order["id"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert order["total_cost"] <= 20000
        assert order["items"]
        assert order["lead_time_days"] == max(i["lead_time_days"] for i in order["items"])

        created = datetime.fromisoformat(order["created_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert expected - created == timedelta(days=order["lead_time_days"])

        listed = client.get("/api/restock/orders").json()
        assert [o["id"] for o in listed] == ["RST-0001"]

    def test_orders_listed_newest_first(self, client):
        client.post("/api/restock/orders", json={"budget": 5000})
        client.post("/api/restock/orders", json={"budget": 8000})
        ids = [o["id"] for o in client.get("/api/restock/orders").json()]
        assert ids == ["RST-0002", "RST-0001"]

    def test_order_matches_recommendation_for_same_budget(self, client):
        plan = get_plan(client, 12000)
        order = client.post("/api/restock/orders", json={"budget": 12000}).json()
        assert order["items"] == plan["items"]
        assert order["total_cost"] == plan["total_cost"]

    def test_budget_too_small_rejected(self, client):
        response = client.post("/api/restock/orders", json={"budget": 1})
        assert response.status_code == 400

    def test_negative_budget_rejected(self, client):
        response = client.post("/api/restock/orders", json={"budget": -100})
        assert response.status_code == 400
