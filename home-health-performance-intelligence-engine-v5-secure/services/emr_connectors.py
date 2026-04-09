from __future__ import annotations

import csv
import json
from datetime import datetime
from io import StringIO
from typing import Any

EMR_REQUIRED_COLUMNS = {'patient_id', 'visit_date'}


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.replace('Z', '+00:00')
    for fmt in (None, '%Y-%m-%d', '%Y-%m-%d %H:%M:%S'):
        try:
            if fmt is None:
                return datetime.fromisoformat(value)
            return datetime.strptime(value, fmt)
        except Exception:
            continue
    return None


def parse_emr_csv(text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(StringIO(text))
    rows = [{k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()} for row in reader]
    if not rows:
        raise ValueError('CSV file contains no rows.')
    missing = EMR_REQUIRED_COLUMNS - set(rows[0].keys())
    if missing:
        raise ValueError(f'Missing required EMR CSV columns: {", ".join(sorted(missing))}')
    return rows


def parse_fhir_bundle(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get('resourceType') != 'Bundle':
        raise ValueError('FHIR upload must be a Bundle resource.')
    rows: list[dict[str, Any]] = []
    patient_map: dict[str, str] = {}
    for entry in payload.get('entry', []):
        resource = entry.get('resource', {})
        rtype = resource.get('resourceType')
        if rtype == 'Patient':
            patient_id = resource.get('id') or 'unknown'
            patient_map[f'Patient/{patient_id}'] = patient_id
        elif rtype == 'Encounter':
            subject = resource.get('subject', {}).get('reference', '')
            period = resource.get('period', {})
            hosp_text = json.dumps(resource.get('hospitalization', {})).lower()
            rows.append({
                'patient_id': subject.split('/')[-1] or patient_map.get(subject, 'unknown'),
                'visit_date': period.get('start', ''),
                'completed_visit': 'true' if resource.get('status') == 'finished' else 'false',
                'hospitalized': 'true' if 'hospital' in hosp_text or 'inpatient' in hosp_text else 'false',
            })
        elif rtype == 'Observation':
            code_text = (
                resource.get('code', {}).get('text')
                or next((c.get('display') for c in resource.get('code', {}).get('coding', []) if c.get('display')), '')
            ).lower()
            subject = resource.get('subject', {}).get('reference', '')
            effective = resource.get('effectiveDateTime', '')
            value = resource.get('valueQuantity', {}).get('value')
            if value is None:
                value = resource.get('valueInteger')
            if value is None:
                value = resource.get('valueString')
            row = {'patient_id': subject.split('/')[-1] or 'unknown', 'visit_date': effective}
            if 'satisfaction' in code_text:
                row['satisfaction_score'] = str(value)
            elif 'oasis' in code_text or 'timeliness' in code_text:
                row['oasis_timely'] = str(value)
            elif 'documentation lag' in code_text:
                row['documentation_lag_hours'] = str(value)
            else:
                continue
            rows.append(row)
    if not rows:
        raise ValueError('FHIR bundle did not contain supported Encounter/Observation resources.')
    return rows


def aggregate_emr_rows(rows: list[dict[str, Any]], agency_name: str, state: str = '', city: str = '', ownership_type: str = 'Private') -> dict[str, Any]:
    unique_patients = {str(r.get('patient_id') or '').strip() for r in rows if r.get('patient_id')}
    completed_visits = 0
    total_visits = 0
    hospitalized_patients = set()
    satisfaction_values = []
    oasis_true = 0.0
    oasis_total = 0
    doc_lags = []
    soc_delays = []

    for row in rows:
        total_visits += 1
        if str(row.get('completed_visit', '')).lower() in {'true', '1', 'yes', 'finished'}:
            completed_visits += 1
        if str(row.get('hospitalized', '')).lower() in {'true', '1', 'yes'}:
            pid = str(row.get('patient_id') or '').strip()
            if pid:
                hospitalized_patients.add(pid)
        if row.get('satisfaction_score') not in (None, ''):
            try:
                satisfaction_values.append(float(row['satisfaction_score']))
            except ValueError:
                pass
        if row.get('oasis_timely') not in (None, ''):
            oasis_total += 1
            try:
                val = float(row['oasis_timely'])
                oasis_true += val / 100.0 if val > 1 else val
            except ValueError:
                if str(row['oasis_timely']).lower() in {'true', 'yes', '1'}:
                    oasis_true += 1
        if row.get('documentation_lag_hours') not in (None, ''):
            try:
                doc_lags.append(float(row['documentation_lag_hours']))
            except ValueError:
                pass
        admit = _parse_dt(row.get('admit_date'))
        soc = _parse_dt(row.get('start_of_care_date')) or _parse_dt(row.get('visit_date'))
        if admit and soc:
            soc_delays.append((soc - admit).total_seconds() / 86400.0)

    patient_count = max(len(unique_patients), 1)
    avg_satisfaction = round(sum(satisfaction_values) / len(satisfaction_values), 2) if satisfaction_values else None
    visit_completion_rate = round((completed_visits / max(total_visits, 1)) * 100, 2) if total_visits else None
    readmission_rate = round((len(hospitalized_patients) / patient_count) * 100, 2) if unique_patients else None
    oasis_timeliness = round((oasis_true / max(oasis_total, 1)) * 100, 2) if oasis_total else None
    documentation_lag = round(sum(doc_lags) / len(doc_lags), 2) if doc_lags else None
    soc_delay = round(sum(soc_delays) / len(soc_delays), 2) if soc_delays else None

    return {
        'agency_name': agency_name,
        'state': state,
        'city': city,
        'ownership_type': ownership_type,
        'avg_monthly_patients': len(unique_patients) or None,
        'clinicians_total': None,
        'star_rating': None,
        'readmission_rate': readmission_rate,
        'patient_satisfaction': avg_satisfaction,
        'oasis_timeliness': oasis_timeliness,
        'soc_delay_days': soc_delay,
        'visit_completion_rate': visit_completion_rate,
        'documentation_lag_hours': documentation_lag,
        'turnover_rate': None,
        'open_positions': None,
        'visits_per_clinician_week': None,
        'ehr_vendor': 'Imported EMR data',
        'evv_present': True,
        'scheduling_software': 'Integrated feed',
        'telehealth_present': False,
        'automation_present': True,
        'monthly_revenue_range': 'Not provided',
        'cost_pressure_level': 'Moderate',
        'improvement_budget': '10K-50K',
        'leadership_readiness': 'Moderate',
        'change_resistance': 'Moderate',
        'training_infrastructure': 'Structured program',
        'pain_points': ['Imported from EMR'],
        'notes': f'Aggregated from {len(rows)} EMR rows.',
        'monthly_series': [],
        'cms_context': {
            'emr_ingestion': {
                'row_count': len(rows),
                'unique_patients': len(unique_patients),
                'hospitalized_patients': len(hospitalized_patients),
                'source_metrics': {
                    'visit_completion_rate': visit_completion_rate,
                    'readmission_rate': readmission_rate,
                    'patient_satisfaction': avg_satisfaction,
                    'oasis_timeliness': oasis_timeliness,
                    'documentation_lag_hours': documentation_lag,
                    'soc_delay_days': soc_delay,
                }
            }
        },
        'scorecard': {},
    }
