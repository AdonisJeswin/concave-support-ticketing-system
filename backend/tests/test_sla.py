import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import OperationalError, IntegrityError
from backend.app.models.ticket import Ticket
from backend.app.models.history import TicketHistory
from backend.app.services.sla_service import (
    check_and_escalate_overdue_tickets,
    recalculate_on_priority_change
)

def test_tat_pause_and_resume_on_member_reply(client, member_headers, agent_headers, db_session):
    created = client.post(
        "/api/tickets",
        json={"category_id": 1, "subject": "Payment pause test", "description": "Need assistance with payment"},
        headers=member_headers
    ).json()
    ticket_id = created["id"]

    # 1. Agent asks for info with is_waiting_for_member=True -> Pauses TAT
    reply_resp = client.post(
        f"/api/tickets/{ticket_id}/replies",
        json={"message": "Please send your UPI transaction reference screenshot", "is_waiting_for_member": True},
        headers=agent_headers
    )
    assert reply_resp.status_code == 201

    t_paused = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
    assert t_paused.tat_paused_at is not None

    # Simulate 120 seconds elapsed in pause
    t_paused.tat_paused_at = datetime.now(timezone.utc) - timedelta(seconds=120)
    db_session.commit()

    # 2. Member replies -> Resumes TAT and extends due_at
    due_before = t_paused.due_at.replace(tzinfo=timezone.utc) if t_paused.due_at.tzinfo is None else t_paused.due_at
    member_reply = client.post(
        f"/api/tickets/{ticket_id}/replies",
        json={"message": "Here is transaction reference UPI-9876543210", "is_waiting_for_member": False},
        headers=member_headers
    )
    assert member_reply.status_code == 201

    db_session.refresh(t_paused)
    assert t_paused.tat_paused_at is None
    assert t_paused.total_paused_seconds >= 120
    due_after = t_paused.due_at.replace(tzinfo=timezone.utc) if t_paused.due_at.tzinfo is None else t_paused.due_at
    assert due_after > due_before

def test_priority_change_unpaused_ticket(client, member_headers, agent_headers, db_session):
    created = client.post(
        "/api/tickets",
        json={"category_id": 3, "subject": "Profile update", "description": "Medium priority inquiry"},
        headers=member_headers
    ).json()
    ticket_id = created["id"]
    assert created["priority"] == "MEDIUM"

    # Agent updates priority from MEDIUM (24h) to HIGH (4h) with mandatory reason
    p_resp = client.patch(
        f"/api/tickets/{ticket_id}/priority",
        json={"priority": "HIGH", "reason": "Participant project deadline expires in 2 hours"},
        headers=agent_headers
    )
    assert p_resp.status_code == 200
    updated = p_resp.json()
    assert updated["priority"] == "HIGH"

def test_priority_change_on_paused_ticket_preserves_pause_state(client, member_headers, agent_headers, db_session):
    created = client.post(
        "/api/tickets",
        json={"category_id": 3, "subject": "Paused priority test", "description": "Initially medium priority"},
        headers=member_headers
    ).json()
    ticket_id = created["id"]

    # Pause ticket
    client.post(
        f"/api/tickets/{ticket_id}/replies",
        json={"message": "Waiting for ID proof", "is_waiting_for_member": True},
        headers=agent_headers
    )

    t = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
    assert t.tat_paused_at is not None
    original_pause_time = t.tat_paused_at

    # Change priority while paused
    p_resp = client.patch(
        f"/api/tickets/{ticket_id}/priority",
        json={"priority": "HIGH", "reason": "Urgent study cohort closing today"},
        headers=agent_headers
    )
    assert p_resp.status_code == 200
    db_session.refresh(t)
    assert t.priority == "HIGH"
    # tat_paused_at must remain preserved to avoid counting pause twice
    assert t.tat_paused_at is not None

def test_overdue_ticket_pause_resumes_without_extra_sla(client, member_headers, agent_headers, db_session):
    created = client.post(
        "/api/tickets",
        json={"category_id": 1, "subject": "Overdue pause boundary", "description": "Already past SLA"},
        headers=member_headers
    ).json()
    ticket_id = created["id"]

    t = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
    now = datetime.now(timezone.utc)
    # Set ticket as already overdue
    t.due_at = now - timedelta(hours=2)
    db_session.commit()

    # Agent pauses
    client.post(
        f"/api/tickets/{ticket_id}/replies",
        json={"message": "Need additional documents", "is_waiting_for_member": True},
        headers=agent_headers
    )

    # Member replies
    client.post(
        f"/api/tickets/{ticket_id}/replies",
        json={"message": "Documents attached", "is_waiting_for_member": False},
        headers=member_headers
    )

    db_session.refresh(t)
    # Resumption must leave it in overdue / ESCALATED status
    assert t.status == "ESCALATED"

def test_priority_change_requires_reason(client, member_headers, agent_headers):
    created = client.post(
        "/api/tickets",
        json={"category_id": 3, "subject": "Profile update 2", "description": "Medium priority inquiry"},
        headers=member_headers
    ).json()
    ticket_id = created["id"]

    # Short reason (<5 chars) rejected
    p_resp = client.patch(
        f"/api/tickets/{ticket_id}/priority",
        json={"priority": "HIGH", "reason": "no"},
        headers=agent_headers
    )
    assert p_resp.status_code == 422

