def calculate_compliance_score(findings):
    score = 100

    for f in findings:
        severity = f.get("severity", "low").lower()

        if severity == "high":
            score -= 15
        elif severity == "medium":
            score -= 7
        elif severity == "low":
            score -= 3

    return max(score, 0)