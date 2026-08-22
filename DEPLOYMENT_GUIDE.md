# VolHedge Pro - Netlify + Railway Deployment Guide

This guide explains how to deploy VolHedge Pro with:
- **Frontend** on Netlify (free)
- **Backend API** on Railway (free tier, $5/month after)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR USERS' BROWSER                      │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ VolHedge Pro Frontend (Netlify)                      │   │
│  │ - HTML/CSS/JavaScript                               │   │
│  │ - Real-time UI updates                              │   │
│  │ URL: https://volhedge-pro.netlify.app               │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↕ (API + WebSocket)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ VolHedge Pro Backend (Railway)                       │   │
│  │ - Python FastAPI Server                             │   │
│  │ - Greeks calculations                               │   │
│  │ - Portfolio management                              │   │
│  │ URL: https://your-app.railway.app                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Deploy Backend on Railway

### 1.1 Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Click **"Start New Project"**
3. Sign up with GitHub

### 1.2 Deploy the Backend
1. Click **"Deploy from GitHub"**
2. Select your repository: `jvkoyani/claude`
3. Select branch: `claude/app-from-markdown-0fpli3`
4. Railway auto-detects Python and deploys automatically ✅

### 1.3 Get Your Backend URL
1. After deployment completes, go to **"Settings"** → **"Networking"**
2. Copy the public URL (e.g., `https://volhedge-pro-prod.railway.app`)
3. Save this URL - you'll need it for the frontend

### 1.4 Configure Environment (Optional)
Add these environment variables in Railway Settings:

```
API_PORT=8000
FYERS_MOCK_MODE=true
```

---

## Step 2: Deploy Frontend on Netlify

### 2.1 Create Netlify Account
1. Go to [netlify.com](https://netlify.com)
2. Click **"Sign up"** and connect GitHub

### 2.2 Deploy the Frontend
1. Click **"Import an existing project"**
2. Select your repository: `jvkoyani/claude`
3. **Build command:** Leave empty (it's a static site)
4. **Publish directory:** `static`
5. Click **"Deploy"** ✅

### 2.3 Configure Your Backend URL
1. After deployment, go to **Site Settings** → **Environment**
2. Add environment variable:
   ```
   REACT_APP_API_URL=https://your-railway-url
   ```
3. Or manually configure in the app:
   - Click **"⚙ Backend Config"** button in the app
   - Enter your Railway backend URL
   - Click **"Save Configuration"**

### 2.4 Get Your Frontend URL
Your site is now live at a URL like:
```
https://your-site.netlify.app
```

---

## Step 3: Connect Frontend ↔ Backend

### Option A: Automatic (Recommended)
1. Open your Netlify app
2. Click **"⚙ Backend Config"** button
3. Paste your Railway URL:
   ```
   https://volhedge-pro-prod.railway.app
   ```
4. Click **"Save Configuration"**
5. App reloads and connects to backend ✅

### Option B: Environment Variable
1. In Netlify Site Settings → Environment
2. Add: `REACT_APP_API_URL=https://your-railway-url`
3. Redeploy site

### Option C: Manual (Testing Locally)
1. Uncomment this in `static/index.html`:
   ```javascript
   window.__VOLHEDGE_CONFIG__ = {
       API_BASE_URL: 'https://your-railway-url',
       WS_PROTOCOL: 'wss:'
   };
   ```

---

## Complete Setup Checklist

- [ ] Railway account created
- [ ] GitHub connected to Railway
- [ ] Backend deployed on Railway
- [ ] Backend URL copied (e.g., `https://volhedge-xxx.railway.app`)
- [ ] Netlify account created
- [ ] GitHub connected to Netlify
- [ ] Frontend deployed on Netlify
- [ ] Netlify deployment URL copied (e.g., `https://volhedge-pro.netlify.app`)
- [ ] Backend URL configured in frontend
- [ ] Test: Click "Backend Config" and verify connection
- [ ] Test: Add a position and verify data saves
- [ ] Test: WebSocket updates (portfolio metrics update every 3s)

---

## Testing the Deployment

### 1. Test API Connection
```bash
# Test from browser console
fetch('https://your-railway-url/api/tabs')
  .then(r => r.json())
  .then(d => console.log(d))
```

### 2. Test WebSocket
```bash
# Browser console
ws = new WebSocket('wss://your-railway-url/ws')
ws.onmessage = (e) => console.log(JSON.parse(e.data))
```

### 3. Full App Test
1. Navigate to your Netlify URL
2. Click **"⚙ Backend Config"**
3. Enter Railway URL
4. Click **"+ Add Position"**
5. Fill in details and submit
6. Verify position appears in table

---

## Troubleshooting

### "CORS Error" or "Failed to fetch"
**Cause:** Backend URL not correctly configured
**Fix:**
1. Click **"⚙ Backend Config"**
2. Verify URL format: `https://your-railway-url` (no trailing slash)
3. Check Railway app is still running

### "WebSocket connection failed"
**Cause:** WebSocket URL incorrect
**Fix:**
1. Railway URL should use `wss://` (secure WebSocket)
2. Check Railway networking settings

### "Cannot find portfolio data"
**Cause:** Portfolio JSON not syncing
**Fix:**
1. Ensure Railway backend is running
2. Check browser console for errors
3. Try manual refresh

### "Netlify shows 404 on refresh"
**Cause:** SPA routing not configured
**Fix:**
1. Check `_redirects` file exists in `static/` folder
2. Redeploy on Netlify

---

## Custom Domain (Optional)

### Netlify Custom Domain
1. Site Settings → Domain management
2. Add custom domain (e.g., `volhedge.yoursite.com`)
3. Update DNS records per Netlify instructions

### Railway Custom Domain
1. Settings → Custom Domain
2. Add your domain
3. Update DNS records

---

## Cost Summary

| Service | Free Tier | Paid |
|---------|-----------|------|
| **Netlify** | ✅ Unlimited | Not needed for frontend |
| **Railway** | ✅ $5/month credit | $0.50/hour active |
| **Total** | **FREE** | **~$5/month** |

---

## Environment Variables Reference

### Frontend (Netlify)
```
REACT_APP_API_URL=https://your-railway-url
```

### Backend (Railway)
```
FYERS_MOCK_MODE=true
API_PORT=8000
HOST=0.0.0.0
```

---

## Updating the App

### Update Backend
1. Push changes to your branch
2. Railway auto-deploys
3. Wait for green status ✅

### Update Frontend
1. Push changes to your branch
2. Netlify auto-deploys
3. Wait for green status ✅

Both update independently - no downtime!

---

## Support Resources

- **Railway Docs:** https://docs.railway.app
- **Netlify Docs:** https://docs.netlify.com
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **GitHub Issues:** Your repo issues page

---

## Security Notes

- ✅ CORS enabled for all origins (safe for Netlify)
- ✅ No sensitive data in frontend
- ✅ API tokens stored server-side (Railway backend)
- ⚠️ Change `allow_origins=["*"]` to specific domains in production

---

**You're all set! Your VolHedge Pro trading terminal is now live!** 🚀
