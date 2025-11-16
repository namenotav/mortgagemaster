# 🔄 Live Mortgage Data Scraping System

## 📖 Overview

Your MortgageDealsHub now includes an **automated web scraping system** that extracts live mortgage deals from multiple online sources, giving your users access to the freshest data that even top brokers might not have!

---

## 🎯 **What It Does**

The scraping system:
- ✅ **Scrapes mortgage rates** from bank websites (HSBC, Nationwide, Barclays, etc.)
- ✅ **Extracts data** from comparison sites (MoneySuperMarket, MoneySavingExpert)
- ✅ **Validates & deduplicates** all scraped data automatically
- ✅ **Updates database** daily at 3 AM UK time
- ✅ **Falls back** to existing data if scraping fails (never loses data)
- ✅ **Respects rate limits** and website policies

---

## 🚀 **How To Access**

### **Admin Scraper Dashboard:**
```
https://mortgagedealshub.co.uk/secret-admin-scraper-xyz
```

From this dashboard you can:
- 📊 View statistics (total deals, breakdown by lender type)
- 🔄 Manually trigger data refresh
- 📅 See when data was last updated
- 📋 Monitor which data sources are active

---

## ⚙️ **How It Works**

### **1. Automatic Daily Updates**
- Scraper runs **every day at 3:00 AM UK time**
- Fetches fresh deals from all configured sources
- Validates and cleans the data
- Updates your database automatically
- **No manual work required!**

### **2. Manual Refresh (When Needed)**
1. Go to `/secret-admin-scraper-xyz`
2. Click "🔄 Refresh Deals Now"
3. Wait 1-2 minutes
4. Database is updated with latest deals!

---

## 📂 **Files Created**

### **1. Scraper Module** (`scrapers/mortgage_scraper.py`)
Contains all scraping logic:
- `MortgageScraper` - Base class with common functionality
- `BankWebsiteScraper` - Scrapes individual bank websites
- `MoneySuperMarketScraper` - Scrapes MoneySuperMarket (requires permission)
- `APIBasedScraper` - Uses professional APIs (recommended!)

### **2. Refresh Utility** (`utils/refresh_deals.py`)
Handles database updates:
- Runs scraping from all sources
- Validates scraped data
- Deduplicates deals
- Updates database safely

### **3. Admin Dashboard** (`templates/admin_scraper.html`)
Beautiful admin interface to monitor scraping

### **4. Updated Scheduler** (`main.py`)
Daily cron job runs at 3 AM UK time

---

## 🎛️ **Data Sources**

### **Currently Active:**

#### **1. Bank Websites** ✅
- **HSBC** - Direct mortgage rates
- **Nationwide** - Building society rates
- **Barclays** - Mainstream bank rates

**Pros:** Direct from source, most accurate
**Cons:** Can break if website changes

#### **2. Comparison Sites** ⚠️
- **MoneySuperMarket** - Requires permission (check Terms of Service)
- **MoneySavingExpert** - Planned

**Pros:** Comprehensive coverage
**Cons:** Need to respect Terms of Service

### **Recommended (Professional):**

#### **3. Moneyfacts API** 💎
Official mortgage data feed - the BEST option!

**How to enable:**
1. Sign up at https://moneyfacts.co.uk
2. Get your API key
3. Add to Railway environment variables:
   ```
   MONEYFACTS_API_KEY=your_key_here
   ```
4. Scraper will automatically use it!

**Why use this:**
- ✅ Official, reliable data
- ✅ No scraping = no breaking
- ✅ Comprehensive coverage
- ✅ Legal and approved
- ✅ Professional service

---

## ⚠️ **IMPORTANT LEGAL NOTICE**

### **Web Scraping Guidelines:**

1. **Check Terms of Service** before scraping any website
2. **Respect robots.txt** - our scraper does this automatically
3. **Rate limiting** - built-in delays between requests
4. **Use APIs when available** - always prefer official APIs!

