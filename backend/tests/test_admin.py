def test_admin_metrics(client, admin_headers, member_headers, agent_headers):
    # Create ticket
    client.post(
        "/api/tickets",
        json={"category_id": 1, "subject": "Metrics Ticket", "description": "Testing admin metrics"},
        headers=member_headers
    )

    resp = client.get("/api/admin/metrics", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_open_tickets" in data
    assert "overdue_tickets_count" in data
    assert "escalated_tickets_count" in data
    assert "resolved_today_count" in data
    assert "average_resolution_time_hours" in data
    assert "category_breakdown" in data
    assert data["total_open_tickets"] >= 1

def test_admin_update_tat_settings(client, admin_headers):
    # Update HIGH priority from 4h to 6h
    resp = client.put(
        "/api/admin/tat-settings/HIGH",
        json={"tat_hours": 6},
        headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["tat_hours"] == 6

    # Verify listing
    list_resp = client.get("/api/admin/tat-settings", headers=admin_headers)
    assert list_resp.status_code == 200
    high_setting = next(s for s in list_resp.json() if s["priority"] == "HIGH")
    assert high_setting["tat_hours"] == 6

def test_admin_system_settings_singleton(client, admin_headers):
    # Get singleton
    resp = client.get("/api/admin/system-settings", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == 1
    assert resp.json()["reopen_window_days"] == 7
    assert resp.json()["max_reopen_attempts"] == 2

    # Update parameters
    put_resp = client.put(
        "/api/admin/system-settings",
        json={"reopen_window_days": 10, "max_reopen_attempts": 3},
        headers=admin_headers
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["reopen_window_days"] == 10
    assert put_resp.json()["max_reopen_attempts"] == 3

def test_trigger_escalation_endpoint(client, admin_headers):
    resp = client.post("/api/admin/run-escalation-check", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    assert "escalated_count" in resp.json()
