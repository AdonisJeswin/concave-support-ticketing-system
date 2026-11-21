# Concave Support Ticketing System

## 1. Project Overview

Concave Insights conducts high-velocity consumer research studies operating in strict 15-day project cycles, where survey participants receive compensation upon completion but face a 3-month cooling period between studies. Support inquiries regarding payment disbursements, survey glitches, profile updates, and study eligibility were historically handled across fragmented phone calls and WhatsApp chats, resulting in lost inquiries and lack of resolution accountability. This project establishes a centralized support ticketing system providing automated SLA tracking, 24/7 continuous Turnaround Time (TAT) computation, automatic supervisory escalations, pause-and-resume workflows, and complete audit logging across Members, Support Agents, and the Support Head.

---

## 2. Tech Stack

- **Backend**: Python with FastAPI (RESTful API, asynchronous request handling, background task scheduling)
- **Frontend**: React with Vite (Single Page Application, responsive component architecture)
- **Database**: SQLite (Relational data storage with lightweight, zero-configuration local portability)
- **ORM**: SQLAlchemy (Object-relational mapping, declarative schema, transaction management)
- **Styling**: Tailwind CSS (Utility-first responsive design and consistent UI tokens)
- **Version Control**: Git and GitHub

---

## 3. Setup and Run

Application implementation is planned for subsequent milestones. Complete setup, environment configuration, dependency installation, and execution instructions for both backend and frontend services will be documented here as development commences. No execution commands are currently provided to avoid running an application that has not yet been built.

---

## 4. Demo Logins and Test Data

Pre-seeded demo user accounts representing all three operational roles (Member, Support Agent, and Support Head / Admin), along with comprehensive seed datasets covering sample research projects and tickets, will be populated during the implementation phase.

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

### Planned — Application Implementation

- Member, Agent, and Support Head dashboards.
- Ticket creation, assignment, messaging, and resolution.
- Automated TAT monitoring and escalation.
- Waiting-for-Member pause/resume functionality.
- Controlled ticket reopening and automatic closure.
- Configurable SLA policies.
- Dashboard analytics and reporting.

---

## 6. Database Design

Complete specifications for data persistence, entity relationships, integrity constraints, and query indexes are documented in the design artifacts:

- [Database Entity Relationship Document (ERD)](design/database-erd.md)
- [User Flow and System Workflows](design/user-flow.md)

---

## 7. API Endpoints

Complete API endpoint specifications (request schemas, response models, query parameters, and error status codes) will be documented as the FastAPI backend routing and controller layers are implemented.

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
- **Active-Time Recalculation**: Remaining SLA is computed based on active consumed time ($t_{\text{active}}$), properly distinguishing unpaused tickets from currently paused tickets to prevent double-counting pause intervals.

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
- Application implementation has not started yet. This repository currently contains the completed system architecture, entity relationships, and workflow documentation for the Day 2 assessment deliverable.

### Planned Next Steps (Implementation Phase)
1. Initialize FastAPI backend structure with dependency management.
2. Implement SQLAlchemy models matching the defined schema in `design/database-erd.md`.
3. Set up Alembic migrations and database seed script with mock users, categories, and initial settings.
4. Build REST API endpoints for user authentication, ticket lifecycle, thread messages, and administrative controls.
5. Implement background scheduler for continuous SLA tracking and automatic overdue escalations.
6. Scaffold React + Vite frontend with Tailwind CSS.
7. Construct role-specific views: Member Dashboard, Agent Support Queue, and Support Head Analytics.
8. Validate end-to-end user flows including TAT pause/resume and reopening validation rules.
