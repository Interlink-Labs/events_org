import pytest
from fastapi.testclient import TestClient
from main import app
from database import engine, Base

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_databases():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_create_venue_and_base_services():
    response = client.post("/api/v1/venues/create", json={"name": "Зал", "address": "ул. Мира", "capacity": 100})
    assert response.status_code == 200
    assert response.json()["venue_id"] == 1

    services = client.get("/api/v1/manager/services").json()
    assert len(services) == 2
    assert services[0]["name"] == "Аренда зала"

def test_update_service_phone():
    client.post("/api/v1/venues/create", json={"name": "Зал", "address": "ул. Мира", "capacity": 100})
    response = client.post("/api/v1/manager/services/1/phone", json={"contact_phone": "+7 999 111-22-33"})
    assert response.status_code == 200
    
    services = client.get("/api/v1/manager/services").json()
    assert services[0]["contact_phone"] == "+7 999 111-22-33"

def test_full_billing_flow():
    event_id = 10
    res = client.post(f"/api/v1/billing/events/{event_id}/estimate/items", 
                      json={"name": "Банкет", "quantity": 1, "unit_price": 50000, "item_type": "service"})
    assert float(res.json()["total"]) == 50000.0

    res = client.post(f"/api/v1/billing/events/{event_id}/estimate/expenses", json={"name": "Шары", "amount": 5000})
    assert float(res.json()["total"]) == 55000.0

    res = client.post(f"/api/v1/billing/events/{event_id}/payments", json={"amount": 20000, "method": "card"})
    payment_id = res.json()["payment_id"]
    
    est = client.get(f"/api/v1/billing/events/{event_id}/estimate").json()
    assert float(est["estimate"]["debt_amount"]) == 55000.0
    
    res = client.post(f"/api/v1/billing/payments/{payment_id}/confirm")
    assert res.status_code == 200

    res = client.post(f"/api/v1/billing/payments/{payment_id}/refund")
    assert res.status_code == 200

    logs = client.get(f"/api/v1/billing/payments/{payment_id}/logs").json()
    assert len(logs) == 3
    assert logs[1]["action"] == "confirmed"
    assert logs[2]["action"] == "refunded"

def test_estimate_status_locks_editing():
    event_id = 20
    client.post(f"/api/v1/billing/events/{event_id}/estimate/items", 
                json={"name": "Аренда", "quantity": 1, "unit_price": 10000, "item_type": "service"})
    
    res = client.patch(f"/api/v1/billing/events/{event_id}/estimate/status", json={"status": "approved"})
    assert res.status_code == 200

    res = client.patch(f"/api/v1/billing/events/{event_id}/estimate/items/1", json={"quantity": 5})
    assert res.status_code == 400