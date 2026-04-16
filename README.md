[Uploading Sample_report.pdf…]()
# Boswell Health Performance Intelligence Engine

## Overview
A full-stack SaaS platform designed to analyze home health agency performance and generate decision-grade intelligence reports.

## Core Features
- Multi-tenant authentication system
- Agency record management
- Async report generation (Celery + Redis)
- PDF & Markdown export
- Risk scoring + reimbursement impact modeling
- CMS benchmarking integration (CSV-based)
- Operational dashboard foundation
- SaaS monetization layer (usage limits)

## Tech Stack
Backend:
- FastAPI
- SQLAlchemy
- Celery + Redis

Frontend:
- React (Vite)
- Axios

Deployment:
- Render (Web + Worker + Redis + Static Site)

## Intelligence Capabilities
- Risk Score (0–100)
- Risk Tier (Low / Moderate / High)
- Estimated reimbursement impact
- CMS benchmark comparison
- Actionable recommendations

## Project Structure
- app/ ? backend services
- frontend/ ? React UI
- reports/ ? generated outputs
- data/ ? CMS datasets

## Current Status
MVP Complete:
- End-to-end working system
- Cloud deployment ready
- Decision intelligence active

## Next Steps
- Live CMS data ingestion
- Postgres migration
- Stripe billing integration
- Advanced dashboards
- Client onboarding flow%PDF-1.7


## Author
Boswell Consulting Group
