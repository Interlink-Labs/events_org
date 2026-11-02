#python -m pytest -v
import pytest
from fastapi.testclient import TestClient
from main import app, venues_db, services_db
from billing import storage as billing_storage
import main  # Импортируем сам модуль main, чтобы получить доступ к его глобальным счетчикам

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_databases():
    """Очищает in-memory базы перед каждым тестом"""
    venues_db.clear()
    services_db.clear()
    billing_storage.estimates_db.clear()
    billing_storage.event_to_estimate.clear()
    billing_storage.items_db.clear()
    billing_storage.expenses_db.clear()
    billing_storage.payments_db.clear()
    billing_storage.payment_logs_db.clear()
    
    # Сбрасываем счетчики billing
    for k in billing_storage._counters:
        billing_storage._counters[k] = 0
        
    # Сбрасываем счетчики main (локации и услуги)
    main._venue_counter = 1
    main._service_counter = 1
    
    yield

# ==================== ТЕСТЫ: ЛОКАЦИИ И УСЛУГИ ====================

def test_create_venue_and_base_services():
    # 1. Создаем локацию
    response = client.post("/api/v1/venues/create", json={"name": "Зал", "address": "ул. Мира", "capacity": 100})
    assert response.status_code == 200
    assert response.json()["venue_id"] == 1

    # 2. Проверяем, что автоматически создались 2 базовые услуги (ТЗ п.13)
    services = client.get("/api/v1/manager/services").json()
    assert len(services) == 2
    assert services[0]["name"] == "Аренда зала"
    assert services[1]["name"] == "Уборка"

def test_update_service_phone():
    client.post("/api/v1/venues/create", json={"name": "Зал", "address": "ул. Мира", "capacity": 100})
    
    # Меняем телефон для услуги с id=1
    response = client.post("/api/v1/manager/services/1/phone", json={"contact_phone": "+7 999 111-22-33"})
    assert response.status_code == 200
    
    services = client.get("/api/v1/manager/services").json()
    
    # Ищем услугу с id=1, независимо от её позиции в списке
    service_1 = next(s for s in services if s["id"] == 1)
    
    assert service_1["contact_phone"] == "+7 999 111-22-33"

# ==================== ТЕСТЫ: СМЕТА И ОПЛАТА ====================

def test_full_billing_flow():
    event_id = 10
    
    # 1. Добавляем услугу (50000)
    res = client.post(f"/api/v1/billing/events/{event_id}/estimate/items", 
                      json={"name": "Банкет", "quantity": 1, "unit_price": 50000, "item_type": "service"})
    assert res.status_code == 200
    assert float(res.json()["total"]) == 50000.0

    # 2. Добавляем доп. расход (5000). Итог должен стать 55000
    res = client.post(f"/api/v1/billing/events/{event_id}/estimate/expenses", 
                      json={"name": "Шары", "amount": 5000})
    assert float(res.json()["total"]) == 55000.0

    # 3. Клиент вносит 20000
    res = client.post(f"/api/v1/billing/events/{event_id}/payments", 
                      json={"amount": 20000, "method": "card"})
    payment_id = res.json()["payment_id"]
    
    # Долг все еще 55000, так как платеж не подтвержден
    est = client.get(f"/api/v1/billing/events/{event_id}/estimate").json()
    assert float(est["debt_amount"]) == 55000.0
    
    # 4. Подтверждаем платеж
    res = client.post(f"/api/v1/billing/payments/{payment_id}/confirm")
    assert float(res.json()["remaining_debt"]) == 35000.0

    # 5. Делаем возврат средств (refund)
    res = client.post(f"/api/v1/billing/payments/{payment_id}/refund")
    assert float(res.json()["new_debt"]) == 55000.0

    # 6. Проверяем лог платежа (создан -> подтвержден -> возвращен)
    logs = client.get(f"/api/v1/billing/payments/{payment_id}/logs").json()
    assert len(logs) == 3
    assert logs[1]["action"] == "confirmed"
    assert logs[2]["action"] == "refunded"

def test_estimate_status_locks_editing():
    event_id = 20
    # Добавляем позицию
    client.post(f"/api/v1/billing/events/{event_id}/estimate/items", 
                json={"name": "Аренда", "quantity": 1, "unit_price": 10000, "item_type": "service"})
    
    # Менеджер утверждает смету
    res = client.patch(f"/api/v1/billing/events/{event_id}/estimate/status", json={"status": "approved"})
    assert res.status_code == 200

    # Пытаемся изменить позицию, когда смета утверждена — должна быть ошибка 400
    res = client.patch(f"/api/v1/billing/events/{event_id}/estimate/items/1", json={"quantity": 5})
    assert res.status_code == 400
    assert "запрещены" in res.json()["detail"]