# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from routes.obsidian import router as obsidian_router


import requests
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.requests import Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from services.compliance import evaluate_compliance_risks
from services.data_intake import load_intake_file, normalize_record
from services.emr_connectors import aggregate_emr_rows, parse_emr_csv, parse_fhir_bundle
from services.persistence import (
    append_audit_event,
    authenticate_user,
    bootstrap_admin,
    change_password,
    get_agency_record,
    get_user,
    list_agency_records,
    list_audit_events,
    save_agency_record,
    update_agency_record,
    save_emr_import,
    list_emr_imports,
)
from services.security import DEFAULT_RATE_LIMITER, constant_time_equal, csrf_token, derive_demo_password
from services.scoring_engine import calculate_metric_score, generate_alerts, simulate_measure_improvement
from services.trends import build_measure_trends
from services.workflow import create_task, list_tasks, update_task
from services.cms_live import build_cms_snapshot

app = FastAPI(title='Home Health Performance Intelligence Engine', version='2.2.0-secure')
app.include_router(obsidian_router)

SECRET_KEY = os.getenv('SESSION_SECRET_KEY') or os.urandom(32).hex()
APP_ENV = os.getenv('APP_ENV', 'local').lower()
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'
COOKIE_SECURE = APP_ENV in {'prod', 'production'}
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site='lax', https_only=COOKIE_SECURE, max_age=60*60*8)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / 'uploads'
REPORTS_DIR = BASE_DIR / 'reports'
STATIC_DIR = BASE_DIR / 'static'
TEMPLATES_DIR = BASE_DIR / 'templates'

for directory in [UPLOAD_DIR, REPORTS_DIR, STATIC_DIR, TEMPLATES_DIR, BASE_DIR / 'data']:
    directory.mkdir(exist_ok=True)

app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')
from jinja2 import Environment, FileSystemLoader

templates_env = Environment(loader=FileSystemLoader("templates"))
templates = Jinja2Templates(directory="templates")

CMS_TIMEOUT = 20
CMS_CATALOG_URL = 'https://data.cms.gov/data.json'
HOME_HEALTH_TITLE = 'Home Health Care Agencies'
HHVBP_TITLE = 'Expanded Home Health Value-Based Purchasing (HHVBP) Model - Agency Data'
STATE_TITLE = 'Home Health Agency Performance Data by State'



BOOTSTRAP_FILE = BASE_DIR / 'data' / 'bootstrap_admin.txt'
MAX_UPLOAD_BYTES = int(os.getenv('MAX_UPLOAD_BYTES', str(5 * 1024 * 1024)))
ALLOWED_UPLOAD_EXTENSIONS = {'.json', '.csv'}


def client_ip(request: Request) -> str:
    forwarded = request.headers.get('x-forwarded-for', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host if request.client else 'unknown'


def ensure_bootstrap_admin() -> None:
    username = os.getenv('BOOTSTRAP_ADMIN_USERNAME', 'admin').strip().lower()
    password = os.getenv('BOOTSTRAP_ADMIN_PASSWORD', '').strip()
    if not password:
        if BOOTSTRAP_FILE.exists():
            contents = BOOTSTRAP_FILE.read_text(encoding='utf-8').splitlines()
            creds = dict(line.split('=', 1) for line in contents if '=' in line)
            password = creds.get('password', '')
        if not password:
            password = derive_demo_password()
            BOOTSTRAP_FILE.write_text(f'username={username}\npassword={password}\nrole=admin\n', encoding='utf-8')
    bootstrap_admin(username, password, role='admin')


ensure_bootstrap_admin()


def ensure_csrf(request: Request) -> str:
    token = request.session.get('csrf_token')
    if not token:
        token = csrf_token()
        request.session['csrf_token'] = token
    return token


def validate_csrf(request: Request, token: str | None) -> None:
    session_token = request.session.get('csrf_token')
    if not session_token or not token or not constant_time_equal(session_token, token):
        raise HTTPException(status_code=403, detail='Invalid CSRF token.')


def current_user_from_session(request: Request) -> dict[str, Any] | None:
    username = request.session.get('user')
    if not username:
        return None
    return get_user(username)


def require_user(request: Request, roles: set[str] | None = None) -> dict[str, Any]:
    if DEMO_MODE:
        return {
            'username': 'demo_user',
            'role': 'admin',
            'is_active': True,
        }
    user = current_user_from_session(request)
    if not user or not user.get('is_active'):
        raise HTTPException(status_code=401, detail='Authentication required.')
    if roles and user.get('role') not in roles:
        raise HTTPException(status_code=403, detail='Insufficient permissions.')
    return user


def enforce_upload_policy(filename: str, size_bytes: int) -> None:
    ext = Path(filename or '').suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail='Unsupported file type.')
    if size_bytes > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail='File too large.')


@app.middleware('http')
async def security_middleware(request: Request, call_next):
    ip = client_ip(request)

    if request.url.path == "/login":
        return await call_next(request)

    if not DEFAULT_RATE_LIMITER.allow(f"{ip}:{request.url.path}"):
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

    response = await call_next(request)
    return response


