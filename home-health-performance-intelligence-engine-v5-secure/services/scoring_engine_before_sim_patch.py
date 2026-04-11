from __future__ import annotations

from typing import Any


BENCHMARK_DEFAULTS = {
    'star_rating': 3.5,
    'readmission_rate': 15.0,
    'patient_satisfaction': 85.0,
    'oasis_timeliness': 90.0,
    'visit_completion_rate': 92.0,
    'documentation_lag_hours': 24.0,
}


def _peer_rank(score: int) -> str:
    if score < 50:
        return 'bottom_10%'
    if score < 60:
        return 'bottom_25%'
    if score < 80:
        return 'middle_50%'
    return 'top_25%'



def calculate_metric_score(data: dict[str, Any]) -> dict[str, Any]:
    score = 100
    deductions: list[str] = []

    def deduct(points: int, reason: str) -> None:
        nonlocal score
        score -= points
        deductions.append(f'-{points}: {reason}')

    star = data.get('star_rating')
    if star is not None:
        if star <= 2:
            deduct(15, 'Low star rating')
        elif star < 3.5:
            deduct(8, 'Below-leading star rating')

    readmission = data.get('readmission_rate')
    if readmission is not None:
        if readmission > 20:
            deduct(15, 'High readmission rate')
        elif readmission > 15:
            deduct(8, 'Elevated readmission rate')

    satisfaction = data.get('patient_satisfaction')
    if satisfaction is not None:
        if satisfaction < 75:
            deduct(12, 'Low patient satisfaction')
        elif satisfaction < 85:
            deduct(6, 'Patient satisfaction below strong threshold')

    oasis = data.get('oasis_timeliness')
    if oasis is not None:
        if oasis < 80:
            deduct(10, 'OASIS timeliness materially below target')
        elif oasis < 90:
            deduct(5, 'OASIS timeliness below best practice')

    soc_delay = data.get('soc_delay_days')
    if soc_delay is not None:
        if soc_delay > 3:
            deduct(10, 'Start-of-care delays greater than 3 days')
        elif soc_delay > 1.5:
            deduct(5, 'Moderate start-of-care delay')

    completion = data.get('visit_completion_rate')
    if completion is not None:
        if completion < 85:
            deduct(10, 'Visit completion rate is weak')
        elif completion < 92:
            deduct(5, 'Visit completion rate has room to improve')

    lag = data.get('documentation_lag_hours')
    if lag is not None:
        if lag > 48:
            deduct(10, 'Documentation lag exceeds 48 hours')
        elif lag > 24:
            deduct(5, 'Documentation lag exceeds next-day standard')

    turnover = data.get('turnover_rate')
    if turnover is not None:
        if turnover > 30:
            deduct(15, 'High workforce turnover')
        elif turnover > 20:
            deduct(8, 'Elevated workforce turnover')

    open_positions = data.get('open_positions')
    clinicians_total = data.get('clinicians_total')
    if open_positions is not None and clinicians_total:
        vacancy_ratio = open_positions / max(clinicians_total, 1)
        if vacancy_ratio > 0.2:
            deduct(10, 'Vacancy load is high relative to clinician base')
        elif vacancy_ratio > 0.1:
            deduct(5, 'Vacancy load is noticeable')

    visits_per_clinician = data.get('visits_per_clinician_week')
    if visits_per_clinician is not None:
        if visits_per_clinician > 32:
            deduct(8, 'Clinician caseload pressure appears high')
        elif visits_per_clinician < 16:
            deduct(4, 'Clinician productivity may be under-optimized')

    if data.get('cost_pressure_level') == 'High':
        deduct(5, 'High cost pressure reduces implementation flexibility')
    if data.get('improvement_budget') == 'None':
        deduct(8, 'No dedicated improvement budget')
    elif data.get('improvement_budget') == '<10K':
        deduct(4, 'Improvement budget is limited')
    if data.get('leadership_readiness') == 'Low':
        deduct(8, 'Leadership readiness is low')
    elif data.get('leadership_readiness') == 'Moderate':
        deduct(3, 'Leadership readiness is not yet strong')
    if data.get('change_resistance') == 'High':
        deduct(8, 'High change resistance')
    elif data.get('change_resistance') == 'Moderate':
        deduct(3, 'Moderate change resistance')
    if data.get('training_infrastructure') == 'None':
        deduct(8, 'No training infrastructure')
    elif data.get('training_infrastructure') == 'Informal':
        deduct(4, 'Training infrastructure is informal')

    score = max(0, min(100, score))
    if score >= 80:
        tier = 'Strong'
        dominant_priority = 'Protect performance while selectively scaling automation and throughput improvements.'
    elif score >= 60:
        tier = 'Transitional'
        dominant_priority = 'Tighten core workflows before layering on larger innovations.'
    else:
        tier = 'At Risk'
        dominant_priority = 'Stabilize care operations, documentation discipline, and staffing reliability first.'

    benchmarks = data.get('cms_context', {}).get('state_benchmarks', {}) or BENCHMARK_DEFAULTS
    benchmark_delta = {
        'star_rating_delta': round((data.get('star_rating') or 0) - benchmarks.get('star_rating', BENCHMARK_DEFAULTS['star_rating']), 2) if data.get('star_rating') is not None else None,
        'readmission_delta': round((data.get('readmission_rate') or 0) - benchmarks.get('readmission_rate', BENCHMARK_DEFAULTS['readmission_rate']), 2) if data.get('readmission_rate') is not None else None,
        'patient_satisfaction_delta': round((data.get('patient_satisfaction') or 0) - benchmarks.get('patient_satisfaction', BENCHMARK_DEFAULTS['patient_satisfaction']), 2) if data.get('patient_satisfaction') is not None else None,
    }

    payment_risk = 0.0
    if readmission is not None:
        payment_risk -= max(0.0, (readmission - 15) * 0.12)
    if oasis is not None:
        payment_risk += max(0.0, (oasis - 90) * 0.03)
    if satisfaction is not None:
        payment_risk += max(0.0, (satisfaction - 85) * 0.02)
    if star is not None:
        payment_risk += max(-1.0, min(1.0, (star - 3.5) * 0.35))
    payment_risk = round(max(-5.0, min(5.0, payment_risk)), 2)

    return {
        'total_score': score,
        'tier': tier,
        'dominant_priority': dominant_priority,
        'deductions': deductions,
        'benchmark_delta': benchmark_delta,
        'estimated_payment_impact_pct': payment_risk,
        'peer_rank_hint': _peer_rank(score),
        'executive_summary': {
            'top_risk': deductions[0] if deductions else 'No major risks triggered.',
            'payment_outlook': 'Positive' if payment_risk > 0 else ('Negative' if payment_risk < 0 else 'Neutral'),
            'benchmark_position': _peer_rank(score),
        }
    }



