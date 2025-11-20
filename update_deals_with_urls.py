#!/usr/bin/env python3
"""
Add lender application URLs to all mortgage deals
Direct links to lender mortgage pages (not affiliate yet)
"""

# Lender mortgage application URLs (publicly available)
LENDER_URLS = {
    # Mainstream Lenders
    "HSBC": "https://www.hsbc.co.uk/mortgages/",
    "Barclays": "https://www.barclays.co.uk/mortgages/",
    "Nationwide": "https://www.nationwide.co.uk/products/mortgages/",
    "Santander": "https://www.santander.co.uk/personal/mortgages",
    "NatWest": "https://www.natwest.com/mortgages.html",
    "Lloyds": "https://www.lloydsbank.com/mortgages.html",
    "Halifax": "https://www.halifax.co.uk/mortgages/",
    "TSB": "https://www.tsb.co.uk/mortgages/",
    "First Direct": "https://www1.firstdirect.com/mortgages/",
    "Virgin Money": "https://uk.virginmoney.com/mortgages/",

    # Building Societies
    "Coventry Building Society": "https://www.coventrybuildingsociety.co.uk/mortgages",
    "Yorkshire Building Society": "https://www.ybs.co.uk/mortgages",
    "Skipton Building Society": "https://www.skipton.co.uk/mortgages",
    "Leeds Building Society": "https://www.leedsbuildingsociety.co.uk/mortgages/",
    "Newcastle Building Society": "https://www.newcastle.co.uk/mortgages",
    "Principality Building Society": "https://www.principality.co.uk/mortgages",

    # Specialist Lenders (Bad Credit)
    "Pepper Money": "https://www.peppermoney.com/mortgages/",
    "Vida Homeloans": "https://www.vidahomeloans.com/",
    "Together Money": "https://www.togethermoney.com/mortgages/",
    "Bluestone Mortgages": "https://www.bluestonemortgages.co.uk/",
    "Foundation Home Loans": "https://www.foundationhomeloans.co.uk/",
    "Kensington Mortgages": "https://www.kensingtonmortgages.co.uk/",
    "Precise Mortgages": "https://www.precise.co.uk/",
    "Alternative Bridging Corporation": "https://www.altbridging.co.uk/",

    # Bank Statement Mortgages
    "Aldermore": "https://www.aldermore.co.uk/mortgages/",
    "Shawbrook Bank": "https://www.shawbrook.co.uk/mortgages/",
    "Paragon Bank": "https://www.paragonbank.co.uk/mortgages/",

    # Asset-Based Lenders
    "United Trust Bank": "https://www.utbank.co.uk/mortgages/",
    "Masthaven Bank": "https://www.masthaven.co.uk/mortgages/",

    # Guarantor Mortgages
    "Lloyds (Lend a Hand)": "https://www.lloydsbank.com/mortgages/first-time-buyer/lend-a-hand.html",
    "Barclays (Family Springboard)": "https://www.barclays.co.uk/mortgages/family-springboard-mortgage/",

    # Credit Unions
    "London Mutual Credit Union": "https://www.londonmutual.coop/",
    "Manchester Credit Union": "https://www.manchestercreditunion.coop/",

    # Shared Ownership
    "Homes England": "https://www.gov.uk/shared-ownership-scheme",
    "L&Q": "https://www.lqgroup.org.uk/buy-a-home/shared-ownership/",
}

def update_urls():
    """Update all deals with lender URLs"""
    from main import app, db, Deal

    with app.app_context():
        updated = 0
        not_found = []

        deals = Deal.query.all()
        print(f"Found {len(deals)} deals in database")
        print()

        for deal in deals:
            # Try exact match first
            if deal.lender in LENDER_URLS:
                deal.apply_url = LENDER_URLS[deal.lender]
                updated += 1
                print(f"✅ {deal.lender}: {deal.apply_url}")
            else:
                # Try partial match
                matched = False
                for lender_name, url in LENDER_URLS.items():
                    if lender_name.lower() in deal.lender.lower() or deal.lender.lower() in lender_name.lower():
                        deal.apply_url = url
                        updated += 1
                        matched = True
                        print(f"✅ {deal.lender} → {lender_name}: {url}")
                        break

                if not matched:
                    not_found.append(deal.lender)
                    print(f"⚠️  {deal.lender}: No URL found")

        db.session.commit()

        print()
        print("=" * 60)
        print(f"✅ Updated {updated} deals with application URLs")
        if not_found:
            print(f"⚠️  {len(not_found)} deals without URLs:")
            for lender in not_found:
                print(f"   - {lender}")
        print("=" * 60)

if __name__ == "__main__":
    update_urls()
