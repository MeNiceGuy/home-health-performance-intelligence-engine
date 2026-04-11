import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function PublicTopbar() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  return (
    <header
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "18px 28px",
        background: "#0f172a",
        color: "#fff",
      }}
    >
      <div style={{ fontWeight: 800, fontSize: 20 }}>Boswell Consulting Group</div>

      <nav style={{ display: "flex", gap: 18, alignItems: "center" }}>
        <Link to="/" style={{ color: "#fff" }}>Home</Link>
        <Link to="/pricing" style={{ color: "#fff" }}>Pricing</Link>
        {isAuthenticated ? (
          <button onClick={() => navigate("/dashboard")}>Dashboard</button>
        ) : (
          <button onClick={() => navigate("/login")}>Login</button>
        )}
      </nav>
    </header>
  );
}
