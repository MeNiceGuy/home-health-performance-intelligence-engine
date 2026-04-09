from __future__ import annotations

from statistics import mean
from typing import Any


def summarize_trend(series: list[float]) -> dict[str, Any]:
    if len(series) < 2:
        return {'trend': 'insufficient_data', 'forecast_30': None, 'forecast_60': None, 'forecast_90': None, 'change': None}
    first = series[0]
    last = series[-1]
    change = last - first
    avg_delta = mean([series[i] - series[i - 1] for i in range(1, len(series))])
    forecast_30 = round(last + avg_delta, 2)
    forecast_60 = round(last + (avg_delta * 2), 2)
    forecast_90 = round(last + (avg_delta * 3), 2)
    if change > 0:
        trend = 'improving'
    elif change < 0:
        trend = 'declining'
    else:
        trend = 'flat'
    return {
        'trend': trend,
        'forecast_30': forecast_30,
        'forecast_60': forecast_60,
        'forecast_90': forecast_90,
        'change': round(change, 2),
        'avg_delta': round(avg_delta, 2),
    }


def build_measure_trends(data: dict[str, Any]) -> dict[str, Any]:
    monthly_series = data.get('monthly_series') or []
    if not monthly_series:
        return {}

    keys = [
        'star_rating',
        'readmission_rate',
        'patient_satisfaction',
        'oasis_timeliness',
        'visit_completion_rate',
        'documentation_lag_hours',
    ]
    output: dict[str, Any] = {}
    for key in keys:
        values = [row[key] for row in monthly_series if isinstance(row, dict) and row.get(key) is not None]
        if values:
            output[key] = summarize_trend(values)
    return output
