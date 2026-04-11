export default function Toast({ message, type = "success" }) {
  if (!message) return null;

  const bg = type === "error" ? "#dc2626" : type === "warning" ? "#d97706" : "#16a34a";

  return (
    <div
      style={{
        position: "fixed",
        top: 20,
        right: 20,
        background: bg,
        color: "#fff",
        padding: "12px 16px",
        borderRadius: 12,
        boxShadow: "0 8px 20px rgba(0,0,0,0.15)",
        zIndex: 9999,
        maxWidth: 320,
      }}
    >
      {message}
    </div>
  );
}
