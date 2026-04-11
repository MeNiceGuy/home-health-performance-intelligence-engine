export default function StatusBadge({ label, color = "#2563eb" }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "6px 10px",
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 700,
        color: "#fff",
        background: color,
      }}
    >
      {label}
    </span>
  );
}