DEMO_SCENARIOS = {
    'at-risk': {
        'slug': 'at-risk', 'tag': 'High urgency', 'name': 'At-Risk Agency',
        'description': 'Declining quality performance, elevated readmissions, and documentation lag.',
        'data': {
            'agency_name': 'Crescent Home Health', 'state': 'VA', 'city': 'Richmond', 'ownership_type': 'Private',
            'avg_monthly_patients': 132, 'clinicians_total': 11, 'star_rating': 2.5, 'readmission_rate': 22.0,
            'patient_satisfaction': 76.0, 'oasis_timeliness': 78.0, 'soc_delay_days': 4.0, 'visit_completion_rate': 83.0,
            'documentation_lag_hours': 56.0, 'turnover_rate': 34.0, 'open_positions': 3, 'visits_per_clinician_week': 31,
            'ehr_vendor': 'EMR export', 'evv_present': True, 'scheduling_software': 'Integrated feed', 'telehealth_present': False,
            'automation_present': False, 'monthly_revenue_range': '500K-1M', 'cost_pressure_level': 'High', 'improvement_budget': '<10K',
            'leadership_readiness': 'Moderate', 'change_resistance': 'High', 'training_infrastructure': 'Informal',
            'pain_points': ['High readmissions', 'Documentation delays'], 'notes': 'Demo scenario: at-risk agency.',
            'monthly_series': [
                {'readmission_rate': 19, 'oasis_timeliness': 84, 'patient_satisfaction': 81, 'visit_completion_rate': 88, 'documentation_lag_hours': 38},
                {'readmission_rate': 21, 'oasis_timeliness': 81, 'patient_satisfaction': 78, 'visit_completion_rate': 86, 'documentation_lag_hours': 44},
                {'readmission_rate': 22, 'oasis_timeliness': 78, 'patient_satisfaction': 76, 'visit_completion_rate': 83, 'documentation_lag_hours': 56},
            ],
            'cms_context': {}, 'scorecard': {}
        }
    },
    'improving': {
        'slug': 'improving', 'tag': 'Growth-ready', 'name': 'Improving Agency',
        'description': 'Improving quality and patient experience with manageable risk profile.',
        'data': {
            'agency_name': 'Harbor Home Health', 'state': 'VA', 'city': 'Norfolk', 'ownership_type': 'Private',
            'avg_monthly_patients': 168, 'clinicians_total': 18, 'star_rating': 4.0, 'readmission_rate': 13.0,
            'patient_satisfaction': 90.0, 'oasis_timeliness': 95.0, 'soc_delay_days': 1.0, 'visit_completion_rate': 95.0,
            'documentation_lag_hours': 12.0, 'turnover_rate': 16.0, 'open_positions': 1, 'visits_per_clinician_week': 24,
            'ehr_vendor': 'EMR export', 'evv_present': True, 'scheduling_software': 'Integrated feed', 'telehealth_present': True,
            'automation_present': True, 'monthly_revenue_range': '1M+', 'cost_pressure_level': 'Moderate', 'improvement_budget': '50K+',
            'leadership_readiness': 'High', 'change_resistance': 'Low', 'training_infrastructure': 'Structured program',
            'pain_points': ['Staff burnout'], 'notes': 'Demo scenario: improving agency.',
            'monthly_series': [
                {'readmission_rate': 15, 'oasis_timeliness': 91, 'patient_satisfaction': 87, 'visit_completion_rate': 92, 'documentation_lag_hours': 20},
                {'readmission_rate': 14, 'oasis_timeliness': 93, 'patient_satisfaction': 89, 'visit_completion_rate': 94, 'documentation_lag_hours': 16},
                {'readmission_rate': 13, 'oasis_timeliness': 95, 'patient_satisfaction': 90, 'visit_completion_rate': 95, 'documentation_lag_hours': 12},
            ],
            'cms_context': {}, 'scorecard': {}
        }
    }
}

PAIN_POINT_CHOICES = {
    'high_readmissions': 'High readmissions',
    'low_hhvbp_scores': 'Low HHVBP scores',
    'staff_burnout': 'Staff burnout',
    'scheduling_inefficiencies': 'Scheduling inefficiencies',
    'documentation_delays': 'Documentation delays',
    'poor_care_coordination': 'Poor care coordination',
    'patient_satisfaction_issues': 'Patient satisfaction issues',
}


class WorkflowTaskIn(BaseModel):
    title: str
    agency_name: str | None = None
    assigned_to: str | None = None
    priority: str = 'medium'
    status: str = 'pending'
    source: str = 'manual'
    due_date: str | None = None
    notes: str | None = ''


class WorkflowPatch(BaseModel):
    assigned_to: str | None = None
    priority: str | None = None
    status: str | None = None
    due_date: str | None = None
    notes: str | None = None


class SimulationRequest(BaseModel):
    data: dict[str, Any]
    measure: str
    improvement: float


