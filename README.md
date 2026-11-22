# Concave Support Ticketing System

## 1. Project Overview

Concave Insights conducts high-velocity consumer research studies operating in strict 15-day project cycles, where survey participants receive compensation upon completion but face a 3-month cooling period between studies. Support inquiries regarding payment disbursements, survey glitches, profile updates, and study eligibility were historically handled across fragmented phone calls and WhatsApp chats, resulting in lost inquiries and lack of resolution accountability. This project establishes a centralized support ticketing system providing automated SLA tracking, 24/7 continuous Turnaround Time (TAT) computation, automatic supervisory escalations, pause-and-resume workflows, and complete audit logging across Members, Support Agents, and the Support Head.

---

## 2. Tech Stack

- **Backend**: Python with FastAPI (RESTful API, asynchronous request handling, background task scheduling)
- **Frontend**: React with Vite (Single Page Application, responsive component architecture — Planned Day 4)
- **Database**: SQLite (Relational data storage with lightweight, zero-configuration local portability)
- **ORM**: SQLAlchemy (Object-relational mapping, declarative schema, transaction management)
- **Styling**: Tailwind CSS (Utility-first responsive design and consistent UI tokens)
- **Version Control**: Git and GitHub

---

## 3. Setup and Run

### Prerequisites

- Python 3.10+ (Tested on Python 3.13)
- Git

### 1. Environment Configuration

Clone the repository and copy the environment template:

```bash
cp .env.example .env
```

### 2. Dependency Installation

Install backend dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Database Initialization & Seeding

Run the repeatable seed script to create all seven SQLite tables, apply immutability triggers, and populate demo users, inquiry categories, SLA rules, and test tickets:

```bash
python seed.py
```

### 4. Running Automated Tests

Execute the complete Pytest suite (25 automated test cases covering authentication, RBAC, ticket workflows, SLA mathematics, and audit triggers):

```bash
python -m pytest -v
```

### 5. Launching the Backend Server

Start the FastAPI application with Uvicorn:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

- **Interactive API Documentation (Swagger UI)**: `http://localhost:8000/docs`
- **Alternative Documentation (ReDoc)**: `http://localhost:8000/redoc`
- **API Health Check**: `http://localhost:8000/health`

---

## 4. Demo Logins and Test Data

The database seed script (`seed.py`) pre-configures standard test accounts across all three operational roles:

| Role | Name | Email | Password | Primary Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **SUPPORT_HEAD** | Sarah Jenkins | `admin@concave.com` | `password123` | Executive metrics, SLA hours configuration, escalated ticket review & reassignment |
| **AGENT** | Alex Rivera | `agent1@concave.com` | `password123` | Queue filtering & search, self-assignment, priority changes, TAT pause, resolution |
| **AGENT** | David Chen | `agent2@concave.com` | `password123` | Queue filtering, thread replies, verification document requests |
| **MEMBER** | Adonis Jeswin | `member1@surveyuser.com` | `password123` | Ticket creation, tracking own tickets, thread responses, reopening within 7-day window |
| **MEMBER** | Priya Sharma | `member2@surveyuser.com` | `password123` | Ticket creation, resolution confirmation, and thread communication |

*Note: For testing, the `/api/auth/mock-login` endpoint also allows instant token generation by role.*

---

## 5. Features

### Completed — Day 2 Design Deliverables

- System architecture and role-based workflows.
- Seven-table relational database schema.
- Entity Relationship Diagram.
- Ticket lifecycle and escalation workflows.
- TAT calculation and pause/resume specifications.
- Role-based permissions and validation rules.
- Audit logging and database integrity specifications.
- Technical assumptions and critical edge cases.

### Completed — Day 3 Backend Milestone

