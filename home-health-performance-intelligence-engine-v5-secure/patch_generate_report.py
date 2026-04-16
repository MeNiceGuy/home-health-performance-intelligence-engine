from pathlib import Path
import re

path = Path("server.py")
text = path.read_text(encoding="utf-8", errors="ignore")

pattern = r"@app\.post\('/generate_report'\)[\s\S]*?(?=\n@app\.|\Z)"

replacement = """@app.post('/generate_report')
async def generate_report(request: Request):
    input_path = UPLOAD_DIR / 'portfolio_agency.json'
    if not input_path.exists():
        raise HTTPException(status_code=500, detail='Missing uploads/portfolio_agency.json')

    safe_name = 'portfolio_report'
    md_output = REPORTS_DIR / f'{safe_name}.md'

    result = subprocess.run(
        [sys.executable, str(BASE_DIR / 'home_health_decision_engine_cli_v2.py'), '-i', str(input_path), '-o', str(md_output)],
        capture_output=True, text=True, cwd=str(BASE_DIR)
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f'Report generation failed.\\nSTDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}')

    pdf_output = md_output.with_suffix('.pdf')
    if pdf_output.exists():
        return FileResponse(str(pdf_output), media_type='application/pdf', filename=pdf_output.name)

    return FileResponse(str(md_output), media_type='text/markdown', filename=md_output.name)
"""

new_text, count = re.subn(pattern, replacement, text, count=1)
if count != 1:
    raise SystemExit("Could not patch /generate_report route.")
path.write_text(new_text, encoding="utf-8")
print("Patched successfully")