class IntakePayload(BaseModel):
    data: dict[str, Any]
    save_record: bool = False


class RecordUpdatePayload(BaseModel):
    data: dict[str, Any]



def normalize_text(value: str) -> str:
    value = (value or '').lower().strip()
    value = re.sub(r'[^a-z0-9\s]', ' ', value)
    value = re.sub(r'\s+', ' ', value)
    return value.strip()



def to_bool(value: str | None) -> bool:
    return str(value).strip().lower() in {'1', 'true', 'yes', 'y', 'on'}



def to_float(value: str | None) -> float | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    raw = raw.replace('%', '').replace(',', '')
    try:
        return float(raw)
    except ValueError:
        return None



def to_int(value: str | None) -> int | None:
    number = to_float(value)
    return None if number is None else int(round(number))



def compact_json(data: Any, max_chars: int = 900) -> str:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    return text if len(text) <= max_chars else text[:max_chars] + '\n... [truncated]'



def resolve_cms_access_url(title: str) -> str | None:
    response = requests.get(CMS_CATALOG_URL, timeout=CMS_TIMEOUT)
    response.raise_for_status()
    catalog = response.json()
    for dataset in catalog.get('dataset', []):
        if dataset.get('title') == title:
            for distro in dataset.get('distribution', []):
                if distro.get('format') == 'API' and distro.get('description') == 'latest':
                    return distro.get('accessURL')
    return None

def fetch_cms_rows(dataset_title: str, query: str = '', limit: int = 25, offset: int = 0) -> list[dict]:
    access_url = resolve_cms_access_url(dataset_title)
    if not access_url:
        return []
    params = {'size': limit, 'offset': offset}
    if query:
        params['keyword'] = query
    response = requests.get(access_url, params=params, timeout=CMS_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else []



def get_first_present(row: dict, keys: list[str]) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ''):
            return str(value)
    return ''



def get_name_from_row(row: dict) -> str:
    return get_first_present(row, ['provider_name', 'agency_name', 'facility_name', 'name', 'hha_name'])



def get_state_from_row(row: dict) -> str:
    return get_first_present(row, ['state', 'provider_state', 'address_state', 'hha_state'])



def get_city_from_row(row: dict) -> str:
    return get_first_present(row, ['city', 'provider_city', 'address_city', 'hha_city'])



def score_candidate(row: dict, agency_name: str, state: str, city: str) -> float:
    target_name = normalize_text(agency_name)
    target_state = normalize_text(state)
    target_city = normalize_text(city)
    row_name = normalize_text(get_name_from_row(row))
    row_state = normalize_text(get_state_from_row(row))
    row_city = normalize_text(get_city_from_row(row))
    score = 0.0
    if row_name:
        score += SequenceMatcher(None, target_name, row_name).ratio() * 100
    if target_state and row_state == target_state:
        score += 25
    if target_city and row_city == target_city:
        score += 15
    elif target_city and target_city in row_city:
        score += 8
    return score



def find_best_match(rows: list[dict], agency_name: str, state: str, city: str) -> tuple[dict | None, float]:
    if not rows:
        return None, 0.0
    ranked = sorted(((score_candidate(r, agency_name, state, city), r) for r in rows), key=lambda x: x[0], reverse=True)
    best_score, best_row = ranked[0]
    if best_score < 35:
        return None, best_score
    return best_row, best_score



def maybe_float(row: dict, keys: list[str]) -> float | None:
    for key in keys:
        if key in row and row[key] not in (None, ''):
            try:
                return float(str(row[key]).replace('%', '').replace(',', ''))
            except ValueError:
                continue
    return None



def extract_verified_metrics(agency_row: dict | None, hhvbp_row: dict | None) -> dict:
    metrics: dict[str, float] = {}
    sources = [agency_row or {}, hhvbp_row or {}]
    candidates = {
        'star_rating': ['quality_of_patient_care_star_rating', 'qm_rating', 'star_rating', 'quality_rating'],
        'patient_satisfaction': ['patient_survey_star_rating', 'patient_satisfaction', 'care_of_patients', 'patient_survey_summary_rating'],
        'readmission_rate': ['potentially_preventable_30_day_post_discharge_readmission_measure', 'readmission_rate', 'discharged_to_community'],
        'timely_initiation_of_care': ['timely_initiation_of_care', 'timely_initiation_of_care_1', 'timely_start_of_care'],
    }
    for metric_name, keys in candidates.items():
        for source in sources:
            value = maybe_float(source, keys)
            if value is not None:
                metrics[metric_name] = value
                break
    return metrics



def extract_state_benchmarks(rows: list[dict], state: str) -> dict:
    target = normalize_text(state)
    for row in rows:
        if normalize_text(get_state_from_row(row)) == target:
            return extract_verified_metrics(row, None)
    return {}