def generate_alerts(scorecard: dict[str, Any], compliance_findings: list[dict[str, Any]], trends: dict[str, Any]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if scorecard.get('tier') == 'At Risk':
        alerts.append({'severity': 'high', 'alert': 'Agency is in the At Risk performance tier.', 'source': 'scorecard'})
    if scorecard.get('estimated_payment_impact_pct', 0) < 0:
        alerts.append({'severity': 'medium', 'alert': f"Estimated payment impact is negative ({scorecard['estimated_payment_impact_pct']}%).", 'source': 'payment_model'})
    for finding in compliance_findings:
        if finding['severity'] in {'high', 'medium'}:
            alerts.append({'severity': finding['severity'], 'alert': finding['issue'], 'source': finding['compliance_flag'], 'category': finding.get('category', 'general')})
    for metric, summary in trends.items():
        if summary.get('trend') == 'declining':
            alerts.append({'severity': 'medium', 'alert': f'{metric} trend is declining.', 'source': 'trend', 'category': 'forecast'})
    return alerts



def simulate_measure_improvement(data: dict[str, Any], measure: str, improvement: float) -> dict[str, Any]:
    clone = dict(data)
    current = clone.get(measure)
    if current is None:
        raise ValueError(f"Measure '{measure}' is unavailable for simulation.")
    clone[measure] = current + improvement
    updated = calculate_metric_score(clone)
    baseline = data.get('scorecard') or calculate_metric_score(data)
    return {
        'measure': measure,
        'baseline_value': current,
        'simulated_value': clone[measure],
        'baseline_score': baseline.get('total_score'),
        'simulated_score': updated.get('total_score'),
        'score_change': updated.get('total_score', 0) - baseline.get('total_score', 0),
        'payment_impact_change_pct': round(updated.get('estimated_payment_impact_pct', 0) - baseline.get('estimated_payment_impact_pct', 0), 2),
        'peer_rank_change': {
            'before': baseline.get('peer_rank_hint'),
            'after': updated.get('peer_rank_hint'),
        }
    }

