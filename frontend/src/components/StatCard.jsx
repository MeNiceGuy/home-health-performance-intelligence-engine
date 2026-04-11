export default function StatCard({ title, value, subtitle, accent = "#2563eb" }) {
  return (
    <div
      style={{
        background: "#fff",
        borderRadius: 18,
        padding: 18,
        boxShadow: "0 6px 18px rgba(15,23,42,0.08)",
        minWidth: 220,
        borderTop: `4px solid ${accent}`,
      }}
    >
      <div style={{ fontSize: 13, color: "#64748b", marginBottom: 8 }}>{title}</div>
      <div style={{ fontSize: 28, fontWeight: 800, color: "#0f172a" }}>{value}</div>
      {subtitle ? <div style={{ fontSize: 12, color: "#64748b", marginTop: 6 }}>{subtitle}</div> : null}
    </div>
  );
}