def enrich_with_cms(agency_name: str, state: str, city: str, data: dict[str, Any]) -> dict[str, Any]:
    notes = []
    state_benchmarks: dict[str, float] = {}
    confidence = 'No match'
    agency_match = None
    hhvbp_match = None

    try:
        agency_rows = fetch_cms_rows(HOME_HEALTH_TITLE, query=agency_name, limit=25)
        agency_match, agency_score = find_best_match(agency_rows, agency_name, state, city)
        if agency_match:
            confidence = f'Matched ({agency_score:.1f})'
        else:
            notes.append('No confident direct agency match found in the CMS provider dataset.')
    except Exception as exc:
        notes.append(f'Provider dataset lookup failed: {exc}')

    try:
        hhvbp_rows = fetch_cms_rows(HHVBP_TITLE, query=agency_name, limit=25)
        hhvbp_match, hhvbp_score = find_best_match(hhvbp_rows, agency_name, state, city)
        if hhvbp_match and confidence == 'No match':
            confidence = f'HHVBP-only match ({hhvbp_score:.1f})'
        elif not hhvbp_match:
            notes.append('No confident direct agency match found in the HHVBP dataset.')
    except Exception as exc:
        notes.append(f'HHVBP dataset lookup failed: {exc}')

    try:
        state_rows = fetch_cms_rows(STATE_TITLE, query=state, limit=25)
        state_benchmarks = extract_state_benchmarks(state_rows, state)
        if not state_benchmarks:
            notes.append('No state benchmark row was confidently extracted.')
    except Exception as exc:
        notes.append(f'State benchmark lookup failed: {exc}')

    verified_metrics = extract_verified_metrics(agency_match, hhvbp_match)
    cms_to_local = {
        'star_rating': 'star_rating',
        'patient_satisfaction': 'patient_satisfaction',
        'readmission_rate': 'readmission_rate',
        'timely_initiation_of_care': 'oasis_timeliness',
    }
    for cms_key, local_key in cms_to_local.items():
        if verified_metrics.get(cms_key) is not None:
            data[local_key] = verified_metrics[cms_key]

    data['cms_context'] = {
        'agency_match_confidence': confidence,
        'verified_metrics': verified_metrics,
        'state_benchmarks': state_benchmarks,
        'notes': ' '.join(notes) if notes else 'CMS lookups completed.',
        'raw_provider_excerpt': compact_json(agency_match) if agency_match else 'Unavailable',
        'raw_hhvbp_excerpt': compact_json(hhvbp_match) if hhvbp_match else 'Unavailable',
    }
    return data



def enrich_locally(data: dict[str, Any]) -> dict[str, Any]:
    data = normalize_record(data)
    data.setdefault('cms_context', {})
    data.setdefault('scorecard', {})
    data['scorecard'] = calculate_metric_score(data)
    data['compliance_findings'] = evaluate_compliance_risks(data)
    data['trend_summary'] = build_measure_trends(data)
    data['alerts'] = generate_alerts(data['scorecard'], data['compliance_findings'], data['trend_summary'])
    return data



def build_form_data(**kwargs: Any) -> dict[str, Any]:
    return {
        'agency_name': kwargs['agency_name'],
        'state': kwargs['state'],
        'city': kwargs['city'],
        'ownership_type': kwargs['ownership_type'],
        'avg_monthly_patients': to_int(kwargs.get('avg_monthly_patients')),
        'clinicians_total': to_int(kwargs.get('clinicians_total')),
        'star_rating': to_float(kwargs.get('star_rating')),
        'readmission_rate': to_float(kwargs.get('readmission_rate')),
        'patient_satisfaction': to_float(kwargs.get('patient_satisfaction')),
        'oasis_timeliness': to_float(kwargs.get('oasis_timeliness')),
        'soc_delay_days': to_float(kwargs.get('soc_delay_days')),
        'visit_completion_rate': to_float(kwargs.get('visit_completion_rate')),
        'documentation_lag_hours': to_float(kwargs.get('documentation_lag_hours')),
        'turnover_rate': to_float(kwargs.get('turnover_rate')),
        'open_positions': to_int(kwargs.get('open_positions')),
        'visits_per_clinician_week': to_float(kwargs.get('visits_per_clinician_week')),
        'ehr_vendor': kwargs.get('ehr_vendor') or 'Unknown',
        'evv_present': to_bool(kwargs.get('evv_present')),
        'scheduling_software': kwargs.get('scheduling_software') or 'Unknown',
        'telehealth_present': to_bool(kwargs.get('telehealth_present')),
        'automation_present': to_bool(kwargs.get('automation_present')),
        'monthly_revenue_range': kwargs.get('monthly_revenue_range') or 'Not provided',
        'cost_pressure_level': kwargs['cost_pressure_level'],
        'improvement_budget': kwargs['improvement_budget'],
        'leadership_readiness': kwargs['leadership_readiness'],
        'change_resistance': kwargs['change_resistance'],
        'training_infrastructure': kwargs['training_infrastructure'],
        'pain_points': [PAIN_POINT_CHOICES[p] for p in kwargs.get('pain_points', []) if p in PAIN_POINT_CHOICES],
        'cms_context': {},
        'scorecard': {},
        'notes': (kwargs.get('notes') or '').strip(),
        'monthly_series': [],
    }



