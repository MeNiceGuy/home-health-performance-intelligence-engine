import { useEffect, useState } from "react";

const initialState = {
  agency_name: "",
  state: "VA",
  city: "Richmond",
  ownership_type: "Private",
  star_rating: 3.5,
  readmission_rate: 15,
  patient_satisfaction: 88,
  oasis_timeliness: 91,
  notes: "Demo record",
  pain_points: ["Documentation delays", "Staff burnout"],
  cms_context: {},
  scorecard: { total_score: 72, dominant_priority: "Workflow" },
  compliance_findings: [{ issue: "Documentation lag", severity: "medium" }],
  trend_summary: { readmission_rate: { trend: "worsening", forecast_next: 16 } },
  alerts: ["Documentation lag elevated"],
  monthly_series: []
};

export default function AgencyForm({ onSubmit, loading, initialData = null, submitLabel = "Save Agency Record" }) {
  const [form, setForm] = useState(initialState);
  const [error, setError] = useState("");

  useEffect(() => {
    if (initialData) setForm((prev) => ({ ...prev, ...initialData }));
  }, [initialData]);

  const update = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  const submit = (e) => {
    e.preventDefault();

    if (!form.agency_name?.trim()) {
      setError("Agency name is required.");
      return;
    }

    if (!form.state?.trim()) {
      setError("State is required.");
      return;
    }

    setError("");
    onSubmit(form);
  };

  return (
    <form onSubmit={submit} style={{ display: "grid", gap: 12 }}>
      {error ? <div style={{ color: "#dc2626", fontWeight: 600 }}>{error}</div> : null}

      <input value={form.agency_name || ""} onChange={(e) => update("agency_name", e.target.value)} placeholder="Agency name" required style={{ padding: 10 }} />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
        <input value={form.city || ""} onChange={(e) => update("city", e.target.value)} placeholder="City" style={{ padding: 10 }} />
        <input value={form.state || ""} onChange={(e) => update("state", e.target.value)} placeholder="State" style={{ padding: 10 }} />
        <input value={form.ownership_type || ""} onChange={(e) => update("ownership_type", e.target.value)} placeholder="Ownership" style={{ padding: 10 }} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        <input type="number" value={form.star_rating ?? 0} onChange={(e) => update("star_rating", Number(e.target.value))} placeholder="Star rating" style={{ padding: 10 }} />
        <input type="number" value={form.readmission_rate ?? 0} onChange={(e) => update("readmission_rate", Number(e.target.value))} placeholder="Readmission" style={{ padding: 10 }} />
        <input type="number" value={form.patient_satisfaction ?? 0} onChange={(e) => update("patient_satisfaction", Number(e.target.value))} placeholder="Patient satisfaction" style={{ padding: 10 }} />
        <input type="number" value={form.oasis_timeliness ?? 0} onChange={(e) => update("oasis_timeliness", Number(e.target.value))} placeholder="OASIS timeliness" style={{ padding: 10 }} />
      </div>
      <textarea value={form.notes || ""} onChange={(e) => update("notes", e.target.value)} placeholder="Notes" rows={4} style={{ padding: 10 }} />
      <button type="submit" disabled={loading} style={{ padding: "12px 16px" }}>
        {loading ? "Saving..." : submitLabel}
      </button>
    </form>
  );
}
