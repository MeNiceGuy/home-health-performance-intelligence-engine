import { useEffect, useState } from "react";
import AppLayout from "../layouts/AppLayout";
import StatusBadge from "../components/StatusBadge";
import Toast from "../components/Toast";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { generateAsyncReport, getAgencyRecords, getReports, getTaskStatus, downloadReportFile } from "../api/services";

export default function ReportsPage() {
  const [reports, setReports] = useState([]);
  const [records, setRecords] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [taskId, setTaskId] = useState("");
  const [taskStatus, setTaskStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState({ message: "", type: "success" });

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast({ message: "", type: "success" }), 2500);
  };

  const loadReports = () => getReports().then(setReports).catch(() => setReports([]));
  const loadRecords = () => getAgencyRecords().then(setRecords).catch(() => setRecords([]));

  useEffect(() => {
    loadReports();
    loadRecords();
  }, []);

  useEffect(() => {
    if (!taskId) return;
    const interval = setInterval(async () => {
      try {
        const status = await getTaskStatus(taskId);
        setTaskStatus(status);
        if (status.status === "SUCCESS" || status.status === "FAILURE") {
          clearInterval(interval);
          loadReports();
          setLoading(false);
          showToast(
            status.status === "SUCCESS" ? "Report generated." : "Report generation failed.",
            status.status === "SUCCESS" ? "success" : "error"
          );
        }
      } catch {
        clearInterval(interval);
        setLoading(false);
        showToast("Could not check task status.", "error");
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [taskId]);

  const handleGenerate = async () => {
    if (!selectedId) {
      showToast("Select an agency record first.", "warning");
      return;
    }

    setLoading(true);
    try {
      const res = await generateAsyncReport(Number(selectedId));
      setTaskId(res.task_id);
      setTaskStatus(res);
      showToast("Report job queued.");
    } catch {
      setLoading(false);
      showToast("Could not queue report.", "error");
    }
  };

  const handleDownload = async (reportId, kind) => {
    try {
      await downloadReportFile(reportId, kind);
      showToast(kind === "pdf" ? "PDF download started." : "Markdown download started.");
    } catch {
      showToast("Download failed.", "error");
    }
  };

  return (
    <AppLayout>
      <Toast message={toast.message} type={toast.type} />
      <h1>Reports</h1>

      <div style={{ background: "#fff", padding: 20, borderRadius: 18, boxShadow: "0 6px 18px rgba(15,23,42,0.08)", marginBottom: 24 }}>
        <h2>Generate Report</h2>
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} style={{ padding: 10, minWidth: 260, borderRadius: 10 }}>
            <option value="">Select agency record</option>
            {records.map((r) => (
              <option key={r.id} value={r.id}>#{r.id} - {r.agency_name}</option>
            ))}
          </select>
          <button onClick={handleGenerate} disabled={loading}>
            {loading ? "Generating..." : "Generate Async Report"}
          </button>
        </div>

        {taskStatus && (
          <div style={{ marginTop: 16 }}>
            <div><strong>Task:</strong> {taskStatus.task_id || taskId}</div>
            <div style={{ marginTop: 8 }}>
              <StatusBadge label={taskStatus.status || "queued"} color={taskStatus.status === "SUCCESS" ? "#16a34a" : taskStatus.status === "FAILURE" ? "#dc2626" : "#d97706"} />
            </div>
          </div>
        )}
      </div>

      <div style={{ background: "#fff", padding: 20, borderRadius: 18, boxShadow: "0 6px 18px rgba(15,23,42,0.08)" }}>
        <h2>Generated Reports</h2>

        {loading ? <LoadingSpinner label="Waiting for report job..." /> : null}

        {reports.length === 0 ? (
          <EmptyState title="No reports yet" message="Generate your first report from an agency record." />
        ) : (
          <ul style={{ paddingLeft: 18 }}>
            {reports.map((r) => (
              <li key={r.id} style={{ marginBottom: 16 }}>
                <strong>Report #{r.id}</strong> - Agency Record #{r.agency_record_id}
                <div style={{ marginTop: 8, display: "flex", gap: 12, flexWrap: "wrap" }}>
                  <button onClick={() => handleDownload(r.id, "md")}>Download Markdown</button>
                  <button onClick={() => handleDownload(r.id, "pdf")}>Download PDF</button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </AppLayout>
  );
}