def process_agency_payload(data: dict[str, Any], save_record: bool = False) -> dict[str, Any]:
    agency_name = data.get('agency_name', '')
    state = data.get('state', '')
    city = data.get('city', '')
    if agency_name and state:
        data = enrich_with_cms(agency_name, state, city, data)
    data = enrich_locally(data)
    if save_record:
        saved = save_agency_record(data)
        append_audit_event('agency_record_saved', 'Agency analysis saved.', agency_name=data.get('agency_name', ''))
        data['saved_record'] = {'id': saved['id'], 'updated_at': saved['updated_at']}
    return data



@app.get('/login', response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if DEMO_MODE:
        return RedirectResponse(url='/', status_code=302)
    template = templates_env.get_template("login.html")
    return HTMLResponse(template.render(request=request))
@app.post('/login')
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...), csrf_token_value: str | None = Form(None, alias='csrf_token')):
    user = authenticate_user(username, password)
    if not user:
        append_audit_event('login_failed', f'Failed login for {username.strip().lower()}', user='anonymous', ip_address=client_ip(request))
        return templates.TemplateResponse('login.html', {'request': request, 'csrf_token': ensure_csrf(request), 'bootstrap_path': BOOTSTRAP_FILE.name, 'error': 'Invalid credentials.'}, status_code=401)
    request.session['user'] = user['username']
    request.session['role'] = user['role']
    ensure_csrf(request)
    append_audit_event('login_success', 'User authenticated.', user=user['username'], ip_address=client_ip(request))
    return RedirectResponse(url='/', status_code=303)


@app.post('/logout')
async def logout_submit(request: Request, csrf_token_value: str = Form(..., alias='csrf_token')):
    validate_csrf(request, csrf_token_value)
    user = current_user_from_session(request)
    request.session.clear()
    append_audit_event('logout', 'User logged out.', user=(user or {}).get('username', 'anonymous'), ip_address=client_ip(request))
    return RedirectResponse(url='/login', status_code=303)


@app.post('/change-password')
async def change_password_submit(request: Request, current_password: str = Form(...), new_password: str = Form(...), csrf_token_value: str = Form(..., alias='csrf_token')):
    validate_csrf(request, csrf_token_value)
    user = require_user(request)
    verified = authenticate_user(user['username'], current_password)
    if not verified:
        raise HTTPException(status_code=401, detail='Current password is incorrect.')
    if len(new_password) < 12:
        raise HTTPException(status_code=400, detail='New password must be at least 12 characters.')
    change_password(user['username'], new_password, must_change_password=False)
    append_audit_event('password_changed', 'Password updated.', user=user['username'], ip_address=client_ip(request))
    return RedirectResponse(url='/', status_code=303)


@app.get('/', response_class=HTMLResponse)
async def intake_form(request: Request):
    user = current_user_from_session(request)
    if not user and not DEMO_MODE:
        return RedirectResponse(url='/login', status_code=302)
    recent_records = list_agency_records()[:5]
    recent_audit = list_audit_events(10)
    return templates.TemplateResponse(request, 'index_v2.html', {
        'request': request,
        'pain_points': PAIN_POINT_CHOICES,
        'recent_records': recent_records,
        'recent_audit': recent_audit,
        'csrf_token': ensure_csrf(request),
        'current_user': user,
    })



@app.get('/client-demo', response_class=HTMLResponse)
async def client_demo(request: Request):
    return templates.TemplateResponse('client_demo.html', {'request': request, 'scenarios': list(DEMO_SCENARIOS.values())})


@app.get('/api/demo/scenarios')
async def demo_scenarios():
    return JSONResponse({'scenarios': [{k: v for k, v in item.items() if k != 'data'} for item in DEMO_SCENARIOS.values()]})


@app.get('/api/demo/scenarios/{slug}')
async def demo_scenario(slug: str):
    scenario = DEMO_SCENARIOS.get(slug)
    if not scenario:
        raise HTTPException(status_code=404, detail='Scenario not found')
    payload = process_agency_payload(dict(scenario['data']), save_record=False)
    generated_tasks = []
    for finding in payload.get('compliance_findings', [])[:3]:
        generated_tasks.append({
            'title': finding['recommendation'][:90],
            'agency_name': payload.get('agency_name', ''),
            'assigned_to': 'Operations Lead' if finding.get('category') != 'quality' else 'Clinical Manager',
            'priority': finding.get('severity', 'medium'),
            'status': 'pending',
            'source': 'demo',
            'notes': finding['issue'],
        })
    payload['workflow'] = generated_tasks
    append_audit_event('demo_scenario_viewed', f'Demo scenario loaded: {slug}', agency_name=payload.get('agency_name', ''))
    return JSONResponse(payload)


@app.get('/health')
async def health():
    return JSONResponse({'status': 'ok', 'version': app.version})


