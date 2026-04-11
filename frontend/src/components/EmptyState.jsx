export default function EmptyState({ title, message }) {
  return (
    <div
      style={{
        background: "#fff",
        padding: 24,
        borderRadius: 18,
        boxShadow: "0 6px 18px rgba(15,23,42,0.08)",
        textAlign: "center",
      }}
    >
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      <p style={{ color: "#64748b", marginBottom: 0 }}>{message}</p>
    </div>
  );
}
