import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";

const COLORS = ["#16a34a", "#d97706", "#dc2626"];

export default function RiskChart({ riskScore }) {
  const safe = Math.max(0, 100 - (riskScore || 0));
  const data = [
    { name: "Safe Margin", value: safe },
    { name: "Risk Score", value: riskScore || 0 },
  ];

  return (
    <div style={{ width: "100%", height: 320, background: "#fff", borderRadius: 18, padding: 16, boxShadow: "0 6px 18px rgba(15,23,42,0.08)" }}>
      <h3 style={{ marginTop: 0 }}>Risk Composition</h3>
      <ResponsiveContainer width="100%" height="88%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" outerRadius={95} label>
            {data.map((entry, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
