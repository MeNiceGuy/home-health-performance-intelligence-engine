export default function FeatureGrid() {
  const features = [
    {
      title: "Agency Performance Intelligence",
      text: "Capture and organize key agency metrics for operational review and strategic planning.",
    },
    {
      title: "Risk Scoring",
      text: "Surface reimbursement risk, performance pressure, and likely problem areas quickly.",
    },
    {
      title: "Report Generation",
      text: "Produce markdown and PDF outputs for executive review, consulting delivery, or documentation.",
    },
    {
      title: "Actionable Workflow",
      text: "Move from raw metrics to guided insight with dashboards, trend visibility, and prioritized focus areas.",
    },
  ];

  return (
    <section style={{ padding: "60px 28px", background: "#f8fafc" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <h2 style={{ marginTop: 0, fontSize: 34 }}>Built for operators who need clarity fast</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 20, marginTop: 24 }}>
          {features.map((feature) => (
            <div
              key={feature.title}
              style={{
                background: "#fff",
                padding: 22,
                borderRadius: 18,
                boxShadow: "0 6px 18px rgba(15,23,42,0.08)",
              }}
            >
              <h3 style={{ marginTop: 0 }}>{feature.title}</h3>
              <p style={{ color: "#475569", marginBottom: 0 }}>{feature.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