def test_automatic_escalation_scanner(client, member_headers, admin_headers, db_session):
    created = client.post(
        "/api/tickets",
        json={"category_id": 1, "subject": "Overdue Payment", "description": "Will breach SLA deadline"},
        headers=member_headers
    ).json()
    ticket_id = created["id"]

    # Artificially set due_at into the past (1 hour ago)
    t = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
    t.due_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    # Trigger escalation scan
    escalated = check_and_escalate_overdue_tickets(db_session)
    assert len(escalated) >= 1
    assert any(x.id == ticket_id for x in escalated)

    db_session.refresh(t)
    assert t.status == "ESCALATED"

    # Support Head reviews and returns escalated ticket to active handling
    reassign_resp = client.post(
        f"/api/tickets/{ticket_id}/reassign-escalated",
        json={"new_agent_id": 2, "directive_reason": "Escalated payment ticket reassigned to Senior Agent for immediate clearing"},
        headers=admin_headers
    )
    assert reassign_resp.status_code == 200
    resumed = reassign_resp.json()
    assert resumed["status"] == "IN_PROGRESS"
    assert resumed["assigned_agent_id"] == 2

def test_audit_history_immutability_trigger(db_session):
    """Verify that SQLite triggers reject UPDATE and DELETE on TICKET_HISTORY."""
    # Ensure triggers exist
    from sqlalchemy import text
    db_session.execute(text("""
        CREATE TRIGGER IF NOT EXISTS trg_test_history_no_update
        BEFORE UPDATE ON ticket_history
        BEGIN
            SELECT RAISE(ABORT, 'TICKET_HISTORY is an immutable audit log: updates are strictly prohibited.');
        END;
    """))
    db_session.execute(text("""
        CREATE TRIGGER IF NOT EXISTS trg_test_history_no_delete
        BEFORE DELETE ON ticket_history
        BEGIN
            SELECT RAISE(ABORT, 'TICKET_HISTORY is an immutable audit log: deletions are strictly prohibited.');
        END;
    """))
    db_session.commit()

    # Create dummy ticket and history record
    ticket = Ticket(
        ticket_number="TKT-IMMUTABLE",
        member_id=3,
        category_id=1,
        subject="Audit Immutability Test",
        description="Testing tamper protection triggers",
        priority="HIGH",
        status="OPEN",
        due_at=datetime.now(timezone.utc) + timedelta(hours=4)
    )
    db_session.add(ticket)
    db_session.flush()

    h = TicketHistory(
        ticket_id=ticket.id,
        actor_id=3,
        action="CREATED",
        new_value="OPEN",
        reason="Initial creation"
    )
    db_session.add(h)
    db_session.commit()

    # Attempt direct SQL UPDATE on history record -> ABORT
    with pytest.raises((IntegrityError, OperationalError)) as exc_update:
        db_session.execute(text(f"UPDATE ticket_history SET reason = 'Tampered' WHERE id = {h.id}"))
        db_session.commit()
    assert "TICKET_HISTORY is an immutable audit log: updates are strictly prohibited" in str(exc_update.value)
    db_session.rollback()

    # Attempt direct SQL DELETE on history record -> ABORT
    with pytest.raises((IntegrityError, OperationalError)) as exc_delete:
        db_session.execute(text(f"DELETE FROM ticket_history WHERE id = {h.id}"))
        db_session.commit()
    assert "TICKET_HISTORY is an immutable audit log: deletions are strictly prohibited" in str(exc_delete.value)
    db_session.rollback()

def test_auto_close_resolved_tickets(client, member_headers, agent_headers, db_session):
    """Verify that resolved tickets exceeding auto_close_days are transitioned to CLOSED with actor_id=None."""
    from backend.app.services.sla_service import run_periodic_maintenance

    # Create and resolve ticket
    created = client.post(
        "/api/tickets",
        json={"category_id": 1, "subject": "Auto-close test ticket", "description": "Testing auto-close maintenance"},
        headers=member_headers
    ).json()
    ticket_id = created["id"]

    resolve_resp = client.post(
        f"/api/tickets/{ticket_id}/resolve",
        json={"resolution_note": "Issue sorted out"},
        headers=agent_headers
    )
    assert resolve_resp.status_code == 200

    t = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
    assert t.status == "RESOLVED"

    # Simulate resolved_at 8 days ago (exceeding default 7-day auto-close threshold)
    t.resolved_at = datetime.now(timezone.utc) - timedelta(days=8)
    db_session.commit()

    # Run periodic maintenance
    result = run_periodic_maintenance(db_session)
    assert result["closed_count"] >= 1
    assert ticket_id in result["closed_tickets"]

    db_session.refresh(t)
    assert t.status == "CLOSED"
    assert t.closed_at is not None

    # Verify audit history logged with actor_id=None
    history_entry = (
        db_session.query(TicketHistory)
        .filter(TicketHistory.ticket_id == ticket_id, TicketHistory.action == "CLOSED")
        .first()
    )
    assert history_entry is not None
    assert history_entry.actor_id is None

