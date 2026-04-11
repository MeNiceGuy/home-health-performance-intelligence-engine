import PublicTopbar from "../components/PublicTopbar";

function PriceCard({ title, price, subtitle, items, featured = false }) {
  return (
    <div
      style={{
        background: "#fff",
        borderRadius: 20,
        padding: 24,
        boxShadow: "0 8px 24px rgba(15,23,42,0.10)",
        border: featured ? "2px solid #2563eb" : "1px solid #e2e8f0",
      }}
    >
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      <div style={{ fontSize: 36, fontWeight: 800, color: "#0f172a" }}>{price}</div>
      <p style={{ color: "#64748b" }}>{subtitle}</p>
      <ul style={{ paddingLeft: 18, color: "#334155", lineHeight: 1.9 }}>
        {items.map((item) => <li key={item}>{item}</li>)}
      </ul>
      <button style={{ width: "100%", marginTop: 12 }}>Get Started</button>
    </div>
  );
}

export default function PricingPage() {
  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc" }}>
      <PublicTopbar />

      <section style={{ padding: "60px 28px" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <h1 style={{ marginTop: 0 }}>Pricing</h1>
          <p style={{ color: "#475569", maxWidth: 760 }}>
            Choose the operating level that matches your current agency analysis and reporting needs.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20, marginTop: 30 }}>
            <PriceCard
              title="Starter"
              price="$99/mo"
              subtitle="For individual operators and light reporting"
              items={[
                "Agency record management",
                "Dashboard access",
                "Basic report generation",
                "Downloadable markdown and PDF reports",
              ]}
            />
            <PriceCard
              title="Professional"
              price="$249/mo"
              subtitle="For active agencies and consultants"
              featured={true}
              items={[
                "Everything in Starter",
                "Async report generation",
                "Enhanced dashboard experience",
                "Expanded usage and audit workflow",
              ]}
            />
            <PriceCard
              title="Enterprise"
              price="Custom"
              subtitle="For larger teams and multi-user environments"
              items={[
                "Everything in Professional",
                "Multi-user operational access",
                "Advanced implementation support",
                "Custom consulting alignment",
              ]}
            />
          </div>
        </div>
      </section>
    </div>
  );
}