@app.get('/api/dashboard')
async def dashboard(request: Request, agency_name: str, state: str, city: str = ''):
    user = require_user(request, {'admin','analyst'})
    payload = process_agency_payload({
        'agency_name': agency_name,
        'state': state,
        'city': city,
        'ownership_type': 'Private',
        'avg_monthly_patients': None,
        'clinicians_total': None,
        'star_rating': None,
        'readmission_rate': None,
        'patient_satisfaction': None,
        'oasis_timeliness': None,
        'soc_delay_days': None,
        'visit_completion_rate': None,
        'documentation_lag_hours': None,
        'turnover_rate': None,
        'open_positions': None,
        'visits_per_clinician_week': None,
        'ehr_vendor': 'Unknown',
        'evv_present': False,
        'scheduling_software': 'Unknown',
        'telehealth_present': False,
        'automation_present': False,
        'monthly_revenue_range': 'Not provided',
        'cost_pressure_level': 'Moderate',
        'improvement_budget': 'None',
        'leadership_readiness': 'Moderate',
        'change_resistance': 'Moderate',
        'training_infrastructure': 'Informal',
        'pain_points': [],
        'notes': '',
        'monthly_series': [],
        'cms_context': {},
        'scorecard': {},
    })
    append_audit_event('dashboard_viewed', 'Dashboard generated from live inputs.', user=user['username'], agency_name=agency_name, ip_address=client_ip(request))
    return JSONResponse({
        'agency_name': agency_name,
        'scorecard': payload['scorecard'],
        'alerts': payload['alerts'],
        'compliance_findings': payload['compliance_findings'],
        'trend_summary': payload['trend_summary'],
        'cms_context': payload['cms_context'],
    })


@app.post('/api/intake')
async def api_intake(request: Request, payload: IntakePayload):
    user = require_user(request, {'admin','analyst'})
    validate_csrf(request, request.headers.get('x-csrf-token'))
    enriched = process_agency_payload(payload.data, save_record=payload.save_record)
    append_audit_event('intake_processed', 'Structured intake processed.', user=user['username'], agency_name=enriched.get('agency_name', ''), ip_address=client_ip(request))
    return JSONResponse(enriched)


@app.post('/api/intake/upload')
async def api_intake_upload(request: Request, file: UploadFile):
    user = require_user(request, {'admin','analyst'})
    validate_csrf(request, request.headers.get('x-csrf-token'))
    suffix = Path(file.filename or '').suffix.lower()
    temp_path = UPLOAD_DIR / f'upload{suffix}'
    raw = await file.read()
    enforce_upload_policy(file.filename or '', len(raw))
    temp_path.write_bytes(raw)
    parsed = load_intake_file(temp_path)
    if isinstance(parsed, list):
        items = [process_agency_payload(item, save_record=True) for item in parsed]
        append_audit_event('bulk_upload_processed', f'Processed {len(items)} uploaded rows.', user=user['username'], ip_address=client_ip(request))
        return JSONResponse({'items': items, 'count': len(items)})
    enriched = process_agency_payload(parsed, save_record=True)
    append_audit_event('upload_processed', 'File upload processed.', user=user['username'], agency_name=enriched.get('agency_name', ''), ip_address=client_ip(request))
    return JSONResponse(enriched)



@app.post('/api/emr/upload')
async def api_emr_upload(
    request: Request,
    agency_name: str = Form(...),
    state: str = Form(''),
    city: str = Form(''),
    ownership_type: str = Form('Private'),
    source_type: str = Form(...),
    file: UploadFile | None = None,
):
    user = require_user(request, {'admin','analyst'})
    validate_csrf(request, request.headers.get('x-csrf-token') or request.headers.get('x-csrf') or request.query_params.get('csrf_token'))
    if file is None:
        raise HTTPException(status_code=400, detail='No file uploaded.')
    raw = await file.read()
    enforce_upload_policy(file.filename or '', len(raw))
    enforce_upload_policy(file.filename or '', len(raw))
    try:
        if source_type == 'csv':
            rows = parse_emr_csv(raw.decode('utf-8-sig'))
        elif source_type == 'fhir':
            rows = parse_fhir_bundle(json.loads(raw.decode('utf-8-sig')))
        else:
            raise HTTPException(status_code=400, detail='source_type must be csv or fhir')
        aggregated = aggregate_emr_rows(rows, agency_name=agency_name, state=state, city=city, ownership_type=ownership_type)
        payload = process_agency_payload(aggregated, save_record=True)
        save_emr_import(agency_name, source_type, len(rows), payload.get('cms_context', {}).get('emr_ingestion', {}))
        append_audit_event('emr_import_processed', f'Imported {len(rows)} {source_type.upper()} rows.', user=user['username'], agency_name=agency_name, ip_address=client_ip(request))
        return JSONResponse({'source_type': source_type, 'row_count': len(rows), 'analysis': payload})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'EMR import failed: {exc}')


@app.get('/api/emr/imports')
async def api_emr_imports(request: Request, agency_name: str | None = None, limit: int = 25):
    require_user(request, {'admin','analyst'})
    return JSONResponse({'imports': list_emr_imports(agency_name, limit)})