- **FastAPI Core Application**: RESTful modular API architecture with CORS, dependency injection, and centralized exception handling.
- **SQLAlchemy 7-Table Schema**: Fully implemented relational models (`USERS`, `CATEGORIES`, `TICKETS`, `REPLIES`, `TICKET_HISTORY`, `TAT_SETTINGS`, `SYSTEM_SETTINGS`) with SQLite foreign key pragma and database immutability triggers.
- **Secure Authentication & RBAC**: Passlib/bcrypt password hashing, JWT token authentication, and role-based route guards for `MEMBER`, `AGENT`, and `SUPPORT_HEAD`.
- **Approved Category-to-Priority Mapping**: Automatic default priority assignment (`Payment: HIGH`, `Survey Issue: HIGH`, `Profile Change: MEDIUM`, `Eligibility: MEDIUM`, `Other: LOW`).
- **Ticket Lifecycle Engine**: Atomic ticket number generator (`TKT-0042`), ticket creation, assignment, resolution, member confirmation closure, and 7-day/2-attempt reopening validation.
- **Continuous 24/7 SLA Service**: Turnaround time calculation without holiday/weekend pauses, overdue deadline tracking (`due_at <= CURRENT_TIMESTAMP`), and automatic supervisory escalation.
- **Stateful Waiting-for-Member TAT Pause/Resume**: Agent toggles pause on reply; member response automatically resumes the clock, preserves active remaining seconds, and prevents abuse on already overdue tickets.
- **Priority Modification with Audit Log**: Recalculates remaining SLA while preserving consumed active time (distinguishing paused from unpaused states) with mandatory audit reason.
- **Support Head Escalation Triage**: Dedicated supervisor review and reassignment workflow returning escalated tickets to active handling (`ESCALATION_RESOLVED`) while preserving overdue deadlines.
- **Executive Metrics & Policy Controls**: Real-time calculations for Total Open, Overdue, Escalated, Resolved Today, Average Resolution Time (ART), and category distributions.
- **Automated Pytest Suite**: 25 automated unit and integration tests passing with 100% success rate.
- **Repeatable Seed Data**: Automated generation of accounts, categories, and test tickets across all lifecycle states.

### Planned — Day 4 Frontend Milestone

- Member, Agent, and Support Head dashboards in React + Vite with Tailwind CSS.
- Interactive ticket queue with real-time filters and search.
- Conversation thread UI with Waiting-for-Member pause badge.
- Support Head analytics visual charts and SLA configuration panel.

---

## 6. Database Design

Complete specifications for data persistence, entity relationships, integrity constraints, and query indexes are documented in the design artifacts:

- [Database Entity Relationship Document (ERD)](design/database-erd.md)
- [User Flow and System Workflows](design/user-flow.md)

---

## 7. API Endpoints

### Authentication (`/api/auth`)
- `POST /api/auth/login`: Authenticate with email and password to receive JWT bearer token.
- `POST /api/auth/token`: OAuth2 password request form for Swagger UI testing.
- `POST /api/auth/mock-login`: Instant role-based authentication (`MEMBER`, `AGENT`, `SUPPORT_HEAD`).
- `GET /api/auth/me`: Retrieve authenticated user profile.

### Categories (`/api/categories`)
- `GET /api/categories`: Retrieve active inquiry categories with default priority mappings.

### Tickets (`/api/tickets`)
- `POST /api/tickets`: Raise a new ticket with automatic priority and initial 24/7 SLA.
- `GET /api/tickets`: Query tickets with role isolation, status/priority/category/overdue filters, and keyword search.
- `GET /api/tickets/{id}`: Retrieve detailed ticket view with conversation thread and audit history.
- `POST /api/tickets/{id}/replies`: Post thread reply with optional Waiting-for-Member TAT pause flag.
- `PATCH /api/tickets/{id}/assign`: Assign or self-claim an ordinary ticket.
- `PATCH /api/tickets/{id}/priority`: Update priority with mandatory explanation and SLA recalculation.
- `POST /api/tickets/{id}/resolve`: Mark ticket as resolved with resolution summary note.
- `POST /api/tickets/{id}/close`: Member confirms satisfactory resolution and permanently closes ticket.
- `POST /api/tickets/{id}/reopen`: Member reopens ticket within 7-day window and maximum 2 attempts limit.
- `POST /api/tickets/{id}/reassign-escalated`: Support Head reviews and returns escalated ticket to active handling.

### Admin & SLA Configuration (`/api/admin`)
- `GET /api/admin/metrics`: Executive KPI metrics (Open, Overdue, Escalated, Resolved Today, ART, Categories).
- `GET /api/admin/tat-settings`: List configured resolution hours per priority level.
- `PUT /api/admin/tat-settings/{priority}`: Update SLA turnaround hours for a priority level.
- `GET /api/admin/system-settings`: Retrieve global reopening and auto-close parameters.
- `PUT /api/admin/system-settings`: Update global system configuration.
- `POST /api/admin/run-escalation-check`: Trigger background overdue SLA escalation scanner.

---

## 8. Assumptions and Decisions

### A. TAT Calculation

- **Decision**: Turnaround Time (TAT) runs continuously, 24 hours a day, 7 days a week, including weekends and public holidays.
- **Rationale**: Market research cycles at Concave Insights operate on rigid 15-day timelines without pauses for non-working days; participant inquiries must be addressed within continuous wall-clock windows.
- **Example**: A High-priority ticket created at 11:00 PM on a Saturday with a 4-hour TAT becomes overdue and escalates at 3:00 AM on Sunday.

