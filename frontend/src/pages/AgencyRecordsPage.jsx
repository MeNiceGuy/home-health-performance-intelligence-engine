import { useEffect, useState } from "react";
import AppLayout from "../layouts/AppLayout";
import AgencyForm from "../components/AgencyForm";
import StatusBadge from "../components/StatusBadge";
import Toast from "../components/Toast";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { createAgencyRecord, deleteAgencyRecord, getAgencyRecord, getAgencyRecords, updateAgencyRecord } from "../api/services";

export default function AgencyRecordsPage() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState("");
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [toast, setToast] = useState({ message: "", type: "success" });

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast({ message: "", type: "success" }), 2500);
  };

  const loadRecords = () => getAgencyRecords().then(setRecords).catch(() => setRecords([]));

  useEffect(() => { loadRecords(); }, []);

  useEffect(() => {
    if (!selectedId) return setSelectedRecord(null);
    getAgencyRecord(selectedId).then(setSelectedRecord).catch(() => setSelectedRecord(null));
  }, [selectedId]);

  const handleCreate = async (form) => {
    setLoading(true);
    try {
      await createAgencyRecord(form);
      await loadRecords();
      showToast("Agency record created.");
    } catch {
      showToast("Could not create agency record.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (form) => {
    if (!selectedId) return;
    setLoading(true);
    try {
      await updateAgencyRecord(selectedId, form);
      await loadRecords();
      const refreshed = await getAgencyRecord(selectedId);
      setSelectedRecord(refreshed);
      showToast("Agency record updated.");
    } catch {
      showToast("Could not update agency record.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedId) return;

    const confirmed = window.confirm("Delete this agency record? This cannot be undone.");
    if (!confirmed) return;

    setLoading(true);
    try {
      await deleteAgencyRecord(selectedId);
      setSelectedId("");
      setSelectedRecord(null);
      await loadRecords();
      showToast("Agency record deleted.", "warning");
    } catch {
      showToast("Could not delete agency record.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <Toast message={toast.message} type={toast.type} />
      <h1>Agency Records</h1>

      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: 24 }}>
        <div style={{ background: "#fff", padding: 20, borderRadius: 18, boxShadow: "0 6px 18px rgba(15,23,42,0.08)" }}>
          <h2>Create Record</h2>
          <AgencyForm onSubmit={handleCreate} loading={loading} submitLabel="Create Agency Record" />
        </div>

        <div style={{ display: "grid", gap: 24 }}>
          <div style={{ background: "#fff", padding: 20, borderRadius: 18, boxShadow: "0 6px 18px rgba(15,23,42,0.08)" }}>
            <h2>Saved Records</h2>

            {loading ? <LoadingSpinner label="Processing..." /> : null}

            {records.length === 0 ? (
              <EmptyState title="No agency records yet" message="Create your first agency record to begin analysis." />
            ) : (
              <>
                <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} style={{ padding: 10, minWidth: 260, marginBottom: 16, borderRadius: 10 }}>
                  <option value="">Select record to edit</option>
                  {records.map((r) => (
                    <option key={r.id} value={r.id}>#{r.id} - {r.agency_name}</option>
                  ))}
                </select>

                <ul style={{ paddingLeft: 18 }}>
                  {records.map((r) => (
                    <li key={r.id} style={{ marginBottom: 12 }}>
                      <strong>#{r.id}</strong> {r.agency_name} - {r.city}, {r.state}{" "}
                      <StatusBadge label="Active" color="#16a34a" />
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>

          {selectedRecord && (
            <div style={{ background: "#fff", padding: 20, borderRadius: 18, boxShadow: "0 6px 18px rgba(15,23,42,0.08)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h2>Edit Record</h2>
                <button onClick={handleDelete} style={{ background: "#dc2626" }}>Delete</button>
              </div>
              <AgencyForm onSubmit={handleUpdate} loading={loading} initialData={selectedRecord} submitLabel="Update Agency Record" />
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
