$body = @{
  vault_path = "C:\Users\1bosw\Documents\ObsidianVault"
  agency = "Test Agency"
  title = "Demo Report"
  markdown = "## Demo Output`nThis is a real export test."
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/obsidian/export" -Method POST -Body $body -ContentType "application/json"
