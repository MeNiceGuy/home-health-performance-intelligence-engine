import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function AppLayout({ children }) {
  const navigate = useNavigate();
  const { logout } = useAuth();

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "Arial, sans-serif", background: "#e2e8f0" }}>
      <aside style={{ width: 250, background: "#0f172a", color: "#fff", padding: 24 }}>
        <h2 style={{ marginTop: 0, marginBottom: 24 }}>BHPI</h2>
        <p style={{ color: "#94a3b8", fontSize: 13, marginBottom: 24 }}>Boswell Consulting Group</p>

        <div style={{ display: "grid", gap: 12 }}>
          <button onClick={() => navigate("/dashboard")}>Dashboard</button>
          <button onClick={() => navigate("/agency-records")}>Agency Records</button>
          <button onClick={() => navigate("/reports")}>Reports</button>
          <button onClick={() => { logout(); navigate("/"); }}>Logout</button>
        </div>
      </aside>

      <main style={{ flex: 1, padding: 28 }}>
        {children}
      </main>
    </div>
  );
}
