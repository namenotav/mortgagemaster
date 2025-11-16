# ✅ Deployment Checklist - DO THIS IN ORDER

Follow these steps **exactly** - check them off as you go!

---

## 📋 PRE-DEPLOYMENT (5 minutes)

### ☐ Step 1: Pull Latest Code
On your Windows computer:
```powershell
cd C:\Users\Admin\Desktop\MortgageMaster
git pull origin claude/review-production-readiness-01KRQLaTnL6KHKk77QamRt82
```

### ☐ Step 2: Run Helper Script
```powershell
.\deploy-helper.bat
```

This will:
- Generate your SECRET_KEY
- Open browser windows for Stripe, Gmail, and Railway
- Save the SECRET_KEY to `.secret_key.txt`

**IMPORTANT:** Keep the `.secret_key.txt` file open - you'll need it!

---

## 🔑 GET YOUR CREDENTIALS (5 minutes)

### ☐ Step 3: Get New Stripe Keys

Browser window should be open at: https://dashboard.stripe.com/test/apikeys

1. Click "Reveal test key token" for Secret key
2. Click the **"..."** menu → **"Roll key"** (IMPORTANT - old keys were exposed!)
3. Copy the NEW Secret key (starts with `sk_test_`)
4. Copy the Publishable key (starts with `pk_test_`)
5. **Paste both into a notepad** - you'll need them!

### ☐ Step 4: Get Gmail App Password

Browser window should be open at: https://myaccount.google.com/security

1. Make sure "2-Step Verification" is ON (turn it on if needed)
2. Search for "App passwords" on the page
3. Click "App passwords"
4. Select "Mail" → Give it a name "MortgageMaster"
5. Click "Generate"
6. **Copy the 16-character password** (looks like: `abcd efgh ijkl mnop`)
7. **Remove the spaces** - should be: `abcdefghijklmnop`
8. **Paste into notepad** - you'll need it!

---

## 🚂 DEPLOY TO RAILWAY (7 minutes)

### ☐ Step 5: Create Railway Project

Browser window should be open at: https://railway.app

1. Click **"Login with GitHub"**
2. Authorize Railway
3. Click **"New Project"**
4. Click **"Deploy from GitHub repo"**
5. Select: **`namenotav/mortgagemaster`**
6. For branch, select: **`claude/review-production-readiness-01KRQLaTnL6KHKk77QamRt82`**
7. Click **"Deploy"**

### ☐ Step 6: Add PostgreSQL Database

1. In your Railway project, click **"New"**
2. Click **"Database"**
3. Click **"Add PostgreSQL"**
4. Wait 30 seconds for it to provision
5. Done! (Railway auto-connects it)

### ☐ Step 7: Set Environment Variables

