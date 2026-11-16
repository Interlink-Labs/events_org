import pytest
from fastapi.testclient import TestClient
from main import app
from database import engine, Base

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_databases(tmp_path):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # модуль услуг работает со своей SQLite-базой: на время теста - чистая временная
    import services_db
    services_db.DB_PATH = str(tmp_path / "services_test.db")
    services_db.init_db()
    yield

def test_create_venue_and_base_services():
    response = client.post("/api/v1/venues/create", json={"name": "Зал", "address": "ул. Мира", "capacity": 100})
    assert response.status_code == 200
    assert response.json()["venue_id"] == 1

    services = client.get("/api/v1/services/list", params={"venue_id": 1}).json()
    assert len(services) == 6
    assert all(s["is_base"] for s in services)

def test_update_service_phone():
    client.post("/api/v1/venues/create", json={"name": "Зал", "address": "ул. Мира", "capacity": 100})
    response = client.post("/api/v1/services/phone", json={"service_id": 1, "contact_phone": "+7 999 111-22-33"})
    assert response.status_code == 200

    services = client.get("/api/v1/services/list").json()
    assert services[0]["contact_phone"] == "+7 999 111-22-33"

def test_service_crud():
    client.post("/api/v1/venues/create", json={"name": "Зал", "address": "ул. Мира", "capacity": 100})
    res = client.post("/api/v1/services/create", json={"venue_id": 1, "name": "Диджей", "price": 15000})
    assert res.status_code == 200
    service_id = res.json()["service_id"]
    assert client.post("/api/v1/services/create", json={"venue_id": 1, "name": "Диджей"}).status_code == 409

    res = client.post("/api/v1/services/update", json={"service_id": service_id, "name": "Диджей", "price": 20000})
    assert res.json()["service"]["price"] == 20000

    assert client.post("/api/v1/services/delete", params={"service_id": service_id}).status_code == 200
    assert client.post("/api/v1/services/get", params={"service_id": service_id}).status_code == 404

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