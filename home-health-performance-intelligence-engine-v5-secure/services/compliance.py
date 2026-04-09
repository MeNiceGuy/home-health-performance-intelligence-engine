from __future__ import annotations

from typing import Any


def evaluate_compliance_risks(data: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    def add(flag: str, severity: str, issue: str, recommendation: str, category: str = 'operational') -> None:
        findings.append({
            'compliance_flag': flag,
            'severity': severity,
            'issue': issue,
            'recommendation': recommendation,
            'category': category,
        })

    readmission = data.get('readmission_rate')
    lag = data.get('documentation_lag_hours')
    oasis = data.get('oasis_timeliness')
    soc_delay = data.get('soc_delay_days')
    evv = data.get('evv_present')
    completion = data.get('visit_completion_rate')
    satisfaction = data.get('patient_satisfaction')
    turnover = data.get('turnover_rate')
    star = data.get('star_rating')
    telehealth = data.get('telehealth_present')
    budget = data.get('improvement_budget')

    if readmission is not None and readmission > 20:
        add('HHVBP Risk', 'high', 'Readmission rate exceeds a high-risk threshold.', 'Launch root-cause review on rehospitalizations and physician follow-up workflow.', 'quality')
    elif readmission is not None and readmission > 15:
        add('HHVBP Risk', 'medium', 'Readmission rate is above preferred operating range.', 'Monitor discharge planning and escalation workflows weekly.', 'quality')

    if lag is not None and lag > 48:
        add('Documentation Risk', 'high', 'Documentation lag exceeds 48 hours.', 'Implement same-day chart close workflow and manager escalation queue.', 'documentation')
    elif lag is not None and lag > 24:
        add('Documentation Risk', 'medium', 'Documentation lag exceeds next-day expectation.', 'Track late notes by clinician and assign coaching.', 'documentation')

    if oasis is not None and oasis < 80:
        add('Quality Reporting Risk', 'high', 'OASIS timeliness is materially below target.', 'Audit intake-to-SOC timing and deploy a timeliness watchlist.', 'quality')
    elif oasis is not None and oasis < 90:
        add('Quality Reporting Risk', 'medium', 'OASIS timeliness is below best practice.', 'Strengthen intake scheduling and weekend coverage planning.', 'quality')

    if soc_delay is not None and soc_delay > 3:
        add('Access Risk', 'high', 'Start-of-care delays are greater than 3 days.', 'Rebalance scheduling capacity and add referral triage rules.', 'access')

    if completion is not None and completion < 85:
        add('Operational Reliability Risk', 'high', 'Visit completion rate is weak.', 'Review missed-visit causes and assign workflow ownership by branch lead.', 'workflow')
    elif completion is not None and completion < 92:
        add('Operational Reliability Risk', 'medium', 'Visit completion rate is below benchmark.', 'Track missed-visit drivers and strengthen daily staffing oversight.', 'workflow')

    if evv is False:
        add('EVV Compliance Readiness', 'medium', 'Electronic visit verification is not enabled.', 'Prioritize EVV implementation and caregiver training plan.', 'compliance')

    if satisfaction is not None and satisfaction < 80:
        add('Patient Experience Risk', 'medium', 'Patient satisfaction is below preferred range.', 'Implement service-recovery workflow and patient callback program.', 'quality')

    if turnover is not None and turnover > 30:
        add('Workforce Stability Risk', 'high', 'Staff turnover is materially elevated.', 'Launch retention review, caseload balancing, and supervisor coaching.', 'workforce')

    if star is not None and star < 3:
        add('Public Rating Risk', 'medium', 'Star rating is below competitive range.', 'Target low-performing measures with 90-day improvement plan.', 'quality')

    if telehealth is False and budget not in {'None', None, ''}:
        add('Digital Readiness Gap', 'low', 'Telehealth is not enabled despite stated improvement capacity.', 'Assess virtual care use cases and phased rollout options.', 'innovation')

    if not findings:
        add('No Immediate Critical Flags', 'low', 'No major compliance signals were triggered by current inputs.', 'Continue monthly monitoring against HHVBP and documentation targets.', 'monitoring')

    return findings
