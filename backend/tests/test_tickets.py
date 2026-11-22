import pytest
from datetime import datetime, timezone

def test_list_categories_with_priority_mapping(client):
    response = client.get("/api/categories")
    assert response.status_code == 200
    cats = {c["name"]: c["default_priority"] for c in response.json()}
    assert cats["Payment"] == "HIGH"
    assert cats["Survey Issue"] == "HIGH"
    assert cats["Profile Change"] == "MEDIUM"
    assert cats["Eligibility"] == "MEDIUM"
    assert cats["Other"] == "LOW"

def test_create_ticket_automatic_priority_and_id(client, member_headers):
    # Create ticket in Payment category (id=1, default HIGH)
    payload = {
        "category_id": 1,
        "subject": "Missing survey payment for cohort 4",
        "description": "Completed study on Thursday but payout was not received."
    }
    response = client.post("/api/tickets", json=payload, headers=member_headers)
    assert response.status_code == 201
    ticket = response.json()
    assert ticket["ticket_number"] == "TKT-0001"
    assert ticket["priority"] == "HIGH"
    assert ticket["status"] == "OPEN"
    assert ticket["reopen_count"] == 0
    assert ticket["total_paused_seconds"] == 0

def test_ticket_isolation_and_agent_queue(client, member_headers, other_member_headers, agent_headers):
    # Member creates ticket
    client.post(
        "/api/tickets",
        json={"category_id": 1, "subject": "Ticket A by Member 1", "description": "Description A text details"},
        headers=member_headers
    )

    # Other member creates ticket
    client.post(
        "/api/tickets",
        json={"category_id": 2, "subject": "Ticket B by Member 2", "description": "Description B text details"},
        headers=other_member_headers
    )

    # Member 1 views list -> only 1 ticket
    resp_m1 = client.get("/api/tickets", headers=member_headers)
    assert resp_m1.status_code == 200
    assert len(resp_m1.json()) == 1
    assert resp_m1.json()[0]["subject"] == "Ticket A by Member 1"

    # Agent views queue -> sees both tickets
    resp_agent = client.get("/api/tickets", headers=agent_headers)
    assert resp_agent.status_code == 200
    assert len(resp_agent.json()) == 2

def test_member_cannot_view_others_ticket(client, member_headers, other_member_headers):
    # Member 1 creates ticket
    created = client.post(
        "/api/tickets",
        json={"category_id": 1, "subject": "Private Inquiry", "description": "Confidential financial description"},
        headers=member_headers
    ).json()

    ticket_id = created["id"]

    # Member 2 tries to view ticket -> 403 Forbidden
    resp = client.get(f"/api/tickets/{ticket_id}", headers=other_member_headers)
    assert resp.status_code == 403

def test_agent_claim_and_assign(client, member_headers, agent_headers, db_session):
    from backend.app.models import User
    agent = db_session.query(User).filter(User.email == "agent@test.com").first()

    created = client.post(
        "/api/tickets",
        json={"category_id": 1, "subject": "Assigned Ticket", "description": "Needs agent attention"},
        headers=member_headers
    ).json()
    ticket_id = created["id"]
    assert created["status"] == "OPEN"

    # Agent claims ticket
    assign_resp = client.patch(
        f"/api/tickets/{ticket_id}/assign",
        json={"assigned_agent_id": agent.id},
        headers=agent_headers
    )
    assert assign_resp.status_code == 200
    updated = assign_resp.json()
    assert updated["assigned_agent_id"] == agent.id
    assert updated["status"] == "IN_PROGRESS"

def test_conversation_thread_and_replies(client, member_headers, agent_headers):
    created = client.post(
        "/api/tickets",
        json={"category_id": 2, "subject": "Thread Test", "description": "Initial inquiry message"},
        headers=member_headers
    ).json()
    ticket_id = created["id"]

    # Agent replies
    r1 = client.post(
        f"/api/tickets/{ticket_id}/replies",
        json={"message": "Agent investigating problem", "is_waiting_for_member": False},
        headers=agent_headers
    )
    assert r1.status_code == 201
    assert r1.json()["sender_role"] == "AGENT"

    # Member replies
    r2 = client.post(
        f"/api/tickets/{ticket_id}/replies",
        json={"message": "Member follows up with screenshot link", "is_waiting_for_member": False},
        headers=member_headers
    )
    assert r2.status_code == 201
    assert r2.json()["sender_role"] == "MEMBER"

    # Check detail view contains thread
    detail = client.get(f"/api/tickets/{ticket_id}", headers=member_headers).json()
    assert len(detail["replies"]) == 2
    assert len(detail["history"]) >= 1

def test_resolution_and_reopen_workflow(client, member_headers, agent_headers):
    created = client.post(
        "/api/tickets",
        json={"category_id": 3, "subject": "Profile update query", "description": "Need to update KYC details"},
        headers=member_headers
    ).json()
    ticket_id = created["id"]

    # Agent resolves ticket
    res_resp = client.post(
        f"/api/tickets/{ticket_id}/resolve",
        json={"resolution_note": "KYC phone number updated successfully"},
        headers=agent_headers
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "RESOLVED"
    assert res_resp.json()["resolved_at"] is not None

    # Member reopens ticket (attempt 1 of 2)
    reopen_resp = client.post(
        f"/api/tickets/{ticket_id}/reopen",
        json={"reason": "Number updated was incorrect, still receiving OTP on old phone"},
        headers=member_headers
    )
    assert reopen_resp.status_code == 200
    assert reopen_resp.json()["status"] == "REOPENED"
    assert reopen_resp.json()["reopen_count"] == 1

    # Agent resolves again
    client.post(
        f"/api/tickets/{ticket_id}/resolve",
        json={"resolution_note": "Corrected the mobile number digits"},
        headers=agent_headers
    )

    # Member reopens again (attempt 2 of 2)
    reopen2 = client.post(
        f"/api/tickets/{ticket_id}/reopen",
        json={"reason": "Still not working on secondary app verification"},
        headers=member_headers
    )
    assert reopen2.status_code == 200
    assert reopen2.json()["reopen_count"] == 2

    # Agent resolves again
    client.post(f"/api/tickets/{ticket_id}/resolve", headers=agent_headers)

    # Member 3rd attempt exceeds max 2 -> rejected 400
    reopen3 = client.post(
        f"/api/tickets/{ticket_id}/reopen",
        json={"reason": "Attempting 3rd reopen should fail by system policy"},
        headers=member_headers
    )
    assert reopen3.status_code == 400
    assert "Maximum reopen attempts (2) reached" in reopen3.json()["detail"]

def test_member_confirm_close_permanent(client, member_headers, agent_headers):
    created = client.post(
        "/api/tickets",
        json={"category_id": 4, "subject": "Eligibility test", "description": "Cooling period duration"},
        headers=member_headers
    ).json()
    ticket_id = created["id"]

    # Resolve
    client.post(f"/api/tickets/{ticket_id}/resolve", headers=agent_headers)

    # Member confirms resolution
    close_resp = client.post(f"/api/tickets/{ticket_id}/close", headers=member_headers)
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "CLOSED"

    # Cannot reopen CLOSED ticket
    reopen_resp = client.post(
        f"/api/tickets/{ticket_id}/reopen",
        json={"reason": "Trying to reopen a closed ticket"},
        headers=member_headers
    )
    assert reopen_resp.status_code == 400
    assert "Cannot reopen ticket in 'CLOSED' status" in reopen_resp.json()["detail"]