@app.get('/api/compliance/check')
async def api_compliance(request: Request, agency_name: str, state: str, city: str = ''):
    return await dashboard(request, agency_name, state, city)


@app.get('/api/alerts')
async def api_alerts(request: Request, agency_name: str, state: str, city: str = ''):
    return await dashboard(request, agency_name, state, city)


@app.post('/api/simulate')
async def api_simulate(request: Request, payload: SimulationRequest):
    user = require_user(request, {'admin','analyst'})
    validate_csrf(request, request.headers.get('x-csrf-token'))
    data = enrich_locally(payload.data)
    result = simulate_measure_improvement(data, payload.measure, payload.improvement)
    append_audit_event('simulation_run', f"Simulation run for {payload.measure} (+{payload.improvement}).", user=user['username'], agency_name=data.get('agency_name', ''), ip_address=client_ip(request))
    return JSONResponse(result)


@app.get('/api/trends')
async def api_trends(request: Request, agency_name: str, state: str, city: str = ''):
    return await dashboard(request, agency_name, state, city)


@app.post('/api/workflow/create')
async def api_workflow_create(request: Request, task: WorkflowTaskIn):
    user = require_user(request, {'admin','analyst'})
    validate_csrf(request, request.headers.get('x-csrf-token'))
    created = create_task(task.model_dump())
    append_audit_event('workflow_task_created', created['title'], user=user['username'], agency_name=created.get('agency_name', ''), ip_address=client_ip(request))
    return JSONResponse(created)


@app.get('/api/workflow')
async def api_workflow(request: Request, agency_name: str | None = None):
    require_user(request, {'admin','analyst'})
    return JSONResponse({'tasks': list_tasks(agency_name)})


@app.patch('/api/workflow/{task_id}')
async def api_workflow_update(request: Request, task_id: str, patch: WorkflowPatch):
    user = require_user(request, {'admin','analyst'})
    validate_csrf(request, request.headers.get('x-csrf-token'))
    try:
        updated = update_task(task_id, patch.model_dump())
        append_audit_event('workflow_task_updated', updated['title'], user=user['username'], agency_name=updated.get('agency_name', ''), ip_address=client_ip(request))
        return JSONResponse(updated)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get('/api/records')
async def api_records(request: Request, agency_name: str | None = None):
    require_user(request, {'admin','analyst'})
    return JSONResponse({'records': list_agency_records(agency_name)})


@app.get('/api/records/{record_id}')
async def api_record_detail(request: Request, record_id: str):
    require_user(request, {'admin','analyst'})
    try:
        return JSONResponse(get_agency_record(record_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.put('/api/records/{record_id}')
async def api_record_update(request: Request, record_id: str, payload: RecordUpdatePayload):
    user = require_user(request, {'admin','analyst'})
    validate_csrf(request, request.headers.get('x-csrf-token'))
    try:
        updated_data = process_agency_payload(payload.data, save_record=False)
        updated = update_agency_record(record_id, updated_data)
        append_audit_event('agency_record_updated', 'Agency analysis updated.', user=user['username'], agency_name=updated.get('agency_name', ''), ip_address=client_ip(request))
        return JSONResponse(updated)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get('/api/audit')
async def api_audit(request: Request, limit: int = 50):
    require_user(request, {'admin'})
    return JSONResponse({'events': list_audit_events(limit)})


@app.post('/generate_report')
async def generate_report(
    request: Request,
    csrf_token_value: str = Form(..., alias='csrf_token'),
    agency_name: str = Form(...),
    state: str = Form(...),
    city: str = Form(...),
    ownership_type: str = Form(...),
    avg_monthly_patients: str = Form(''),
    clinicians_total: str = Form(''),
    star_rating: str = Form(''),
    readmission_rate: str = Form(''),
    patient_satisfaction: str = Form(''),
    oasis_timeliness: str = Form(''),
    soc_delay_days: str = Form(''),
    visit_completion_rate: str = Form(''),
    documentation_lag_hours: str = Form(''),
    turnover_rate: str = Form(''),
    open_positions: str = Form(''),
    visits_per_clinician_week: str = Form(''),
    ehr_vendor: str = Form(''),
    evv_present: str = Form('false'),
    scheduling_software: str = Form(''),
    telehealth_present: str = Form('false'),
    automation_present: str = Form('false'),
    monthly_revenue_range: str = Form(''),
    cost_pressure_level: str = Form(...),
    improvement_budget: str = Form(...),
    leadership_readiness: str = Form(...),
    change_resistance: str = Form(...),
    training_infrastructure: str = Form(...),
    pain_points: list[str] = Form([]),
    notes: str = Form(''),
    output_format: str = Form('pdf'),
):
    user = require_user(request, {'admin','analyst'})
    validate_csrf(request, csrf_token_value)
    data = build_form_data(
        agency_name=agency_name, state=state, city=city, ownership_type=ownership_type,
        avg_monthly_patients=avg_monthly_patients, clinicians_total=clinicians_total,
        star_rating=star_rating, readmission_rate=readmission_rate, patient_satisfaction=patient_satisfaction,
        oasis_timeliness=oasis_timeliness, soc_delay_days=soc_delay_days, visit_completion_rate=visit_completion_rate,
        documentation_lag_hours=documentation_lag_hours, turnover_rate=turnover_rate, open_positions=open_positions,
        visits_per_clinician_week=visits_per_clinician_week, ehr_vendor=ehr_vendor, evv_present=evv_present,
        scheduling_software=scheduling_software, telehealth_present=telehealth_present,
        automation_present=automation_present, monthly_revenue_range=monthly_revenue_range,
        cost_pressure_level=cost_pressure_level, improvement_budget=improvement_budget,
        leadership_readiness=leadership_readiness, change_resistance=change_resistance,
        training_infrastructure=training_infrastructure, pain_points=pain_points, notes=notes,
    )
    try:
        data = process_agency_payload(data, save_record=True)
        safe_name = ''.join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in agency_name.strip()) or 'agency'
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8', dir=str(UPLOAD_DIR)) as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            tmp_path = Path(tmp.name)
        md_output = REPORTS_DIR / f'{safe_name}.md'
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / 'home_health_decision_engine_cli_v2.py'), '-i', str(tmp_path), '-o', str(md_output)],
            capture_output=True, text=True, cwd=str(BASE_DIR)
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f'Report generation failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}')
        pdf_output = md_output.with_suffix('.pdf')
        append_audit_event('report_generated', f'Report generated in {output_format.upper()} format.', user=user['username'], agency_name=agency_name, ip_address=client_ip(request))
        if output_format.lower().strip() == 'md':
            return FileResponse(str(md_output), media_type='text/markdown', filename=md_output.name)
        return FileResponse(str(pdf_output), media_type='application/pdf', filename=pdf_output.name)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Unexpected server error: {exc}')


