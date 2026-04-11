import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import PublicTopbar from "../components/PublicTopbar";

export default function LoginPage() {
  const navigate = useNavigate();
  const { setToken } = useAuth();
  const [username, setUsername] = useState("devon");
  const [password, setPassword] = useState("TestPass123!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.post("/auth/login", { username, password });
      setToken(res.data.access_token);
      navigate("/dashboard");
    } catch (err) {
      setError(err?.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const demoLogin = async () => {
    setUsername("devon");
    setPassword("TestPass123!");
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc" }}>
      <PublicTopbar />

      <div style={{ maxWidth: 980, margin: "50px auto", display: "grid", gridTemplateColumns: "1fr 420px", gap: 28, alignItems: "start", padding: "0 20px" }}>
        <div>
          <h1 style={{ marginTop: 0, fontSize: 42 }}>Access the intelligence platform</h1>
          <p style={{ color: "#475569", lineHeight: 1.7 }}>
            Log in to manage agency records, generate operational reports, and review risk-focused performance insights across your workflow.
          </p>

          <div style={{ background: "#fff", borderRadius: 18, padding: 22, boxShadow: "0 8px 24px rgba(15,23,42,0.08)", marginTop: 22 }}>
            <h3 style={{ marginTop: 0 }}>Demo access</h3>
            <p style={{ color: "#64748b" }}>
              Use the prefilled demo credentials to quickly enter the platform and explore the current workflow.
            </p>
            <button onClick={demoLogin}>Load Demo Credentials</button>
          </div>
        </div>

        <div style={{ background: "#fff", padding: 24, borderRadius: 20, boxShadow: "0 10px 28px rgba(15,23,42,0.10)" }}>
          <h2 style={{ marginTop: 0 }}>Login</h2>
          <form onSubmit={submit}>
            <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" style={{ width: "100%", marginBottom: 12, padding: 12, borderRadius: 10, border: "1px solid #cbd5e1" }} />
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" style={{ width: "100%", marginBottom: 12, padding: 12, borderRadius: 10, border: "1px solid #cbd5e1" }} />
            <button type="submit" style={{ width: "100%" }}>
              {loading ? "Signing in..." : "Login"}
            </button>
          </form>
          {error && <p style={{ color: "#dc2626" }}>{error}</p>}
        </div>
      </div>
    </div>
  );
}
