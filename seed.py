"""
Seed script for Concave Support Ticketing System.
Populates standard mock users, inquiry categories, SLA turnaround settings,
system parameters, and realistic test tickets spanning all lifecycle states.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from backend.app.database import init_db, SessionLocal
from backend.app.models import (
    User, Category, Ticket, Reply, TicketHistory, TATSetting, SystemSetting
)
from backend.app.services.auth_service import hash_password
from backend.app.services.audit_service import log_ticket_action

def seed_database():
    print("Initializing database schema and triggers...")
    init_db()
    db = SessionLocal()

    try:
        print("Seeding Users...")
        # 1. Seed Users
        users_data = [
            {
                "name": "Sarah Jenkins (Support Head)",
                "email": "admin@concave.com",
                "password": "password123",
                "role": "SUPPORT_HEAD"
            },
            {
                "name": "Alex Rivera (Support Agent)",
                "email": "agent1@concave.com",
                "password": "password123",
                "role": "AGENT"
            },
            {
                "name": "David Chen (Support Agent)",
                "email": "agent2@concave.com",
                "password": "password123",
                "role": "AGENT"
            },
            {
                "name": "Adonis Jeswin (Participant)",
                "email": "member1@surveyuser.com",
                "password": "password123",
                "role": "MEMBER"
            },
            {
                "name": "Priya Sharma (Participant)",
                "email": "member2@surveyuser.com",
                "password": "password123",
                "role": "MEMBER"
            },
        ]

        users = {}
        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(
                    name=u["name"],
                    email=u["email"],
                    password_hash=hash_password(u["password"]),
                    role=u["role"],
                    created_at=datetime.now(timezone.utc) - timedelta(days=30)
                )
                db.add(user)
                db.flush()
                users[u["email"]] = user
            else:
                users[u["email"]] = existing

        admin_user = users["admin@concave.com"]
        agent1 = users["agent1@concave.com"]
        agent2 = users["agent2@concave.com"]
        member1 = users["member1@surveyuser.com"]
        member2 = users["member2@surveyuser.com"]

        print("Seeding Categories with approved priority mappings...")
        # 2. Seed Categories
        categories_data = [
            {"name": "Payment", "default_priority": "HIGH"},
            {"name": "Survey Issue", "default_priority": "HIGH"},
            {"name": "Profile Change", "default_priority": "MEDIUM"},
            {"name": "Eligibility", "default_priority": "MEDIUM"},
            {"name": "Other", "default_priority": "LOW"},
        ]

        categories = {}
        for cat in categories_data:
            existing = db.query(Category).filter(Category.name == cat["name"]).first()
            if not existing:
                category = Category(
                    name=cat["name"],
                    default_priority=cat["default_priority"],
                    is_active=True
                )
                db.add(category)
                db.flush()
                categories[cat["name"]] = category
            else:
                categories[cat["name"]] = existing

        print("Seeding TAT Settings...")
        # 3. Seed TAT Settings
        tat_data = [
            {"priority": "HIGH", "hours": 4},
            {"priority": "MEDIUM", "hours": 24},
            {"priority": "LOW", "hours": 48},
        ]
        for t in tat_data:
            existing = db.query(TATSetting).filter(TATSetting.priority == t["priority"]).first()
            if not existing:
                setting = TATSetting(
                    priority=t["priority"],
                    tat_hours=t["hours"],
                    updated_by=admin_user.id,
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(setting)

        print("Seeding System Settings singleton...")
        # 4. Seed System Settings (row id=1)
        sys_setting = db.query(SystemSetting).filter(SystemSetting.id == 1).first()
        if not sys_setting:
            sys_setting = SystemSetting(
                id=1,
                reopen_window_days=7,
                max_reopen_attempts=2,
                auto_close_days=7,
                updated_by=admin_user.id,
                updated_at=datetime.now(timezone.utc)
            )
            db.add(sys_setting)

        db.commit()

        print("Seeding realistic sample tickets across all lifecycle states...")
        now = datetime.now(timezone.utc)

        # 5. Seed Demonstration Tickets if table is empty
        if db.query(Ticket).count() == 0:
            sample_tickets = [
                # Ticket 1: OPEN (Payment issue)
                {
                    "number": "TKT-0001",
                    "member": member1,
                    "category": categories["Payment"],
                    "agent": None,
                    "subject": "Missing study stipend for Project Alpha-15",
                    "description": "Completed all 15 modules of Project Alpha on Friday, but incentive has not credited to UPI.",
                    "priority": "HIGH",
                    "status": "OPEN",
                    "created_at": now - timedelta(hours=1),
                    "due_at": now + timedelta(hours=3),
                    "reopen_count": 0,
                    "paused_at": None,
                    "total_paused": 0,
                    "resolved_at": None,
                    "closed_at": None
                },
                # Ticket 2: IN_PROGRESS (Survey crash)
                {
                    "number": "TKT-0002",
                    "member": member2,
                    "category": categories["Survey Issue"],
                    "agent": agent1,
                    "subject": "Screen freezing on Q18 of consumer electronics study",
                    "description": "Every time I click Next on page 4, error 504 gateway timeout appears.",
                    "priority": "HIGH",
                    "status": "IN_PROGRESS",
                    "created_at": now - timedelta(hours=2),
                    "due_at": now + timedelta(hours=2),
                    "reopen_count": 0,
                    "paused_at": None,
                    "total_paused": 0,
                    "resolved_at": None,
                    "closed_at": None
                },
                # Ticket 3: IN_PROGRESS with TAT PAUSED (Waiting for member)
                {
                    "number": "TKT-0003",
                    "member": member1,
                    "category": categories["Profile Change"],
                    "agent": agent2,
                    "subject": "Request to update verified payout phone number",
                    "description": "Changed my primary mobile number, need to link new number to survey account.",
                    "priority": "MEDIUM",
                    "status": "IN_PROGRESS",
                    "created_at": now - timedelta(hours=8),
                    "due_at": now + timedelta(hours=16),
                    "reopen_count": 0,
                    "paused_at": now - timedelta(hours=2),
                    "total_paused": 0,
                    "resolved_at": None,
                    "closed_at": None
                },
                # Ticket 4: ESCALATED (Overdue payment ticket)
                {
                    "number": "TKT-0004",
                    "member": member2,
                    "category": categories["Payment"],
                    "agent": agent1,
                    "subject": "Referral bonus not credited for 3 enrolled participants",
                    "description": "Referred three verified colleagues who finished the 15-day study, bonus missing.",
                    "priority": "HIGH",
                    "status": "ESCALATED",
                    "created_at": now - timedelta(hours=6),
                    "due_at": now - timedelta(hours=2),  # Past due!
                    "reopen_count": 0,
                    "paused_at": None,
                    "total_paused": 0,
                    "resolved_at": None,
                    "closed_at": None
                },
                # Ticket 5: RESOLVED (Eligibility query)
                {
                    "number": "TKT-0005",
                    "member": member1,
                    "category": categories["Eligibility"],
                    "agent": agent2,
                    "subject": "When does my 3-month cooling off period conclude?",
                    "description": "Participated in October study cycle, want to know if I am eligible for the December cycle.",
                    "priority": "MEDIUM",
                    "status": "RESOLVED",
                    "created_at": now - timedelta(days=2),
                    "due_at": now - timedelta(days=1),
                    "reopen_count": 0,
                    "paused_at": None,
                    "total_paused": 0,
                    "resolved_at": now - timedelta(hours=5),
                    "closed_at": None
                },
                # Ticket 6: CLOSED (General query confirmed closed by member)
                {
                    "number": "TKT-0006",
                    "member": member2,
                    "category": categories["Other"],
                    "agent": agent1,
                    "subject": "Confirmation of participation certificate",
                    "description": "Need receipt certificate for academic research panel record.",
                    "priority": "LOW",
                    "status": "CLOSED",
                    "created_at": now - timedelta(days=5),
                    "due_at": now - timedelta(days=3),
                    "reopen_count": 0,
                    "paused_at": None,
                    "total_paused": 0,
                    "resolved_at": now - timedelta(days=3),
                    "closed_at": now - timedelta(days=2)
                },
                # Ticket 7: REOPENED (Survey Issue reoccurred)
                {
                    "number": "TKT-0007",
                    "member": member1,
                    "category": categories["Survey Issue"],
                    "agent": agent1,
                    "subject": "Mobile survey session keeps expiring prematurely",
                    "description": "Agent marked resolved earlier but the session still crashes on iOS Safari.",
                    "priority": "HIGH",
                    "status": "REOPENED",
                    "created_at": now - timedelta(days=1),
                    "due_at": now + timedelta(hours=3),
                    "reopen_count": 1,
                    "paused_at": None,
                    "total_paused": 0,
                    "resolved_at": now - timedelta(hours=10),
                    "closed_at": None
                }
            ]

            for st in sample_tickets:
                ticket = Ticket(
                    ticket_number=st["number"],
                    member_id=st["member"].id,
                    category_id=st["category"].id,
                    assigned_agent_id=st["agent"].id if st["agent"] else None,
                    subject=st["subject"],
                    description=st["description"],
                    priority=st["priority"],
                    status=st["status"],
                    created_at=st["created_at"],
                    due_at=st["due_at"],
                    resolved_at=st["resolved_at"],
                    closed_at=st["closed_at"],
                    reopen_count=st["reopen_count"],
                    tat_paused_at=st["paused_at"],
                    total_paused_seconds=st["total_paused"]
                )
                db.add(ticket)
                db.flush()

                # Initial history
                log_ticket_action(
                    db=db,
                    ticket_id=ticket.id,
                    action="CREATED",
                    actor_id=st["member"].id,
                    new_value=st["status"],
                    reason=f"Created in category '{st['category'].name}'"
                )

                # Add sample replies and status events
                if st["number"] == "TKT-0002":
                    r1 = Reply(
                        ticket_id=ticket.id,
                        sender_id=agent1.id,
                        message="Hello Priya, I am investigating the gateway timeout on module 4. Could you confirm if you are on mobile or desktop?",
                        created_at=now - timedelta(hours=1, minutes=30)
                    )
                    db.add(r1)

                if st["number"] == "TKT-0003":
                    r1 = Reply(
                        ticket_id=ticket.id,
                        sender_id=agent2.id,
                        message="Please upload a photo of your government ID or utility bill to verify account ownership before we update the phone number.",
                        created_at=now - timedelta(hours=2)
                    )
                    db.add(r1)
                    log_ticket_action(
                        db=db,
                        ticket_id=ticket.id,
                        action="TAT_PAUSE",
                        actor_id=agent2.id,
                        reason="Agent requested verification documents; SLA clock paused"
                    )

                if st["number"] == "TKT-0004":
                    log_ticket_action(
                        db=db,
                        ticket_id=ticket.id,
                        action="ESCALATED",
                        actor_id=None,
                        old_value="IN_PROGRESS",
                        new_value="ESCALATED",
                        reason="Resolution deadline exceeded active SLA threshold"
                    )

                if st["number"] == "TKT-0005":
                    r1 = Reply(
                        ticket_id=ticket.id,
                        sender_id=agent2.id,
                        message="Hi Adonis, your 3-month cooling period for the October study concludes on January 15th. You will automatically receive survey invites after that date.",
                        created_at=now - timedelta(hours=5)
                    )
                    db.add(r1)
                    log_ticket_action(
                        db=db,
                        ticket_id=ticket.id,
                        action="RESOLVED",
                        actor_id=agent2.id,
                        old_value="IN_PROGRESS",
                        new_value="RESOLVED",
                        reason="Provided exact cooling-off eligibility date to participant"
                    )

                if st["number"] == "TKT-0006":
                    log_ticket_action(
                        db=db,
                        ticket_id=ticket.id,
                        action="RESOLVED",
                        actor_id=agent1.id,
                        old_value="IN_PROGRESS",
                        new_value="RESOLVED",
                        reason="Certificate PDF generated and dispatched via email"
                    )
                    log_ticket_action(
                        db=db,
                        ticket_id=ticket.id,
                        action="CLOSED",
                        actor_id=member2.id,
                        old_value="RESOLVED",
                        new_value="CLOSED",
                        reason="Member confirmed satisfactory resolution"
                    )

                if st["number"] == "TKT-0007":
                    log_ticket_action(
                        db=db,
                        ticket_id=ticket.id,
                        action="RESOLVED",
                        actor_id=agent1.id,
                        old_value="IN_PROGRESS",
                        new_value="RESOLVED",
                        reason="Cache flush applied"
                    )
                    r_reopen = Reply(
                        ticket_id=ticket.id,
                        sender_id=member1.id,
                        message="The issue is still occurring when loading the survey on iOS Safari 17.2.",
                        created_at=now - timedelta(hours=2)
                    )
                    db.add(r_reopen)
                    log_ticket_action(
                        db=db,
                        ticket_id=ticket.id,
                        action="REOPENED",
                        actor_id=member1.id,
                        old_value="RESOLVED",
                        new_value="REOPENED",
                        reason="Attempt 1/2: Issue still occurring on iOS Safari 17.2"
                    )

            db.commit()
            print("Successfully seeded 7 sample tickets spanning OPEN, IN_PROGRESS, PAUSED, ESCALATED, RESOLVED, CLOSED, and REOPENED states.")

        print("\n=== Seeding Complete ===")
        print("Demo Accounts:")
        print("  Support Head: admin@concave.com / password123")
        print("  Support Agent 1: agent1@concave.com / password123")
        print("  Support Agent 2: agent2@concave.com / password123")
        print("  Member 1: member1@surveyuser.com / password123")
        print("  Member 2: member2@surveyuser.com / password123")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
