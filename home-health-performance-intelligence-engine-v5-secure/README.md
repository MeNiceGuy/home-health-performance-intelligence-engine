# Home Health Performance Intelligence Engine

AI decision-intelligence platform for home health agencies to analyze HHVBP performance, benchmark peers, simulate reimbursement impact, flag compliance risk, and turn findings into action workflows.

## Live demo
After deployment, use these links at the very top of your GitHub repo:

- **Analyst workspace:** `https://YOUR-APP.onrender.com`
- **Client demo:** `https://YOUR-APP.onrender.com/client-demo`
- **Login:** `https://YOUR-APP.onrender.com/login`

## Why recruiters and clients should care
This project is built to show end-to-end product thinking:
- ingest home health operational data
- evaluate reimbursement and quality risk
- benchmark performance against peers
- simulate improvement scenarios
- generate workflow tasks and executive-ready outputs

It is positioned as a **decision intelligence layer** for home health operations, not as a full EMR replacement.

## What this project is
This is a secure, functional prototype for a home health analytics and decision-support product. It demonstrates:
- healthcare data intake
- EMR/FHIR-style ingestion
- HHVBP-oriented scoring
- compliance-aware analytics
- workflow automation
- client-ready demo presentation
- security hardening for a multi-user web application

## Core capabilities
- Structured intake and agency profile analysis
- CMS enrichment hooks and HHVBP-oriented scoring
- Compliance risk checks and alert generation
- Peer-benchmark deltas and executive summaries
- Trend forecasting (30, 60, and 90 day views)
- What-if simulation for measure improvement
- Workflow task generation from alerts and risks
- Audit history and saved agency records
- PDF and Markdown reporting
- Client-ready demo experience at `/client-demo`
- Secure login and role-aware workspace controls

## Client-ready demo flow
Use this sequence when showing the product to recruiters, hiring managers, agencies, or consultants:
1. Open `/client-demo`
2. Select a scenario
3. Show reimbursement risk, peer position, and compliance flags
4. Run a what-if simulation
5. Show recommended workflow actions
6. Explain how the tool converts raw operational data into decision support

That flow makes the value obvious in under two minutes.

## Demo credentials
The application creates a bootstrap admin account on first run.

### Local run
If you do not set bootstrap admin environment variables, the credentials are written to:
- `data/bootstrap_admin.txt`

### Hosted run
For a hosted demo, set these Render environment variables:
- `BOOTSTRAP_ADMIN_USERNAME`
- `BOOTSTRAP_ADMIN_PASSWORD`

## Deploy to Render
This repo includes a ready-to-use `render.yaml` file.

### Deploy steps
1. Push this repository to GitHub
2. Create a new **Web Service** on Render
3. Connect your GitHub repo
4. Render will detect the `render.yaml`
5. Add the environment variables listed below
6. Deploy

### Required environment variables
- `APP_ENV=production`
- `SESSION_SECRET_KEY=generate-a-long-random-value`
- `BOOTSTRAP_ADMIN_USERNAME=admin`
- `BOOTSTRAP_ADMIN_PASSWORD=choose-a-strong-password`
- `MAX_UPLOAD_BYTES=5242880`
- `OPENAI_API_KEY` (optional)

A full deployment guide is included in `docs/deploy_render.md`.

## Requirements
To run this project locally, you need:
- Python 3.10 or newer
- `pip`
- a virtual environment (recommended)
- internet access for live CMS lookups
- optional `OPENAI_API_KEY` for AI-enhanced report generation

### Recommended local setup
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

Open:
- Analyst workspace: `http://127.0.0.1:8000`
- Client demo: `http://127.0.0.1:8000/client-demo`
- Login: `http://127.0.0.1:8000/login`

## Data and integration notes
This system is designed to work with real-world healthcare data inputs, including:
- CMS datasets and HHVBP-related performance inputs
- EMR exports in CSV format
- FHIR-style bundles in JSON format

For this portfolio build:
- Sample datasets are included in the `samples/` directory
- EMR CSV import is functional and aggregates row-level data into agency metrics
- FHIR bundle import is functional for demo-level Encounter and Observation ingestion
- Live vendor integrations such as Axxess, Homecare Homebase, AlayaCare, MatrixCare, or WellSky are not included
- Live production EMR integrations would require vendor API credentials, field mapping, and customer-specific access

This is intentional. The project is positioned as an analytics and decision-support layer rather than a full EMR.

## Security model
This version includes a strong security baseline:
- persisted user accounts with password hashing
- bootstrap admin creation for plug-and-play local use
- role checks for admin and analyst functions
- CSRF protection for browser-based state-changing requests
- security headers middleware
- in-memory rate limiting by IP and path
- encrypted storage for protected JSON payloads in SQLite
- upload validation for type and size
- audit logging for login, logout, imports, reports, simulations, and record changes

### Security note
This is a strong portfolio and prototype baseline, not a formal certification claim. Production use would still require secure hosting, key rotation, monitoring, backup strategy, vendor contracts, and organizational controls.

## Demo mode
A client-ready walkthrough is available at `/client-demo`.

The demo simulates:
- reimbursement risk scoring
- benchmark comparison
- compliance flags
- forecast and trend direction
- workflow task generation
- what-if improvement modeling

This allows stakeholders to experience the value of the product without requiring live customer data.

## Sample files for testing
Use these files in `samples/` for the fastest first run:
- `agency_demo.json`
- `emr_export_demo.csv`
- `fhir_bundle_demo.json`

## EMR import demo
Upload either sample file with:
- `POST /api/emr/upload`

Required multipart form-data fields:
- `agency_name`
- `source_type` = `csv` or `fhir`
- `file`

## API and workflow highlights
Key routes include:
- `GET /` analyst workspace
- `GET /client-demo` client-facing demo experience
- `GET /login` login page
- `POST /api/intake` structured agency intake
- `POST /api/emr/upload` EMR/FHIR ingestion
- `GET /api/dashboard` dashboard summary data
- `POST /api/simulate` what-if improvement simulation
- `GET /api/compliance/check` compliance risk checks
- workflow, task, record, and audit endpoints in the analyst workspace

## Business value
This project is designed for:
- home health agency leaders
- consultants and operators
- strategy and innovation teams
- analytics and compliance stakeholders

Primary outcomes it supports:
- identify reimbursement downside risk under HHVBP
- highlight measure-level performance gaps
- prioritize improvement actions
- create a repeatable decision workflow from data to execution

## Production considerations
This repository is a portfolio-grade, functional prototype. A production deployment would typically add:
- managed database services
- background jobs for larger imports
- vendor-authenticated EMR integrations
- cloud monitoring and alerting
- backup and recovery policies
- HIPAA-aligned infrastructure and operational controls
- formal audit, security, and compliance readiness work

## What users need to set up to actually run it
A user can run the project locally today if they have:
- Python and pip installed
- dependencies from `requirements.txt`
- sample files from the `samples/` folder
- optional API keys for AI-enhanced report output

A user would need additional enterprise setup only if they want:
- live EMR vendor integrations
- organization-specific production data pipelines
- production security controls and audit readiness
- hosted multi-user deployment

## Why this matters
Most portfolio projects stop at reporting. This one is built to support the full loop:

**collect data -> score performance -> flag risk -> simulate changes -> generate tasks -> support decisions**

That is the competitive lane for a modern healthcare analytics product.
