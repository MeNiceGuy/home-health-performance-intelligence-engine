def generate_remediation_plan(findings):
    plan = []

    for f in findings:
        severity = f.get("severity", "low").lower()
        issue = f.get("issue", "Unknown issue")

        if severity == "high":
            plan.append({
                "priority": "HIGH",
                "action": f"Fix {issue}",
                "impact": "Immediate performance and reimbursement risk"
            })
        elif severity == "medium":
            plan.append({
                "priority": "MEDIUM",
                "action": f"Improve {issue}",
                "impact": "Moderate operational impact"
            })
        else:
            plan.append({
                "priority": "LOW",
                "action": f"Monitor {issue}",
                "impact": "Low immediate risk"
            })

    return plan[:5]