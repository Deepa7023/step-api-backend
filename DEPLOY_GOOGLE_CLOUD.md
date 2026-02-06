# Deploy to Google Cloud Run - Step by Step Guide

Google Cloud Run is the EASIEST way to deploy your API to the web. It's free for small usage and handles everything automatically.

## What You'll Get

- A live URL like: `https://step-api-xyz123.run.app`
- Automatic scaling (handles traffic spikes)
- Free tier: 2 million requests/month
- No server management needed

## Prerequisites

- A Google account (Gmail account)
- A credit card (for verification only - won't be charged on free tier)

---

## Step 1: Set Up Google Cloud

1. Go to: https://console.cloud.google.com
2. Sign in with your Google account
3. Click **"Create Project"** at the top
4. Name it: `step-api` and click **Create**
5. Wait for the project to be created (30 seconds)

## Step 2: Enable Required Services

1. In the search bar at top, type: **"Cloud Run API"**
2. Click on it and click **ENABLE**
3. In the search bar, type: **"Cloud Build API"**
4. Click on it and click **ENABLE**

(These take about 1 minute to enable)

## Step 3: Open Cloud Shell

1. Look for the **">_"** icon in the top-right corner of the Google Cloud Console
2. Click it - a terminal will open at the bottom of your screen
3. This is Cloud Shell - it's like a computer in the cloud you can use for free!

## Step 4: Upload Your Files

In Cloud Shell, click the **3 dots** (⋮) menu and select **"Upload"**

Upload these files from your step-api-backend folder:
- The entire `app` folder (you might need to zip it first)
- `Dockerfile`
- `requirements.txt`
- `environment.yml`

**OR** you can clone directly if files are in GitHub (skip to Step 5)

## Step 5: Prepare Your Files in Cloud Shell

Type these commands one by one:

```bash
# Create project directory
mkdir step-api-backend
cd step-api-backend

# If you uploaded a zip file:
unzip step-api-backend.zip

# Or download directly (I'll create a public link for you)
```

## Step 6: Fix the Dockerfile for Cloud Run

Cloud Run needs a simpler Dockerfile. Run this command to create it:

```bash
cat > Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OCCT
RUN apt-get update && apt-get install -y \
    wget \
    bzip2 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install micromamba
RUN wget -qO- https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba

# Copy environment file
COPY environment.yml .

# Install packages using micromamba
RUN ./bin/micromamba create -y -f environment.yml && \
    ./bin/micromamba clean --all --yes

# Copy application
COPY ./app /app/app

# Expose port
ENV PORT=8080
EXPOSE 8080

# Run the app
CMD ./bin/micromamba run -n base uvicorn app.main:app --host 0.0.0.0 --port 8080
EOF
```

## Step 7: Deploy to Cloud Run

Run this ONE command (it does everything):

```bash
gcloud run deploy step-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300
```

This will:
- Build your Docker container
- Upload it to Google's servers
- Deploy it
- Give you a public URL

**This takes 5-10 minutes the first time.**

When it's done, you'll see:
```
Service [step-api] revision [step-api-00001-abc] has been deployed
Service URL: https://step-api-xyz123-uc.a.run.app
```

## Step 8: Test Your Live API!

Copy the URL from Step 7 and add `/docs` to the end:

**Example:** `https://step-api-xyz123-uc.a.run.app/docs`

Open that in your browser and you'll see your API documentation!

You can now upload STEP files from anywhere in the world!

---

## 🎉 You're Done!

Your API is now live on the internet at your Cloud Run URL!

**Share this URL** with anyone who needs to analyze STEP files.

---

## Costs

**Free Tier Includes:**
- 2 million requests per month
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds

**For typical usage:** This should be FREE or less than $5/month

---

## Managing Your API

### View Logs
```bash
gcloud run services logs read step-api --region us-central1
```

### Update Your API
After making code changes:
```bash
gcloud run deploy step-api --source . --region us-central1
```

### Delete Your API
If you want to shut it down:
```bash
gcloud run services delete step-api --region us-central1
```

---

## Troubleshooting

**"Permission denied"**
- Make sure billing is enabled on your Google Cloud project

**"Build failed"**
- Check the build logs in the Cloud Console
- The micromamba installation might need more time

**"Service unavailable"**
- The container might be too large
- Try increasing memory: add `--memory 4Gi`

---

## Need Help?

The most common issue is the first build timing out. If that happens:

1. Go to Cloud Build in the console
2. Look at the build logs
3. If it timed out, just run the deploy command again

---

## Alternative: Use a Pre-built Image

If building is too slow, I can create a pre-built Docker image for you that you can deploy instantly. Just let me know!

