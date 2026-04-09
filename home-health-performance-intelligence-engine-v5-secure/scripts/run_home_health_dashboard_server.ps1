# PowerShell script to run Home Health Innovation Decision Engine web dashboard server

# Set environment variables
$env:SESSION_SECRET_KEY = "YourSecretSessionKeyHere"
$env:OPENAI_API_KEY = $env:OPENAI_API_KEY="YOUR_OPENAI_API_KEY"

# Navigate to the web_dashboard directory
Set-Location -Path "C:\Users\1bosw\GitHub\home_health_innovation_tool\web_dashboard"

# Run the server with Uvicorn
uvicorn server:app --reload --host 0.0.0.0 --port 8000
