# Deploy to Railway.app - EASIEST Option (5 Minutes!)

Railway is the ABSOLUTE EASIEST way to deploy. No command line needed!

## What You'll Get

- Live URL like: `https://step-api.up.railway.app`
- Automatic HTTPS
- Free tier: $5 credit per month (usually enough)
- Automatic deployments

---

## Step-by-Step (No Coding Required!)

### Step 1: Create Railway Account

1. Go to: https://railway.app
2. Click **"Start a New Project"** (or "Login with GitHub")
3. Sign up with GitHub, Google, or Email
4. **Important:** Add a credit card (required, but won't charge you on free tier)

### Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Empty Project"**
3. Name it: `step-api`

### Step 3: Add a Service

1. Click **"+ New"**
2. Select **"Empty Service"**
3. Name it: `api`

### Step 4: Upload Your Files

Unfortunately Railway doesn't have direct file upload. You have **two options**:

#### Option A: Use GitHub (Recommended)

1. Create a free GitHub account: https://github.com
2. Click **"+ New"** → **"Repository"**
3. Name it `step-api-backend`
4. Upload all your files to the repository
5. In Railway, click **"+ New"** → **"GitHub Repo"**
6. Select your `step-api-backend` repository

#### Option B: Use Railway CLI (Slightly Technical)

1. Install Railway CLI:
   - **Mac:** `brew install railway`
   - **Windows:** Download from https://railway.app/cli
   
2. In your step-api-backend folder, run:
```bash
railway login
railway link
railway up
```

### Step 5: Configure Settings

After connecting your code:

1. Click on your service
2. Go to **"Settings"** tab
3. Set these **Environment Variables**:
   - Click **"+ New Variable"**
   - Name: `PORT`, Value: `8000`

4. Under **"Deploy"** section:
   - **Build Command:** Leave empty (Docker handles it)
   - **Start Command:** Leave empty (Docker handles it)

5. Click **"Generate Domain"** under **"Networking"**
   - This gives you a public URL

### Step 6: Deploy!

Railway will automatically:
- Build your Docker container
- Deploy it
- Give you a URL

**Wait 5-10 minutes for first build**

### Step 7: Test It!

1. Copy your Railway URL (looks like: `https://step-api.up.railway.app`)
2. Add `/docs` to the end
3. Open in browser: `https://step-api.up.railway.app/docs`

🎉 **Your API is live!**

---

## Costs

**Free Tier:**
- $5 credit per month
- Usually enough for small-medium usage
- After that: ~$0.000463 per hour when running

**Typical cost:** $0-10/month

---

## Managing Your API

### View Logs
- Click on your service → **"Deployments"** → Click latest deployment → See logs

### Update Your Code
- Just push to GitHub (if using GitHub)
- Or run `railway up` (if using CLI)
- Automatic redeployment!

### Pause/Delete
- Click service → **"Settings"** → **"Pause Service"** or **"Delete Service"**

---

## Troubleshooting

**Build Failed?**
- Check build logs in Railway dashboard
- Common issue: Dockerfile needs internet to download packages
- Solution: Wait and try redeploying (Railway has better servers)

**Out of Memory?**
- Railway gives 8GB RAM by default, should be plenty
- If needed, upgrade plan

**Need Custom Domain?**
- Railway Settings → Domains → Add your own domain

---

## Why Railway vs Google Cloud?

**Railway Pros:**
✅ Super easy web interface
✅ No command line needed
✅ Auto-deploys from GitHub
✅ Beautiful dashboard

**Railway Cons:**
❌ Costs more than Google Cloud free tier
❌ $5/month credit limit

**Google Cloud Pros:**
✅ More generous free tier
✅ Better for high traffic

**Google Cloud Cons:**
❌ Requires command line
❌ More complex setup

---

**My Recommendation:** Start with Railway for simplicity. If you get lots of traffic, move to Google Cloud later.

