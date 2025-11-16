# 🚀 Quick Deploy Guide for mortgagedealshub.co.uk

## ⚡ FAST TRACK DEPLOYMENT (15 minutes)

You already own the domain, so let's get your site live!

---

## STEP 1: Generate Your Secret Keys (2 minutes)

On your Windows machine, run these commands one by one:

```powershell
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```
**Save this output** - you'll need it in Step 3

---

## STEP 2: Get Your Stripe Keys (3 minutes)

### ⚠️ IMPORTANT: Your old Stripe keys were exposed in git!

1. Go to https://dashboard.stripe.com/test/apikeys
2. Click on "Reveal test key" for the Secret key
3. Click the **"..."** menu → **"Roll key"** to generate a NEW secret key
4. **Copy both:**
   - Publishable key (starts with `pk_test_`)
   - Secret key (starts with `sk_test_`)

---

## STEP 3: Get Gmail App Password (3 minutes)

1. Go to https://myaccount.google.com/security
2. Make sure "2-Step Verification" is ON
3. Search for "App passwords" on the page
4. Click "App passwords"
5. Select "Mail" and give it a name like "MortgageMaster"
6. Click "Generate"
7. **Copy the 16-character password**

---

## STEP 4: Deploy to Railway (5 minutes)

### A. Create Account & Project
1. Go to **https://railway.app**
2. Click **"Login with GitHub"**
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose **`namenotav/mortgagemaster`**
6. Select branch: **`claude/review-production-readiness-01KRQLaTnL6KHKk77QamRt82`**

### B. Add PostgreSQL Database
1. In Railway, click **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Done! Railway auto-connects it.

### C. Configure Environment Variables
1. Click on your **web service** (the Python app, not the database)
2. Go to **"Variables"** tab
3. Click **"RAW Editor"** (top right)
4. **Copy and paste this**, then replace the placeholders:

```bash
FLASK_ENV=production
SECRET_KEY=paste_your_generated_key_from_step_1
STRIPE_SECRET_KEY=sk_test_paste_from_step_2
STRIPE_PUBLIC_KEY=pk_test_paste_from_step_2
STRIPE_WEBHOOK_SECRET=leave_empty_for_now
STRIPE_YEARLY_PRICE_ID=price_1STXcVD2EDcoPFLNECjwrN1p
STRIPE_MONTHLY_PRICE_ID=price_1STXbDD2EDcoPFLN6hEU2gS9
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=paste_16_char_password_from_step_3
SITE_URL=https://mortgagedealshub.co.uk
SCHEDULER_ENABLED=1
```

5. Click **"Deploy"**

### D. Wait for Deployment
- Watch the **"Deployments"** tab
- Wait for green checkmark (about 2 minutes)
- You'll get a temporary URL like: `mortgagemaster-production-xxxx.up.railway.app`

---

## STEP 5: Connect Your Domain mortgagedealshub.co.uk (3 minutes)

### A. Add Domain in Railway
1. In Railway, go to your service → **"Settings"** tab
2. Scroll to **"Domains"** section
3. Click **"Custom Domain"**
4. Enter: **`mortgagedealshub.co.uk`**
5. Railway will show you DNS records to add

### B. Update DNS Records

**Where did you buy your domain?** (Namecheap, GoDaddy, Cloudflare, etc.)

Go to your domain registrar's DNS settings and add these records:

**For Root Domain (mortgagedealshub.co.uk):**
```
Type: CNAME
Name: @ (or leave blank)
Value: [Railway will give you this - looks like: xxxx.up.railway.app]
```

**For WWW subdomain (optional):**
```
Type: CNAME
Name: www
Value: mortgagedealshub.co.uk
```

**DNS propagation takes 5-60 minutes.** You can check status at: https://dnschecker.org

---

## STEP 6: Configure Stripe Webhook (2 minutes)

Once your domain is working:

1. Go to https://dashboard.stripe.com/test/webhooks
2. Click **"Add endpoint"**
3. **Endpoint URL:** `https://mortgagedealshub.co.uk/stripe-webhook`
4. Click **"Select events"**
5. Choose: **`checkout.session.completed`**
6. Click **"Add endpoint"**
7. Click on your new webhook
8. Click **"Reveal"** next to "Signing secret"
9. **Copy the secret** (starts with `whsec_`)
10. Go to Railway → Variables → Update `STRIPE_WEBHOOK_SECRET` with this value
11. Railway will auto-redeploy

---

## STEP 7: TEST YOUR LIVE SITE! 🎉

### Test 1: Visit Your Domain
Go to: **https://mortgagedealshub.co.uk**

If you see your site → SUCCESS! ✅

If you see "DNS not found" → Wait a bit longer (DNS propagation)

### Test 2: Create Account
1. Click **"Sign Up"**
2. Create account with a strong password
3. Login

### Test 3: Test Payment (Using Stripe Test Mode)
1. Login
2. Click **"Upgrade"**
3. Choose a plan
4. Use test card: **4242 4242 4242 4242**
5. Any future expiry date
6. Any 3-digit CVC
7. Complete payment
8. Check dashboard - you should be **PRO** within 5 seconds!

### Test 4: Verify Webhook Worked
1. Stripe Dashboard → Webhooks
2. Click your webhook
3. You should see **"✓ Succeeded"** events

---

## 🎯 YOUR SITE IS LIVE!

**Your mortgage comparison site is now running at:**
### **https://mortgagedealshub.co.uk** 🚀

---

## 📊 What's Next?

### To Switch from Test Mode to Live Mode (When Ready):

1. **Activate Your Stripe Account:**
   - Stripe Dashboard → Complete business verification
   - Add bank details

2. **Get Live API Keys:**
   - Go to https://dashboard.stripe.com/apikeys (not /test/)
   - Copy Live keys (start with `pk_live_` and `sk_live_`)

3. **Update Railway Variables:**
   - Change `STRIPE_SECRET_KEY` to live key
   - Change `STRIPE_PUBLIC_KEY` to live key
   - Update webhook to use live mode

4. **Update Stripe Products:**
   - Create products in Live mode
   - Update `STRIPE_YEARLY_PRICE_ID` and `STRIPE_MONTHLY_PRICE_ID`

---

## 🔄 How to Update Your Site Later

Whenever you make changes:

```powershell
cd C:\Users\Admin\Desktop\MortgageMaster
git add .
git commit -m "Your change description"
git push origin claude/review-production-readiness-01KRQLaTnL6KHKk77QamRt82
```

Railway automatically deploys in ~2 minutes! ✅

---

## 💰 Cost Estimate

**Railway Pricing:**
- Free tier: $0/month (includes $5 credit)
- Hobby plan: $5/month (for production sites)
- Your site will likely use: ~$3-8/month depending on traffic

**Stripe Pricing:**
- Free to use
- 1.5% + 20p per successful card charge (UK pricing)

---

## 🆘 Troubleshooting

**Domain not working after 1 hour?**
- Check DNS records are correct in your registrar
- Use https://dnschecker.org to verify propagation
- Make sure you used CNAME, not A record

**Payments not granting PRO access?**
- Check Stripe webhook is configured correctly
- Check webhook secret matches in Railway variables
- View Railway logs for errors

**Can't log in?**
- Make sure password meets requirements (8+ chars, uppercase, lowercase, number)

**Need help?**
- Check Railway logs: Dashboard → Deployments → View logs
- Check this repository's issues

---

## 🎉 YOU'RE DONE!

Your secure, production-ready mortgage comparison site is live!
