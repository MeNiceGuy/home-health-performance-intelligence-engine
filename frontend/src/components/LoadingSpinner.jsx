export default function LoadingSpinner({ label = "Loading..." }) {
  return (
    <div style={{ padding: 16, color: "#475569", fontWeight: 600 }}>
      {label}
    </div>
  );
}
