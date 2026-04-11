import { useEffect, useState } from "react";
import AppLayout from "../layouts/AppLayout";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";
import MetricsChart from "../components/MetricsChart";
import RiskChart from "../components/RiskChart";
import { getAgencyRecords, getDashboard, getRisk } from "../api/services";
import { getRiskBadgeColor, getScoreBadgeColor } from "../components/uiHelpers";

export default function DashboardPage() {
  const [records, setRecords] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [dashboard, setDashboard] = useState(null);
  const [risk, setRisk] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getAgencyRecords()
      .then((data) => {
        setRecords(data || []);
        if (data?.length) setSelectedId(String(data[0].id));
      })
      .catch(() => setError("Could not load agency records."));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    getDashboard(selectedId).then(setDashboard).catch(() => setError("Could not load dashboard."));
    getRisk(selectedId).then(setRisk).catch(() => setError("Could not load risk."));
  }, [selectedId]);

  const chartData = [
    { name: "Star Rating", value: Number(dashboard?.scorecard?.star_rating || 0) },
    { name: "Risk Score", value: Number(risk?.risk_score || 0) },
    { name: "Payment Impact", value: Math.abs(Number(risk?.estimated_payment_impact_pct || 0)) },
    { name: "Alerts", value: Number(dashboard?.alerts?.length || 0) },
  ];

  return (
    <AppLayout>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ marginBottom: 8 }}>Dashboard</h1>
        <p style={{ color: "#475569", marginTop: 0 }}>Operational intelligence overview for home health performance.</p>
      </div>

      {error ? <p style={{ color: "red" }}>{error}</p> : null}

      <div style={{ marginBottom: 20 }}>
        <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} style={{ padding: 10, minWidth: 280, borderRadius: 10 }}>
          <option value="">Select agency record</option>
          {records.map((r) => (
            <option key={r.id} value={r.id}>#{r.id} - {r.agency_name}</option>
          ))}
        </select>
      </div>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 24 }}>
        <StatCard title="Agency" value={dashboard?.agency_name || "-"} subtitle={dashboard?.location || ""} accent="#2563eb" />
        <StatCard title="Risk Score" value={risk?.risk_score ?? "-"} subtitle={risk?.risk_tier || ""} accent="#dc2626" />
        <StatCard title="Est. Payment Impact" value={risk ? `${risk.estimated_payment_impact_pct}%` : "-"} accent="#d97706" />
        <StatCard title="Dominant Priority" value={dashboard?.scorecard?.dominant_priority || "-"} accent="#16a34a" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 20, marginBottom: 24 }}>
        <MetricsChart data={chartData} />
        <RiskChart riskScore={risk?.risk_score || 0} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <div style={{ background: "#fff", padding: 20, borderRadius: 18, boxShadow: "0 6px 18px rgba(15,23,42,0.08)" }}>
          <h2 style={{ marginTop: 0 }}>Alerts</h2>
          {dashboard?.alerts?.length ? (
            <ul>
              {dashboard.alerts.map((a, i) => <li key={i}>{typeof a === "string" ? a : JSON.stringify(a)}</li>)}
            </ul>
          ) : (
            <p>No alerts available.</p>
          )}
        </div>

        <div style={{ background: "#fff", padding: 20, borderRadius: 18, boxShadow: "0 6px 18px rgba(15,23,42,0.08)" }}>
          <h2 style={{ marginTop: 0 }}>Current Status</h2>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <StatusBadge label={risk?.risk_tier || "Unknown"} color={getRiskBadgeColor(risk?.risk_tier)} />
            <StatusBadge label={`Score ${risk?.risk_score ?? "-"}`} color={getScoreBadgeColor(100 - (risk?.risk_score || 0))} />
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
