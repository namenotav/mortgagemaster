# 🚀 MortgageMaster Deployment Guide

## Quick Deploy Options

### Option 1: Railway (RECOMMENDED - Easiest!)
### Option 2: Heroku (Classic option)

---

## ✅ Pre-Deployment Checklist

Before deploying, make sure you have:
- [x] Fixed all security issues ✅
- [x] Pushed code to GitHub ✅
- [ ] Stripe account with API keys
- [ ] Gmail account for sending emails
- [ ] Choose deployment platform (Railway or Heroku)

---

# 🚂 RAILWAY DEPLOYMENT (RECOMMENDED)

## Step 1: Create Railway Account

1. Go to https://railway.app
2. Click "Login with GitHub"
3. Authorize Railway to access your GitHub

## Step 2: Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Select your repository: `namenotav/mortgagemaster`
4. Railway will automatically detect it's a Python app

## Step 3: Set Environment Variables

In Railway dashboard, go to your project → Variables tab and add:

```bash
# Required Variables
FLASK_ENV=production
SECRET_KEY=<generate-new-key-below>
STRIPE_SECRET_KEY=sk_live_YOUR_KEY_HERE
STRIPE_PUBLIC_KEY=pk_live_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET
STRIPE_YEARLY_PRICE_ID=price_1STXcVD2EDcoPFLNECjwrN1p
STRIPE_MONTHLY_PRICE_ID=price_1STXbDD2EDcoPFLN6hEU2gS9
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
SITE_URL=https://your-app.up.railway.app
SCHEDULER_ENABLED=1
```

### How to Generate SECRET_KEY:

Run this on your computer:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output and paste it as SECRET_KEY

## Step 4: Database Setup

Railway will automatically provision a PostgreSQL database:
1. In Railway, click "New" → "Database" → "Add PostgreSQL"
2. Railway automatically sets DATABASE_URL - you don't need to do anything!

## Step 5: Deploy!

Railway automatically deploys when you push to GitHub. Your app will be live at:
`https://your-app-name.up.railway.app`

## Step 6: Configure Stripe Webhook

1. Copy your Railway app URL (e.g., `https://your-app.up.railway.app`)
2. Go to Stripe Dashboard → Developers → Webhooks
3. Click "Add endpoint"
4. Webhook URL: `https://your-app.up.railway.app/stripe-webhook`
5. Events to send: Select `checkout.session.completed`
6. Copy the webhook signing secret
7. Add it to Railway environment variables as `STRIPE_WEBHOOK_SECRET`

## Step 7: Set Up Gmail App Password

1. Go to https://myaccount.google.com/security
2. Enable "2-Step Verification" (if not already)
3. Go to "App passwords"
4. Create new app password for "Mail"
5. Copy the 16-character password
6. Add it to Railway as `EMAIL_PASSWORD`

---

# 🟣 HEROKU DEPLOYMENT (ALTERNATIVE)

## Step 1: Install Heroku CLI

Download from: https://devcenter.heroku.com/articles/heroku-cli

## Step 2: Login to Heroku

```bash
heroku login
```

## Step 3: Create Heroku App

```bash
cd C:\Users\Admin\Desktop\MortgageMaster
heroku create your-app-name
```

## Step 4: Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:mini
```

## Step 5: Set Environment Variables

```bash
# Generate SECRET_KEY first
python -c "import secrets; print(secrets.token_hex(32))"

# Then set all variables
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=<paste-generated-key>
heroku config:set STRIPE_SECRET_KEY=sk_live_YOUR_KEY
heroku config:set STRIPE_PUBLIC_KEY=pk_live_YOUR_KEY
heroku config:set STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET
heroku config:set STRIPE_YEARLY_PRICE_ID=price_1STXcVD2EDcoPFLNECjwrN1p
heroku config:set STRIPE_MONTHLY_PRICE_ID=price_1STXbDD2EDcoPFLN6hEU2gS9
heroku config:set EMAIL_USERNAME=your-email@gmail.com
heroku config:set EMAIL_PASSWORD=your-gmail-app-password
heroku config:set SCHEDULER_ENABLED=1
```

## Step 6: Deploy to Heroku

```bash
git push heroku claude/review-production-readiness-01KRQLaTnL6KHKk77QamRt82:main
```

## Step 7: Open Your App

```bash
heroku open
```

## Step 8: Configure Stripe Webhook

Same as Railway Step 6 above, but use your Heroku URL:
`https://your-app-name.herokuapp.com/stripe-webhook`

---

# 🔑 Getting Your Stripe Keys

## For Testing (Stripe Test Mode):
1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy "Publishable key" → Use as STRIPE_PUBLIC_KEY
3. Copy "Secret key" → Use as STRIPE_SECRET_KEY

## For Production (Stripe Live Mode):
1. Go to https://dashboard.stripe.com/apikeys
2. Activate your account (requires business details)
3. Copy "Publishable key" → Use as STRIPE_PUBLIC_KEY
4. Copy "Secret key" → Use as STRIPE_SECRET_KEY

⚠️ **IMPORTANT**: Your old Stripe keys were exposed in git. You MUST:
1. Go to https://dashboard.stripe.com/apikeys
2. Click the "..." menu next to your secret key
3. Click "Roll key" to generate new keys
4. Use the NEW keys for deployment

---

# 🧪 Testing After Deployment

## 1. Check Health Endpoint
Visit: `https://your-app.com/healthz`
Should show: `ok`

## 2. Test Homepage
Visit: `https://your-app.com`
Should load without errors

## 3. Test Signup
1. Create a new account
2. Check password requirements work
3. Verify you can login

## 4. Test Payment (Stripe Test Mode)
1. Login to your account
2. Go to /upgrade
3. Click "Upgrade for £49"
4. Use test card: 4242 4242 4242 4242, any future date, any CVC
5. Complete payment
6. Check webhook received in Stripe dashboard
7. Verify PRO status in your dashboard

## 5. Test Search
1. Go to homepage
2. Enter property details
3. Click "Find My Best Deals"
4. Should show search results

---

# 🛠️ Troubleshooting

## Error: "SECRET_KEY environment variable must be set"
**Fix**: Make sure you set SECRET_KEY in environment variables

## Error: "Module not found"
**Fix**: Make sure requirements.txt is in your repository

## Database errors
**Fix**: Railway/Heroku should auto-provision database. Check DATABASE_URL is set.

## Stripe payments not working
**Fix**:
1. Check STRIPE_SECRET_KEY is set correctly
2. Verify webhook is configured in Stripe dashboard
3. Check webhook secret matches STRIPE_WEBHOOK_SECRET

## CSRF errors on forms
**Fix**: Make sure WTF_CSRF_ENABLED=True in config (it is by default)

## Rate limiting errors
**Fix**: This is normal for development. In production, rate limits are per-IP.

---

# 📊 Monitoring Your App

## Railway:
- Go to Railway dashboard → Your project → Logs
- View real-time logs and errors

## Heroku:
```bash
heroku logs --tail
```

---

# 🔒 Security Checklist Before Going Live

- [x] Secrets removed from git
- [ ] New Stripe keys generated
- [ ] SECRET_KEY generated and set
- [ ] FLASK_ENV=production
- [ ] Stripe webhook configured
- [ ] Gmail app password set
- [ ] Test payment flow works
- [ ] Test signup/login works
- [ ] HTTPS enabled (automatic on Railway/Heroku)

---

# 🎉 You're Ready!

Your app is now secure and ready for production. Choose Railway for the easiest deployment!

**Recommended: Start with Railway + Stripe Test Mode, then switch to Live Mode when ready.**
