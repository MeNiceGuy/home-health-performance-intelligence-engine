import json
from pathlib import Path

from fastapi.testclient import TestClient

from server import app
from services.compliance import evaluate_compliance_risks
from services.emr_connectors import aggregate_emr_rows, parse_emr_csv, parse_fhir_bundle
from services.persistence import append_audit_event, list_audit_events, list_agency_records, save_agency_record
from services.scoring_engine import calculate_metric_score, simulate_measure_improvement
from services.trends import build_measure_trends

client = TestClient(app)


def sample_data():
    return {
        'agency_name': 'ABC Home Health',
        'state': 'VA',
        'city': 'Richmond',
        'ownership_type': 'Private',
        'avg_monthly_patients': 120,
        'clinicians_total': 12,
        'star_rating': 3.0,
        'readmission_rate': 18.0,
        'patient_satisfaction': 81.0,
        'oasis_timeliness': 84.0,
        'soc_delay_days': 2.0,
        'visit_completion_rate': 89.0,
        'documentation_lag_hours': 36.0,
        'turnover_rate': 22.0,
        'open_positions': 2,
        'visits_per_clinician_week': 28.0,
        'ehr_vendor': 'WellSky',
        'evv_present': True,
        'scheduling_software': 'AxisCare',
        'telehealth_present': True,
        'automation_present': False,
        'monthly_revenue_range': '500K-1M',
        'cost_pressure_level': 'High',
        'improvement_budget': '10K-50K',
        'leadership_readiness': 'Moderate',
        'change_resistance': 'Moderate',
        'training_infrastructure': 'Informal',
        'pain_points': ['High readmissions'],
        'cms_context': {'state_benchmarks': {'star_rating': 3.5, 'readmission_rate': 15, 'patient_satisfaction': 85}},
        'scorecard': {},
        'notes': '',
        'monthly_series': [
            {'readmission_rate': 20, 'oasis_timeliness': 80, 'patient_satisfaction': 79},
            {'readmission_rate': 19, 'oasis_timeliness': 82, 'patient_satisfaction': 80},
            {'readmission_rate': 18, 'oasis_timeliness': 84, 'patient_satisfaction': 81},
        ],
    }


def test_scorecard():
    score = calculate_metric_score(sample_data())
    assert score['total_score'] < 100
    assert 'estimated_payment_impact_pct' in score


def test_compliance_findings():
    findings = evaluate_compliance_risks(sample_data())
    assert any(f['category'] == 'documentation' for f in findings)


def test_simulation_and_trends():
    data = sample_data()
    data['scorecard'] = calculate_metric_score(data)
    sim = simulate_measure_improvement(data, 'oasis_timeliness', 5)
    assert sim['simulated_score'] >= sim['baseline_score']
    trends = build_measure_trends(data)
    assert trends['oasis_timeliness']['trend'] == 'improving'


def test_persistence_and_audit():
    saved = save_agency_record(sample_data())
    assert saved['id']
    records = list_agency_records('ABC Home Health')
    assert records
    append_audit_event('test_event', 'integration test', agency_name='ABC Home Health')
    events = list_audit_events(5)
    assert any(e['action'] == 'test_event' for e in events)


def test_emr_csv_connector():
    csv_text = (Path(__file__).resolve().parents[1] / 'samples' / 'emr_export_demo.csv').read_text(encoding='utf-8')
    rows = parse_emr_csv(csv_text)
    agg = aggregate_emr_rows(rows, 'Demo Agency', 'VA', 'Richmond')
    assert agg['avg_monthly_patients'] == 3
    assert agg['visit_completion_rate'] is not None


def test_fhir_connector():
    bundle = json.loads((Path(__file__).resolve().parents[1] / 'samples' / 'fhir_bundle_demo.json').read_text(encoding='utf-8'))
    rows = parse_fhir_bundle(bundle)
    assert len(rows) >= 1


def test_client_demo_page():
    res = client.get('/client-demo')
    assert res.status_code == 200
    assert 'Client-ready demo' in res.text
