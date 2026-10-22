"""
Tests for report endpoints (quarterly and monthly trends) and their filters.
"""
import pytest


def get(client, path, **params):
    response = client.get(path, params=params)
    assert response.status_code == 200
    return response.json()


class TestQuarterlyReports:
    """Test suite for GET /api/reports/quarterly."""

    def test_structure_and_order(self, client):
        data = get(client, "/api/reports/quarterly")
        assert data, "expected quarterly data"
        assert [q["quarter"] for q in data] == sorted(q["quarter"] for q in data)
        for q in data:
            for field in ("quarter", "total_orders", "total_revenue",
                          "avg_order_value", "fulfillment_rate", "delivered_orders"):
                assert field in q
            assert 0 <= q["fulfillment_rate"] <= 100

    def test_totals_match_orders_endpoint(self, client):
        quarters = get(client, "/api/reports/quarterly")
        orders = get(client, "/api/orders")
        assert sum(q["total_orders"] for q in quarters) == len(orders)

    def test_warehouse_filter_narrows_results(self, client):
        all_orders = sum(q["total_orders"] for q in get(client, "/api/reports/quarterly"))
        tokyo = get(client, "/api/reports/quarterly", warehouse="Tokyo")
        tokyo_orders = get(client, "/api/orders", warehouse="Tokyo")
        assert sum(q["total_orders"] for q in tokyo) == len(tokyo_orders)
        assert sum(q["total_orders"] for q in tokyo) < all_orders

    def test_month_filter_keeps_only_its_quarter(self, client):
        data = get(client, "/api/reports/quarterly", month="2025-01")
        assert [q["quarter"] for q in data] == ["Q1-2025"]

    def test_status_filter(self, client):
        data = get(client, "/api/reports/quarterly", status="delivered")
        assert all(q["fulfillment_rate"] == 100.0 for q in data)


class TestMonthlyTrends:
    """Test suite for GET /api/reports/monthly-trends."""

    def test_structure_and_order(self, client):
        data = get(client, "/api/reports/monthly-trends")
        assert data
        assert [m["month"] for m in data] == sorted(m["month"] for m in data)
        for m in data:
            assert {"month", "order_count", "revenue", "delivered_count"} <= m.keys()

    def test_month_filter_returns_single_month(self, client):
        data = get(client, "/api/reports/monthly-trends", month="2025-03")
        assert [m["month"] for m in data] == ["2025-03"]

    def test_quarter_filter_returns_three_months(self, client):
        data = get(client, "/api/reports/monthly-trends", month="Q2-2025")
        assert [m["month"] for m in data] == ["2025-04", "2025-05", "2025-06"]

    def test_category_filter_matches_orders(self, client):
        data = get(client, "/api/reports/monthly-trends", category="sensors")
        orders = get(client, "/api/orders", category="sensors")
        assert sum(m["order_count"] for m in data) == len(orders)
        assert sum(m["revenue"] for m in data) == pytest.approx(
            sum(o["total_value"] for o in orders), abs=0.05)
