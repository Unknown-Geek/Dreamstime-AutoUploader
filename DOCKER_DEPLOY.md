# Docker Deployment Guide

## Quick Start

### 1. Local Docker

```bash
# Build the image
docker build -t dreamstime-bot .

# Run the container
docker run -p 5000:5000 --env-file .env dreamstime-bot
```

Or use docker-compose:

```bash
docker-compose up -d
```

Access the web UI at: `http://localhost:5000`

---

## Deploy to Render

### Method 1: Direct Deploy (Recommended)

1. **Push to GitHub** (already done)

2. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com/

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repo: `Unknown-Geek/Dreamstime-AutoUploader`

4. **Configure Service**
   - **Name**: `dreamstime-bot`
   - **Environment**: `Docker`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Build Command**: (leave empty, Dockerfile handles it)
   - **Start Command**: (leave empty, Dockerfile handles it)

5. **Add Environment Variables**
   ```
   DREAMSTIME_USERNAME=your_username
   DREAMSTIME_PASSWORD=your_password
   GEMINI_API_KEY=your_gemini_key
   FLASK_SECRET_KEY=your_secret_key_here
   DOCKER_CONTAINER=true
   ```

6. **Configure Instance**
   - **Instance Type**: At least `Standard 512 MB` ($7/month)
   - ⚠️ Free tier won't work (needs more RAM for Chromium)

7. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (~5-10 minutes)

### Method 2: Using render.yaml

Create `render.yaml` in your repo:

```yaml
services:
  - type: web
    name: dreamstime-bot
    env: docker
    plan: starter
    healthCheckPath: /
    envVars:
      - key: DREAMSTIME_USERNAME
        sync: false
      - key: DREAMSTIME_PASSWORD
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: FLASK_SECRET_KEY
        generateValue: true
      - key: DOCKER_CONTAINER
        value: true
```

Then use Render's "Blueprint" deployment.

---

## Deploy to Railway

1. **Install Railway CLI** (Optional)
   ```bash
   npm i -g @railway/cli
   ```

2. **Deploy via Web**
   - Go to: https://railway.app/
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repo

3. **Add Environment Variables**
   - Go to "Variables" tab
   - Add:
     ```
     DREAMSTIME_USERNAME=your_username
     DREAMSTIME_PASSWORD=your_password
     GEMINI_API_KEY=your_gemini_key
     FLASK_SECRET_KEY=random_secret_here
     DOCKER_CONTAINER=true
     PORT=5000
     ```

4. **Configure Resources**
   - Railway auto-detects Dockerfile
   - Free tier includes $5 credit
   - Upgrade for more resources if needed

---

## Deploy to Fly.io

1. **Install Fly CLI**
   ```bash
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Login**
   ```bash
   fly auth login
   ```

3. **Launch App**
   ```bash
   fly launch --name dreamstime-bot
   ```

4. **Set Secrets**
   ```bash
   fly secrets set DREAMSTIME_USERNAME="your_username"
   fly secrets set DREAMSTIME_PASSWORD="your_password"
   fly secrets set GEMINI_API_KEY="your_gemini_key"
   fly secrets set FLASK_SECRET_KEY="random_secret"
   fly secrets set DOCKER_CONTAINER="true"
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DREAMSTIME_USERNAME` | Yes | Your Dreamstime username |
| `DREAMSTIME_PASSWORD` | Yes | Your Dreamstime password |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `FLASK_SECRET_KEY` | Yes | Random secret for Flask sessions |
| `DOCKER_CONTAINER` | Auto | Set to `true` in Docker (auto-detected) |
| `HEADLESS` | No | Force headless mode (default: auto in Docker) |
| `API_KEY` | No | Optional API key for webhook authentication |
| `REQUIRE_API_KEY` | No | Set to `true` to require API key |

---

## Resource Requirements

### Minimum
- **CPU**: 1 core
- **RAM**: 512 MB (tight, may struggle)
- **Disk**: 1 GB

### Recommended
- **CPU**: 2 cores
- **RAM**: 1-2 GB
- **Disk**: 2 GB

### Platform Recommendations

| Platform | Best Plan | Cost | Notes |
|----------|-----------|------|-------|
| **Render** | Starter (512MB) | $7/month | Easy setup, good for beginners |
| **Railway** | Hobby | $5/month | Fast deployment, good dev experience |
| **Fly.io** | Shared CPU 1x | ~$3/month | Most affordable, more technical |
| **DigitalOcean** | Basic Droplet | $6/month | Full VPS control |

---

## Troubleshooting

### Chromium Crashes
**Error**: `Browser process exited` or `Out of memory`

**Solution**: Increase RAM allocation to at least 1GB

### Build Timeout
**Error**: Build takes too long

**Solution**: 
- Use a platform with longer build timeouts
- Or pre-build the image and push to Docker Hub

### Connection Issues
**Error**: Can't access the web UI

**Solution**:
- Check if port 5000 is exposed
- Verify firewall rules
- Check platform-specific networking settings

### Browser Not Found
**Error**: `Executable doesn't exist`

**Solution**: Make sure Playwright install step runs:
```dockerfile
RUN playwright install chromium
RUN playwright install-deps chromium
```

---

## Local Development

Run with auto-reload:

```bash
docker-compose up --build
```

View logs:

```bash
docker-compose logs -f
```

Stop:

```bash
docker-compose down
```

---

## Security Notes

⚠️ **Important**:
- Never commit `.env` file to Git
- Use environment variables for all secrets
- Consider using a secrets manager for production
- Keep your Docker image updated

---

## Need Help?

- **Render Docs**: https://render.com/docs
- **Railway Docs**: https://docs.railway.app
- **Fly.io Docs**: https://fly.io/docs
- **Docker Docs**: https://docs.docker.com