1. Click on your **web service** (NOT the database - it's the Python one)
2. Click **"Variables"** tab
3. Click **"RAW Editor"** button (top right)
4. Open the file: **`railway-env-template.txt`** (in your project folder)
5. Replace all the `[BRACKETED]` values with your actual values:
   - SECRET_KEY from `.secret_key.txt`
   - STRIPE keys from Step 3
   - EMAIL_PASSWORD from Step 4
   - EMAIL_USERNAME with your Gmail address
6. **Copy the entire edited content**
7. **Paste into Railway Raw Editor**
8. Click anywhere outside the editor to save
9. Railway will automatically start deploying!

### ☐ Step 8: Wait for Deployment

1. Click **"Deployments"** tab
2. Watch the logs scroll
3. Wait for **green checkmark** (takes 2-3 minutes)
4. You'll see a URL like: `mortgagemaster-production-xxxx.up.railway.app`
5. **Click the URL** to test it
6. If you see your site → SUCCESS! ✅

---

## 🌐 CONNECT YOUR DOMAIN (5 minutes)

### ☐ Step 9: Add Custom Domain in Railway

1. In Railway, click on your service → **"Settings"** tab
2. Scroll to **"Domains"** section
3. Click **"Custom Domain"**
4. Enter: **`mortgagedealshub.co.uk`**
5. Railway will show you a CNAME record to add

**It will look like:**
```
Type: CNAME
Name: @ or mortgagedealshub.co.uk
Value: mortgagemaster-production-xxxx.up.railway.app
```

### ☐ Step 10: Update DNS Records

**Where did you buy mortgagedealshub.co.uk?**

Choose your registrar:

#### If Namecheap:
1. Go to https://www.namecheap.com
2. Dashboard → Domain List → Manage next to mortgagedealshub.co.uk
3. Advanced DNS tab
4. Add New Record:
   - Type: **CNAME Record**
   - Host: **@**
   - Value: **[paste Railway's value]**
   - TTL: **Automatic**
5. Save

#### If GoDaddy:
1. Go to https://www.godaddy.com/
2. My Products → DNS
3. Add → CNAME
   - Name: **@**
   - Value: **[paste Railway's value]**
   - TTL: **1 Hour**
4. Save

#### If Cloudflare:
1. Go to https://dash.cloudflare.com
2. Select mortgagedealshub.co.uk
3. DNS → Add record
   - Type: **CNAME**
   - Name: **@**
   - Target: **[paste Railway's value]**
   - Proxy: **ON** (orange cloud)
4. Save

#### Other registrars:
Look for "DNS Management" or "DNS Settings" and add a CNAME record as shown above.

### ☐ Step 11: Wait for DNS Propagation

- DNS changes take **5-60 minutes**
- Check progress at: https://dnschecker.org/#CNAME/mortgagedealshub.co.uk
- Once you see green checkmarks worldwide, continue!

---

## 🔗 CONFIGURE STRIPE WEBHOOK (3 minutes)

### ☐ Step 12: Set Up Webhook

**IMPORTANT:** Only do this after your domain is working!

1. Go to https://dashboard.stripe.com/test/webhooks
2. Click **"Add endpoint"**
3. Endpoint URL: **`https://mortgagedealshub.co.uk/stripe-webhook`**
4. Click **"Select events"**
5. Search for and check: **`checkout.session.completed`**
6. Click **"Add endpoint"**
7. Click on your newly created webhook
8. Click **"Reveal"** next to "Signing secret"
9. **Copy the secret** (starts with `whsec_`)

### ☐ Step 13: Update Railway with Webhook Secret

1. Go back to Railway
2. Click your service → **"Variables"**
3. Find **`STRIPE_WEBHOOK_SECRET`**
4. Paste the webhook secret you just copied
5. Railway will automatically redeploy (takes 1-2 minutes)

---

## 🧪 FINAL TESTING (5 minutes)

### ☐ Step 14: Test Your Live Site!

1. Visit: **https://mortgagedealshub.co.uk**
2. You should see your homepage ✅

### ☐ Step 15: Test Signup

1. Click **"Sign Up"**
2. Create account:
   - Name: Your name
   - Email: your email
   - Password: **MUST have 8+ chars, 1 uppercase, 1 lowercase, 1 number**
   - Example good password: `Test1234`
3. Login with your new account

### ☐ Step 16: Test Payment (FREE - Test Mode!)

1. Login to your account
2. Click **"Upgrade"** or **"See Pro Plans"**
3. Choose any plan
4. Use Stripe test card:
   - Card number: **4242 4242 4242 4242**
   - Expiry: **12/34** (any future date)
   - CVC: **123** (any 3 digits)
   - ZIP: **12345** (any 5 digits)
5. Complete payment
6. You should see "Thank you" message
7. **Wait 5 seconds** then refresh your dashboard
8. You should now be **PRO** member! ✅

### ☐ Step 17: Verify Webhook

1. Go to Stripe Dashboard → Webhooks
2. Click on your webhook
3. You should see **"✓ Succeeded"** events
4. If you see this → Everything works! ✅

---

## ✅ YOU'RE LIVE!

# 🎉 **Your site is now running at:**
# **https://mortgagedealshub.co.uk**

---

## 📊 What's Next?

### Want to go LIVE (accept real payments)?

When you're ready to accept real money:

1. **Complete Stripe verification:**
   - Stripe Dashboard → Activate your account
   - Add business details
   - Add bank account

2. **Get LIVE API keys:**
   - https://dashboard.stripe.com/apikeys (not /test/)
   - Copy Live keys (start with `pk_live_` and `sk_live_`)

3. **Update Railway:**
   - Variables → Change to LIVE keys
   - Update STRIPE_SECRET_KEY
   - Update STRIPE_PUBLIC_KEY

4. **Create products in Live mode:**
   - Create your £49 yearly plan
   - Create your £14.99 monthly plan
   - Update STRIPE_YEARLY_PRICE_ID and STRIPE_MONTHLY_PRICE_ID

5. **Update webhook to Live mode:**
   - Create new webhook in Live mode
   - Update STRIPE_WEBHOOK_SECRET

---

## 🔄 How to Update Your Site

Whenever you want to make changes:

```powershell
cd C:\Users\Admin\Desktop\MortgageMaster
# Make your changes to files
git add .
git commit -m "Description of changes"
git push origin claude/review-production-readiness-01KRQLaTnL6KHKk77QamRt82
```

Railway deploys automatically in ~2 minutes!

---

## 💰 Costs

**Railway:**
- Free tier: $5 credit/month (likely enough for low traffic)
- Hobby: $5/month (for production)
- Your site will use ~$3-8/month

**Stripe:**
- Free to use
- 1.5% + 20p per successful card payment (UK)

**Domain:**
- You already own it! ✅

---

## 🆘 Troubleshooting

**Can't access site after 1 hour?**
- Check DNS settings in your registrar
- Verify CNAME record is correct
- Check https://dnschecker.org

**Payments not working?**
- Verify webhook secret is correct
- Check Railway logs for errors
- Verify Stripe test mode keys are being used

**Can't create account?**
- Password must have 8+ chars, uppercase, lowercase, number
- Try: `Password123`

**Need to see logs?**
- Railway → Deployments → Click latest deployment → View logs

---

## ✅ FINAL CHECKLIST

Before telling people about your site:

- ☐ Site loads at https://mortgagedealshub.co.uk
- ☐ Can create account
- ☐ Can login
- ☐ Can search for mortgages
- ☐ Test payment works
- ☐ PRO access granted after payment
- ☐ All forms work
- ☐ No errors in Railway logs

**IF ALL CHECKED → YOU'RE READY TO LAUNCH!** 🚀
