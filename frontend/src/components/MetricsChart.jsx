import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

export default function MetricsChart({ data }) {
  return (
    <div style={{ width: "100%", height: 320, background: "#fff", borderRadius: 18, padding: 16, boxShadow: "0 6px 18px rgba(15,23,42,0.08)" }}>
      <h3 style={{ marginTop: 0 }}>Performance Metrics</h3>
      <ResponsiveContainer width="100%" height="88%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" interval={0} angle={-15} textAnchor="end" height={60} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