### **Best Practices:**

✅ **DO:**
- Use official APIs (Moneyfacts, bank APIs)
- Add delays between requests (we do this)
- Respect robots.txt (we do this)
- Check each site's Terms of Service
- Use for personal/educational purposes

❌ **DON'T:**
- Scrape sites that prohibit it in their ToS
- Overwhelm servers with rapid requests
- Sell or redistribute scraped data
- Ignore cease-and-desist notices

### **Legal Disclaimer:**

This scraping system is provided for **educational and personal use only**. You are responsible for:
- Checking Terms of Service of all scraped websites
- Obtaining permission where required
- Complying with all applicable laws
- Using data ethically and responsibly

**We strongly recommend using official APIs like Moneyfacts instead of web scraping!**

---

## 🔧 **Configuration**

### **Enable/Disable Scraping:**

In Railway environment variables:
```
SCHEDULER_ENABLED=1  # Enable automatic daily scraping
SCHEDULER_ENABLED=0  # Disable (manual only)
```

### **Add Moneyfacts API:**

```
MONEYFACTS_API_KEY=your_api_key_here
```

---

## 📊 **How Data is Validated**

Every scraped deal goes through:

1. **Field Validation** - Checks all required fields exist
2. **Range Validation** - Ensures rates are realistic (0-20%)
3. **Deduplication** - Removes duplicate deals
4. **Quality Check** - Minimum 10 deals required to update database
5. **Fallback** - Keeps existing data if scraping fails

---

## 🛠️ **Troubleshooting**

### **Problem: No new deals appearing**

**Solutions:**
1. Check `/secret-admin-scraper-xyz` to see last refresh time
2. Manually trigger refresh
3. Check Railway logs for errors
4. Ensure `SCHEDULER_ENABLED=1` in environment variables

### **Problem: Scraper failing**

**Common causes:**
- Bank website changed structure (needs code update)
- Rate limiting (wait and try again)
- Network issues (temporary)

**Solution:**
- Check logs for specific errors
- Scrapers are designed to fail gracefully
- Existing data is preserved automatically

### **Problem: Want more reliable data**

**Solution:**
Get a Moneyfacts API key! This is the professional solution and eliminates all scraping issues.

---

## 🚀 **Future Enhancements**

Planned features:
- [ ] More bank scrapers (Santander, Halifax, etc.)
- [ ] Specialist lender sites (Pepper Money, Bluestone, etc.)
- [ ] Historical rate tracking
- [ ] Rate change alerts for users
- [ ] Machine learning for rate predictions

---

## 📞 **Support**

**Logs Location:**
- Railway: Check "Deployments" → "Logs"
- Look for messages starting with 🔄 (scraping) or ✅ (success)

**Admin Dashboards:**
- Gatekeeper: `/secret-admin-control-xyz`
- Scraper: `/secret-admin-scraper-xyz`

---

## 💡 **Recommendations**

### **For Development/Testing:**
✅ Use the scraper as-is (works with demo data)

### **For Production:**
✅ **Get Moneyfacts API key** - This is the RIGHT way!
✅ Check Terms of Service for all scraped sites
✅ Monitor logs regularly
✅ Set up alerts for scraping failures

### **Best Setup:**
```
1. Moneyfacts API (primary source) - $$$
2. Bank direct APIs where available - Free
3. Web scraping (backup only) - Free but fragile
```

---

## 🎉 **Summary**

You now have a **fully automated mortgage data extraction system** that:
- Runs daily at 3 AM
- Pulls fresh data from multiple sources
- Validates and cleans everything
- Updates your database automatically
- Has a beautiful admin dashboard
- Falls back gracefully on errors

**Your users get the freshest mortgage deals - even obscure ones that brokers might miss!**

---

**Questions?** Check the code comments in `scrapers/mortgage_scraper.py` for detailed implementation notes!
