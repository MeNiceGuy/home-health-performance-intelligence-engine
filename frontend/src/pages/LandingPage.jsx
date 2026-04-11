import PublicTopbar from "../components/PublicTopbar";
import HeroSection from "../components/HeroSection";
import FeatureGrid from "../components/FeatureGrid";

export default function LandingPage() {
  return (
    <div style={{ minHeight: "100vh", background: "#fff" }}>
      <PublicTopbar />
      <HeroSection />
      <FeatureGrid />

      <section style={{ padding: "50px 28px", background: "#0f172a", color: "#fff" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <h2 style={{ marginTop: 0 }}>Boswell Consulting Group</h2>
          <p style={{ color: "#cbd5e1", maxWidth: 780 }}>
            A strategic consulting and intelligence-driven operating model focused on performance, compliance-minded execution, and scalable operational insight.
          </p>
        </div>
      </section>
    </div>
  );
}
