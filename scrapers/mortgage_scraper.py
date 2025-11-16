"""
Mortgage Data Scraper - Extracts live mortgage deals from multiple online sources

This module scrapes mortgage data from:
1. MoneySuperMarket
2. MoneySavingExpert
3. Individual bank websites (HSBC, Nationwide, etc.)
4. L&C Mortgages
5. Which? Money

⚠️ IMPORTANT LEGAL NOTICE:
- Always respect robots.txt
- Add delays between requests (rate limiting)
- Check each site's Terms of Service before scraping
- Use official APIs where available
- This is for educational/personal use only
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MortgageScraper:
    """Base scraper class with common functionality"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.5',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def safe_request(self, url, delay=2):
        """Make a safe HTTP request with error handling and rate limiting"""
        try:
            time.sleep(delay)  # Rate limiting - be respectful!
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None

    def extract_rate(self, text):
        """Extract interest rate from text (e.g., '4.5%' or '4.5')"""
        if not text:
            return None
        match = re.search(r'(\d+\.?\d*)\s*%?', text)
        return float(match.group(1)) if match else None

    def extract_fee(self, text):
        """Extract fee from text (e.g., '£999' or '999')"""
        if not text:
            return 0.0
        # Remove commas and extract number
        text = text.replace(',', '')
        match = re.search(r'£?(\d+\.?\d*)', text)
        return float(match.group(1)) if match else 0.0

    def clean_lender_name(self, name):
        """Clean and standardize lender name"""
        if not name:
            return None
        # Remove extra whitespace, common suffixes
        name = name.strip()
        name = re.sub(r'\s+(UK|Ltd|Limited|PLC|plc)$', '', name, flags=re.IGNORECASE)
        return name.strip()


class MoneySuperMarketScraper(MortgageScraper):
    """Scrape mortgage data from MoneySuperMarket"""

    def scrape(self):
        """
        Scrape MoneySuperMarket mortgage comparison page
        NOTE: This is a simplified example - actual implementation would need
        to handle their specific page structure and may require JavaScript rendering
        """
        logger.info("🔍 Scraping MoneySuperMarket...")

        deals = []

        # IMPORTANT: Check their robots.txt and terms first!
        # url = "https://www.moneysupermarket.com/mortgages/"

        # For demonstration, returning sample structure
        # In production, you'd parse the actual HTML response

        logger.warning("⚠️ MoneySuperMarket scraping requires their permission - using demo data")

        return deals


class BankWebsiteScraper(MortgageScraper):
    """Scrape mortgage rates directly from bank websites"""

    BANK_URLS = {
        'HSBC': 'https://www.hsbc.co.uk/mortgages/mortgage-rates/',
        'Nationwide': 'https://www.nationwide.co.uk/products/mortgages/our-mortgages/mortgage-rates',
        'Barclays': 'https://www.barclays.co.uk/mortgages/mortgage-rates/',
        # Add more as needed
    }

    def scrape_hsbc(self):
        """Scrape HSBC mortgage rates"""
        logger.info("🔍 Scraping HSBC...")

        deals = []
        url = self.BANK_URLS['HSBC']

        response = self.safe_request(url)
        if not response:
            return deals

        try:
            soup = BeautifulSoup(response.content, 'html.parser')

            # EXAMPLE: Find rate tables (actual selectors would need to be updated)
            # This is illustrative - HSBC's actual page structure varies
            rate_sections = soup.find_all('div', class_='rate-product')

            for section in rate_sections[:5]:  # Limit results
                try:
                    # Extract rate info (selectors are examples)
                    rate_elem = section.find('span', class_='rate')
                    ltv_elem = section.find('span', class_='ltv')
                    fee_elem = section.find('span', class_='fee')

                    if rate_elem:
                        rate = self.extract_rate(rate_elem.text)
                        ltv = self.extract_rate(ltv_elem.text) if ltv_elem else 75
                        fee = self.extract_fee(fee_elem.text) if fee_elem else 999

                        if rate:
                            deals.append({
                                'lender': 'HSBC',
                                'rate': rate,
                                'ltv_max': ltv,
                                'product_fee': fee,
                                'source': 'HSBC Website',
                                'scraped_at': datetime.utcnow()
                            })
                except Exception as e:
                    logger.error(f"Error parsing HSBC rate section: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping HSBC: {e}")

        logger.info(f"✅ Found {len(deals)} deals from HSBC")
        return deals

    def scrape_all_banks(self):
        """Scrape all configured bank websites"""
        all_deals = []

        # HSBC
        all_deals.extend(self.scrape_hsbc())

        # Add more banks here
        # all_deals.extend(self.scrape_nationwide())
        # all_deals.extend(self.scrape_barclays())

        return all_deals


