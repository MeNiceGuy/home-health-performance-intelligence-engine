from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from services.persistence import get_conn


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_task(task: dict[str, Any]) -> dict[str, Any]:
    created = {
        'id': str(uuid4()),
        'title': task['title'],
        'agency_name': task.get('agency_name', 'Unknown Agency'),
        'assigned_to': task.get('assigned_to', 'Unassigned'),
        'priority': task.get('priority', 'medium'),
        'status': task.get('status', 'pending'),
        'source': task.get('source', 'manual'),
        'due_date': task.get('due_date'),
        'notes': task.get('notes', ''),
        'created_at': _utc_now(),
        'updated_at': _utc_now(),
    }
    with get_conn() as conn:
        conn.execute(
            'INSERT INTO workflow_tasks (id, title, agency_name, assigned_to, priority, status, source, due_date, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            tuple(created.values()),
        )
    return created


def list_tasks(agency_name: str | None = None) -> list[dict[str, Any]]:
    query = 'SELECT * FROM workflow_tasks'
    params = []
    if agency_name:
        query += ' WHERE agency_name=?'
        params.append(agency_name)
    query += ' ORDER BY CASE status WHEN "pending" THEN 0 WHEN "in_progress" THEN 1 ELSE 2 END, CASE priority WHEN "high" THEN 0 WHEN "medium" THEN 1 ELSE 2 END, created_at DESC'
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def update_task(task_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute('SELECT * FROM workflow_tasks WHERE id=?', (task_id,)).fetchone()
        if not row:
            raise KeyError(f'Task not found: {task_id}')
        data = dict(row)
        for k, v in patch.items():
            if v is not None:
                data[k] = v
        data['updated_at'] = _utc_now()
        conn.execute('UPDATE workflow_tasks SET assigned_to=?, priority=?, status=?, due_date=?, notes=?, updated_at=? WHERE id=?',
                     (data['assigned_to'], data['priority'], data['status'], data['due_date'], data['notes'], data['updated_at'], task_id))
    return data
