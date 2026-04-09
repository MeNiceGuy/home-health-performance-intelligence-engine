# Render deployment guide

## 1. Push this project to GitHub
From PowerShell in the project folder:

```powershell
git add .
git commit -m "Prepare secure production demo for Render"
git push origin main
```

## 2. Create the web service on Render
1. Sign in to Render.
2. Click **New +**.
3. Choose **Web Service**.
4. Connect your GitHub repository.
5. Select this repository.
6. Render will read `render.yaml` automatically.
7. Create the service.

## 3. Add environment variables in Render
Set these in the Render dashboard:

- `APP_ENV=production`
- `SESSION_SECRET_KEY=generate-a-long-random-value`
- `BOOTSTRAP_ADMIN_USERNAME=admin`
- `BOOTSTRAP_ADMIN_PASSWORD=choose-a-strong-password`
- `OPENAI_API_KEY=optional-for-ai-enhanced-reports`
- `MAX_UPLOAD_BYTES=5242880`

## 4. Test after deploy
Open:
- `/login`
- `/client-demo`
- `/`

## 5. Suggested recruiter-facing links
Use these in your README and LinkedIn:
- Live app: `https://YOUR-RENDER-SERVICE.onrender.com`
- Client demo: `https://YOUR-RENDER-SERVICE.onrender.com/client-demo`
- GitHub repo: your repository root

## 6. Production note
Render free services can spin down after inactivity. For a smoother recruiter experience, upgrade the plan later or add a status note in the README.