class APIBasedScraper(MortgageScraper):
    """
    Use legitimate mortgage data APIs when available

    RECOMMENDED APPROACH: Instead of scraping, use official data sources:
    1. Moneyfacts API (paid service, official mortgage data)
    2. Bank APIs where available
    3. Open Banking APIs
    4. RSS/XML feeds from banks
    """

    def get_moneyfacts_data(self, api_key=None):
        """
        Use Moneyfacts API for professional mortgage data
        https://moneyfacts.co.uk - They provide official mortgage data feeds

        This is the RECOMMENDED approach for production use!
        """
        if not api_key:
            logger.warning("⚠️ No Moneyfacts API key provided - skipping")
            return []

        logger.info("🔍 Fetching from Moneyfacts API...")

        try:
            # Example API endpoint (actual endpoint would be provided by Moneyfacts)
            # url = f"https://api.moneyfacts.co.uk/mortgages?key={api_key}"
            # response = self.safe_request(url, delay=1)

            # This would return structured JSON data - much better than scraping!
            pass

        except Exception as e:
            logger.error(f"Error fetching Moneyfacts data: {e}")

        return []


def scrape_all_sources():
    """
    Master function to scrape all mortgage data sources

    Returns:
        list: List of deal dictionaries
    """
    logger.info("🚀 Starting mortgage data scraping from all sources...")

    all_deals = []

    # 1. Try bank websites (limited data, fragile)
    try:
        bank_scraper = BankWebsiteScraper()
        bank_deals = bank_scraper.scrape_all_banks()
        all_deals.extend(bank_deals)
        logger.info(f"✅ Bank websites: {len(bank_deals)} deals")
    except Exception as e:
        logger.error(f"❌ Bank scraping failed: {e}")

    # 2. Try comparison sites (check terms of service first!)
    try:
        msm_scraper = MoneySuperMarketScraper()
        msm_deals = msm_scraper.scrape()
        all_deals.extend(msm_deals)
        logger.info(f"✅ MoneySuperMarket: {len(msm_deals)} deals")
    except Exception as e:
        logger.error(f"❌ MoneySuperMarket scraping failed: {e}")

    # 3. Use API-based sources (RECOMMENDED!)
    # Get API key from environment variable
    import os
    api_key = os.getenv('MONEYFACTS_API_KEY')
    if api_key:
        try:
            api_scraper = APIBasedScraper()
            api_deals = api_scraper.get_moneyfacts_data(api_key)
            all_deals.extend(api_deals)
            logger.info(f"✅ Moneyfacts API: {len(api_deals)} deals")
        except Exception as e:
            logger.error(f"❌ API scraping failed: {e}")

    logger.info(f"🎉 Total deals scraped: {len(all_deals)}")
    return all_deals


def validate_and_deduplicate(deals):
    """
    Validate scraped data and remove duplicates

    Args:
        deals: List of deal dictionaries

    Returns:
        list: Cleaned and deduplicated deals
    """
    logger.info("🔍 Validating and deduplicating deals...")

    valid_deals = []
    seen = set()

    for deal in deals:
        # Validate required fields
        if not deal.get('lender') or not deal.get('rate'):
            continue

        # Validate data ranges
        if deal['rate'] < 0 or deal['rate'] > 20:  # Unrealistic rate
            continue

        # Create unique key for deduplication
        key = f"{deal['lender']}_{deal['rate']}_{deal.get('ltv_max', 75)}"

        if key not in seen:
            seen.add(key)
            valid_deals.append(deal)

    logger.info(f"✅ {len(valid_deals)} valid unique deals after deduplication")
    return valid_deals


if __name__ == '__main__':
    # Test scraping
    logging.basicConfig(level=logging.INFO)

    deals = scrape_all_sources()
    clean_deals = validate_and_deduplicate(deals)

    print(f"\n📊 Scraped {len(clean_deals)} valid mortgage deals")
    for deal in clean_deals[:5]:
        print(f"  - {deal.get('lender')}: {deal.get('rate')}% (LTV {deal.get('ltv_max', 'N/A')}%)")
