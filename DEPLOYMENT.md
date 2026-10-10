# Railway Deployment Guide

## Prerequisites
- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))
- Git installed on your computer

---

## Step 1: Push to GitHub

```bash
# Initialize Git repository (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial web-dlp API implementation"

# Create a new repository on GitHub (go to github.com/new)
# Then connect and push:
git remote add origin https://github.com/YOUR_USERNAME/web-dlp-api.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy to Railway

### Option A: Using Railway Dashboard

1. **Sign in to Railway**
   - Go to [railway.app](https://railway.app)
   - Click "Login" and sign in with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your GitHub

3. **Select Repository**
   - Find and select `web-dlp-api` repository
   - Railway will auto-detect the Dockerfile

4. **Deploy**
   - Railway automatically starts building
   - Wait 2-3 minutes for deployment
   - You'll get a URL like: `https://web-dlp-production.up.railway.app`

5. **Generate Domain** (if not auto-assigned)
   - Go to your project settings
   - Click "Generate Domain" under "Networking"

### Option B: Using Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

---

## Step 3: Test Your Deployed API

```bash
# Replace with your Railway URL
export API_URL="https://your-app.railway.app"

# Test health check
curl $API_URL/

# Test creating a job
curl -X POST $API_URL/request \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","format":"mp3"}'
```

---

## Step 4: Set Up Keep-Alive (Free Tier)

Railway's free tier may sleep your app after inactivity. Use a cron service:

### Using Cron-Job.org

1. Go to [cron-job.org](https://cron-job.org)
2. Sign up for free
3. Create new cron job:
   - **Title**: web-dlp keep-alive
   - **URL**: `https://your-app.railway.app/`
   - **Schedule**: Every 5 minutes
   - **Method**: GET

### Using UptimeRobot

1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Add New Monitor:
   - **Monitor Type**: HTTP(s)
   - **URL**: `https://your-app.railway.app/`
   - **Monitoring Interval**: 5 minutes

---

## Step 5: Monitor Your API

### View Logs in Railway
```bash
# Using Railway CLI
railway logs
```

Or in the Railway dashboard:
- Go to your project
- Click "Deployments"
- Click "View Logs"

---

## Environment Variables (Optional)

If you need to add environment variables:

1. In Railway Dashboard:
   - Go to your project
   - Click "Variables"
   - Add key-value pairs

2. Using CLI:
   ```bash
   railway variables set KEY=VALUE
   ```

---

## Troubleshooting

### Build Fails
- Check Railway logs for errors
- Ensure Dockerfile is in root directory
- Verify all files are committed to Git

### API Not Responding
- Check if ffmpeg is installed (it should be via Dockerfile)
- Verify port 8000 is exposed
- Check Railway logs for startup errors

### Worker Not Running
- Ensure CMD in Dockerfile starts both processes
- Check logs for worker initialization messages

---

## Updating Your API

```bash
# Make changes to your code
git add .
git commit -m "Update: description of changes"
git push

# Railway auto-deploys on push to main branch
```

---

## Cost Monitoring

**Railway Free Tier** (as of 2024):
- $5 credit per month
- Limited to 500 hours execution time
- 1GB memory, 1 vCPU

**Tips to stay within free tier**:
- Use keep-alive to prevent sleep (reduces cold starts)
- Monitor usage in Railway dashboard
- Implement file cleanup (already done!)

---

## Custom Domain (Optional)

1. In Railway Dashboard:
   - Go to Settings → Networking
   - Add custom domain
   - Update DNS records as instructed

---

## API Documentation URL

Once deployed, your API docs will be at:
- **Swagger UI**: `https://your-app.railway.app/docs`
- **ReDoc**: `https://your-app.railway.app/redoc`

Share these URLs with your users for API exploration!