### B. Waiting for Member (TAT Pause)

- **Decision**: TAT pauses when a support agent marks a response with the "Waiting for Member" flag requesting additional clarification. The clock resumes automatically when the member submits a reply.
- **Rationale**: Agents must not be penalized for resolution delays caused by participants taking days to upload verification documents, transaction IDs, or screenshots.
- **Preservation Rule**: The exact remaining resolution time before the deadline is preserved to the second and added to the resumption timestamp.
- **Overdue Boundary**: If a ticket was already overdue before pausing (`due_at <= CURRENT_TIMESTAMP`), pausing freezes active overdue accrual, but resumption grants no additional SLA time and immediately leaves the ticket in overdue/escalated status.

### C. Default Priority Mapping and Recalculation

- **Decision**: Every ticket category maps to a default priority upon creation:
  - **Payment**: `HIGH` (Incentives and payouts directly impact member retention and trust)
  - **Profile Change**: `MEDIUM` (Account detail modifications, KYC data updates)
  - **Survey Issue**: `HIGH` (Active survey crashes directly jeopardize ongoing 15-day study data)
  - **Eligibility**: `MEDIUM` (Questions regarding the 3-month cooling period or project criteria)
  - **Other**: `LOW` (General questions or feedback)
- **Override Rule**: Support agents can manually modify ticket priority with a mandatory audit reason.
- **Active-Time Recalculation**: Remaining SLA is computed based on active consumed time (`t_active`), properly distinguishing unpaused tickets from currently paused tickets to prevent double-counting pause intervals.

### D. Default TAT Durations

- **Decision**: Baseline turnaround times are configured as:
  - `HIGH`: 4 hours
  - `MEDIUM`: 24 hours
  - `LOW`: 48 hours
- **Administrative Flexibility**: The Support Head can recalibrate these durations at any time through the administrative settings panel.

### E. Reopening Policy

- **Decision**: Members may reopen a `RESOLVED` ticket within 7 calendar days of resolution.
- **Limits & Safeguards**:
  - Maximum of 2 lifetime reopen attempts per ticket to prevent perpetual resolution churn.
  - A descriptive reason explaining why the issue is not resolved is mandatory.
  - Beyond 7 days or after 2 attempts, the ticket is permanently closed, requiring a new inquiry.

### F. Automatic Escalation and De-escalation

- **Decision**: An automated background worker checks active tickets every 60 seconds using the condition `due_at <= CURRENT_TIMESTAMP`. Any non-paused, non-resolved ticket exceeding its deadline transitions immediately to `ESCALATED`.
- **Supervisory Routing**: The Support Head receives an immediate in-app dashboard notification. The system appends an automated audit record to `TICKET_HISTORY` with `actor_id = NULL` and action `ESCALATED`.
- **Return to Active Handling**: Escalated tickets return to active handling exclusively through the Support Head via action `ESCALATION_RESOLVED`. The original overdue deadline is preserved; the system does not silently grant a fresh SLA.

### G. Timezone and Timestamp Handling

- **Decision**: All database timestamps (`created_at`, `due_at`, `resolved_at`, `tat_paused_at`) are stored strictly in UTC.
- **Presentation**: Timestamps are localized on the frontend client according to the user's local timezone.

### H. Database Selection

- **Decision**: SQLite is selected as the primary database for development and demonstration.
- **Rationale**: Provides zero-configuration setup, full ACID compliance, and excellent local developer experience. SQLAlchemy abstraction allows clean migration to PostgreSQL if production deployment demands high concurrency.

---

## 9. Known Issues and Next Steps

### Current Status

- **Day 3 Backend Milestone Complete**: All backend models, API routes, RBAC permissions, SLA calculation engines, audit triggers, and test suites are implemented and validated (25/25 automated tests passing).

### Planned Next Steps (Day 4 Frontend Milestone)

1. Scaffold React frontend with Vite and Tailwind CSS.
2. Implement mock authentication and role switcher UI for demonstration.
3. Build Member Dashboard: ticket creation form, active ticket tracker, and conversation view.
4. Build Agent Support Queue: multi-parameter filtering, search, self-assignment, and resolution workflow.
5. Build Support Head Console: executive KPI cards, category breakdown charts, and SLA policy editor.
6. Implement in-app escalation feed and supervisor reassignment dialog.
7. Conduct full end-to-end user acceptance testing across frontend and backend.
8. Validate production build and prepare final assessment submission deliverables.
