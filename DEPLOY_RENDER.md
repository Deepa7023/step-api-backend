# Deploy to Render.com - Super Easy & Free Tier Available!

Render is similar to Railway but has a generous free tier!

## What You'll Get

- Live URL like: `https://step-api.onrender.com`
- Free tier available (with limitations)
- Automatic HTTPS
- Simple web interface

---

## Step-by-Step Guide

### Step 1: Upload Code to GitHub

First, you need to put your code on GitHub:

1. Go to: https://github.com
2. Sign up or log in
3. Click **"New repository"** (green button)
4. Name it: `step-api-backend`
5. Make it **Public**
6. Click **"Create repository"**

Now upload your files:
7. Click **"uploading an existing file"**
8. Drag and drop all your files from step-api-backend folder
9. Click **"Commit changes"**

### Step 2: Create Render Account

1. Go to: https://render.com
2. Click **"Get Started for Free"**
3. Sign up with GitHub (easier) or email
4. Authorize Render to access your GitHub

### Step 3: Create New Web Service

1. Click **"New +"** button (top right)
2. Select **"Web Service"**
3. Click **"Build and deploy from a Git repository"**
4. Click **"Next"**

### Step 4: Connect Your Repository

1. Find your `step-api-backend` repository
2. Click **"Connect"**

### Step 5: Configure Service

Fill in these settings:

**Name:** `step-api`

**Region:** Choose closest to you (e.g., Oregon, Frankfurt)

**Branch:** `main` (or `master`)

**Root Directory:** Leave blank

**Runtime:** `Docker`

**Instance Type:** 
- **Free** (slower, sleeps after 15 min of inactivity) - Good for testing
- **Starter $7/month** (faster, always on) - Good for production

**Environment Variables:**
- Click **"Add Environment Variable"**
- Key: `PORT`, Value: `8000`

**Advanced:**
- **Health Check Path:** `/health`

### Step 6: Deploy!

1. Click **"Create Web Service"** at the bottom
2. Render will start building (takes 10-15 minutes first time)
3. Watch the logs - you'll see progress

When you see: `Deploy live for step-api` → **You're done!**

### Step 7: Get Your URL

At the top of the page, you'll see your URL:
`https://step-api.onrender.com`

Add `/docs` to test it:
`https://step-api.onrender.com/docs`

🎉 **Your API is live!**

---

## Free Tier vs Paid

### Free Tier ($0/month)
✅ 750 hours per month
✅ Perfect for testing/low traffic
❌ Spins down after 15 minutes of inactivity (first request takes 30-60 seconds to wake up)
❌ Limited to 512MB RAM

### Starter ($7/month)
✅ Always on
✅ 512MB RAM
✅ Good for production

### Standard ($25/month)
✅ 2GB RAM (needed for large STEP files)
✅ Better performance

---

## Managing Your API

### View Logs
- In Render dashboard → Click your service → "Logs" tab

### Update Your Code
1. Make changes to your GitHub repository
2. Render automatically rebuilds and redeploys!

### Manual Deploy
- Click **"Manual Deploy"** → "Deploy latest commit"

### Environment Variables
- Settings → Environment → Add/edit variables

### Custom Domain
- Settings → Add custom domain (free on all plans!)

---

## Important Notes

⚠️ **Free tier spins down after 15 min** - First request will be slow
💡 **Solution:** Use a service like UptimeRobot (free) to ping your API every 5 minutes to keep it awake

⚠️ **512MB RAM might not be enough** for very large STEP files
💡 **Solution:** Upgrade to Standard tier ($25/month) for 2GB RAM

---

## Troubleshooting

### Build Failed

**Problem:** Docker build timed out
**Solution:** Render free tier has build limits. Try deploying again, or upgrade to paid tier

### Out of Memory

**Problem:** Service crashes when processing large files
**Solution:** Upgrade to Standard tier (2GB RAM)

### Service Unreachable

**Problem:** Free tier spun down
**Solution:** 
- Wait 30-60 seconds for it to wake up
- Or set up UptimeRobot to keep it alive
- Or upgrade to paid tier

---

## Keep Free Tier Always On (Hack)

Use UptimeRobot to ping your API:

1. Go to: https://uptimerobot.com
2. Sign up free
3. Add new monitor:
   - **Type:** HTTP(s)
   - **URL:** `https://step-api.onrender.com/health`
   - **Interval:** 5 minutes
4. Your API will never sleep!

---

## Comparison: Render vs Railway vs Google Cloud

| Feature | Render | Railway | Google Cloud |
|---------|--------|---------|--------------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Free Tier** | ✅ Yes (limited) | $5 credit | ✅ Yes (generous) |
| **Setup Time** | 15 min | 5 min | 30 min |
| **Always On (Free)** | ❌ No | ✅ Yes* | ✅ Yes |
| **Custom Domain** | ✅ Free | ✅ Free | ✅ Free |
| **Best For** | Testing | Small projects | Production |

*Railway: Until $5 credit runs out

---

## My Recommendation

**For You (Non-Coder):**
1. **Start with Render Free Tier** - Easy setup, test it out
2. **If you like it:** Upgrade to Starter ($7/month) or Standard ($25/month)
3. **If traffic grows:** Move to Google Cloud Run (scales automatically, pay per use)

