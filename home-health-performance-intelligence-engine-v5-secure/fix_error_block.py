from pathlib import Path
import re

p = Path("server.py")
t = p.read_text(encoding="utf-8", errors="ignore")

# Replace any broken multiline f-string in the error raise
t = re.sub(
    r"raise HTTPException\([^\)]*Report generation failed\.[\s\S]*?\)",
    """raise HTTPException(
        status_code=500,
        detail=f"Report generation failed.\\nSTDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}"
    )""",
    t,
    count=1
)

p.write_text(t, encoding="utf-8")
print("Fixed error block")
