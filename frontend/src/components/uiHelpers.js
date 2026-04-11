export function getRiskBadgeColor(tier) {
  if (tier === "High") return "#dc2626";
  if (tier === "Moderate") return "#d97706";
  return "#16a34a";
}

export function getScoreBadgeColor(score) {
  if (score >= 80) return "#16a34a";
  if (score >= 60) return "#d97706";
  return "#dc2626";
}