@app.get('/cms_debug')
async def cms_debug(request: Request, agency_name: str, state: str, city: str = ''):
    require_user(request, {'admin'})
    user = require_user(request, {'admin','analyst'})
    validate_csrf(request, csrf_token_value)
    data = build_form_data(
        agency_name=agency_name, state=state, city=city, ownership_type='Private',
        cost_pressure_level='Moderate', improvement_budget='None', leadership_readiness='Moderate',
        change_resistance='Moderate', training_infrastructure='Informal', pain_points=[], notes=''
    )
    return JSONResponse(enrich_with_cms(agency_name, state, city, data))























@app.get('/api/cms/provider-lookup')
async def api_cms_provider_lookup(agency_name: str, state: str, city: str = ''):
    return JSONResponse(build_cms_snapshot(agency_name=agency_name, state=state, city=(city or None)))



@app.get('/dashboard', response_class=HTMLResponse)
async def dashboard_page(request: Request):
    sample = {
        'agency_name': 'abc Home Health Agency',
        'city': 'Petersburg',
        'state': 'VA',
        'tier': 'At Risk',
        'total_score': 36,
        'star_rating': 3.5,
        'readmission_rate': 20,
        'patient_satisfaction': 87,
        'oasis_timeliness': 92,
        'soc_delay_days': 5,
        'visit_completion_rate': 87,
        'documentation_lag_hours': 40,
        'turnover_rate': 30,
        'clinicians_total': 20,
        'avg_monthly_patients': 80,
        'cms_status': 'disabled_pending_verified_source',
        'risks': [
            {'title': 'HHVBP Risk', 'detail': 'Readmission rate is above preferred operating range.'},
            {'title': 'Documentation Risk', 'detail': 'Documentation lag exceeds next-day expectation.'},
            {'title': 'Access Risk', 'detail': 'Start-of-care delays are greater than 3 days.'},
            {'title': 'Operational Reliability', 'detail': 'Visit completion rate is below benchmark.'}
        ],
        'recommendations': [
            {'title': 'Stabilize Care Operations', 'detail': 'Implement weekly discharge planning reviews and referral triage.'},
            {'title': 'Enhance Documentation Discipline', 'detail': 'Track late notes and coach clinicians on chart completion.'},
            {'title': 'Improve Staffing Reliability', 'detail': 'Analyze turnover drivers and tighten scheduling workflows.'}
        ],
        'action_plan': [
            'Month 1: Root cause analysis on readmissions.',
            'Month 1: Implement referral triage rules.',
            'Month 2: Launch documentation lag tracking.',
            'Month 2: Start retention survey and exit interviews.',
            'Month 3: Optimize scheduling workflows.',
            'Month 3: Develop formal training modules.'
        ],
        'roi_points': [
            'Reducing readmissions by 5% can improve payment adjustments.',
            'Improving SOC delays under 3 days may lift patient satisfaction.',
            'Raising visit completion above 90% can improve continuity and reduce overtime.',
            'Cutting documentation lag below 24 hours reduces compliance risk.'
        ]
    }
    return templates.TemplateResponse(request, 'dashboard.html', sample)





