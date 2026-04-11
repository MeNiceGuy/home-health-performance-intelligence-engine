Write-Host "Activating virtual environment..."
& .\.venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Initializing database..."
python -m app.db.init_db

Write-Host "Starting app..."
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
