# app/utils/refresh_deals.py
import requests
from datetime import datetime
from main import Deal, db  # Adjust imports based on your structure

def refresh_deals():
    """
    Refreshes the mortgage deals in the database.
    Fetches the latest data from your sources (APIs or scrapers),
    updates the DB, and removes expired deals.
    """
    print(f"[{datetime.now()}] 🔄 Starting daily mortgage deal refresh...")

    # Example static data (replace this with your scraper/API)
    new_deals = [
        {
            "lender": "HSBC",
            "product_name": "2-Year Fixed 90% LTV",
            "rate": 4.65,
            "product_fee": 999,
            "cashback": 0,
            "ltv_max": 90,
            "initial_period_months": 24,
            "last_updated": datetime.now()
        },
        {
            "lender": "Nationwide",
            "product_name": "5-Year Fixed 85% LTV",
            "rate": 4.35,
            "product_fee": 499,
            "cashback": 250,
            "ltv_max": 85,
            "initial_period_months": 60,
            "last_updated": datetime.now()
        }
    ]

    # Clear old deals
    Deal.query.delete()

    # Add new ones
    for data in new_deals:
        deal = Deal(**data)
        db.session.add(deal)

    db.session.commit()

    print(f"[{datetime.now()}] ✅ {len(new_deals)} deals refreshed successfully!")
