import api from "./client";

export async function getAgencyRecords() {
  const res = await api.get("/agency-records");
  return res.data;
}

export async function getAgencyRecord(id) {
  const res = await api.get(`/agency-records/${id}`);
  return res.data;
}

export async function createAgencyRecord(data) {
  const res = await api.post("/agency-records", { data, save_record: true });
  return res.data;
}

export async function updateAgencyRecord(id, data) {
  const res = await api.put(`/agency-records/${id}`, { data });
  return res.data;
}

export async function deleteAgencyRecord(id) {
  const res = await api.delete(`/agency-records/${id}`);
  return res.data;
}

export async function getReports() {
  const res = await api.get("/reports");
  return res.data;
}

export async function generateAsyncReport(agencyRecordId) {
  const res = await api.post("/reports/generate-async", {
    agency_record_id: agencyRecordId,
  });
  return res.data;
}

export async function getTaskStatus(taskId) {
  const res = await api.get(`/reports/tasks/${taskId}`);
  return res.data;
}

export async function getDashboard(agencyRecordId) {
  const res = await api.get(`/dashboard/agency/${agencyRecordId}`);
  return res.data;
}

export async function getRisk(agencyRecordId) {
  const res = await api.get(`/risk/agency/${agencyRecordId}`);
  return res.data;
}

export async function downloadReportFile(reportId, kind) {
  const endpoint =
    kind === "pdf"
      ? `/reports/${reportId}/download/pdf`
      : `/reports/${reportId}/download/md`;

  const response = await api.get(endpoint, {
    responseType: "blob",
  });

  const blob = new Blob([response.data], {
    type:
      kind === "pdf"
        ? "application/pdf"
        : "text/markdown",
  });

  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  const disposition = response.headers["content-disposition"] || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const fallbackName = kind === "pdf" ? `report-${reportId}.pdf` : `report-${reportId}.md`;
  link.href = url;
  link.download = match?.[1] || fallbackName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
