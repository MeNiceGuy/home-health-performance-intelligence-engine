import { useNavigate } from "react-router-dom";

export default function HeroSection() {
  const navigate = useNavigate();

  return (
    <section
      style={{
        padding: "80px 28px",
        background: "linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%)",
        color: "#fff",
      }}
    >
      <div style={{ maxWidth: 1100, margin: "0 auto", display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 32, alignItems: "center" }}>
        <div>
          <div style={{ display: "inline-block", padding: "8px 12px", borderRadius: 999, background: "rgba(255,255,255,0.12)", marginBottom: 18 }}>
            Home Health Performance Intelligence
          </div>
          <h1 style={{ fontSize: 52, lineHeight: 1.05, margin: "0 0 18px 0" }}>
            Turn agency data into strategic action.
          </h1>
          <p style={{ fontSize: 18, lineHeight: 1.6, color: "#dbeafe", maxWidth: 700 }}>
            Boswell Consulting Group helps home health operators assess performance risk,
            generate operational intelligence reports, and make stronger reimbursement-aware decisions.
          </p>

          <div style={{ display: "flex", gap: 14, marginTop: 28, flexWrap: "wrap" }}>
            <button onClick={() => navigate("/login")} style={{ background: "#fff", color: "#0f172a", fontWeight: 700 }}>
              Access Platform
            </button>
            <button onClick={() => navigate("/pricing")} style={{ background: "transparent", color: "#fff", border: "1px solid rgba(255,255,255,0.35)" }}>
              View Pricing
            </button>
          </div>
        </div>

        <div
          style={{
            background: "#fff",
            color: "#0f172a",
            borderRadius: 20,
            padding: 24,
            boxShadow: "0 14px 32px rgba(0,0,0,0.18)",
          }}
        >
          <h3 style={{ marginTop: 0 }}>What the platform does</h3>
          <ul style={{ paddingLeft: 18, lineHeight: 1.9, color: "#334155" }}>
            <li>Centralizes agency performance inputs</li>
            <li>Scores risk and reimbursement impact</li>
            <li>Generates downloadable intelligence reports</li>
            <li>Supports async report processing and auditability</li>
            <li>Improves management visibility across operations</li>
          </ul>
        </div>
      </div>
    </section>
  );
}
