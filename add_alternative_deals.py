#!/usr/bin/env python3
"""
Add 40 alternative mortgage deals to the database
Bank statement, asset-based, bridging, credit unions, guarantor, shared ownership, alternative finance
"""

from main import app, db, Deal

# Alternative mortgage deals data
ALTERNATIVE_DEALS = [
    # Bank Statement Mortgages (7 deals)
    {"lender": "Aldermore", "rate": 4.89, "ltv_max": 75, "min_loan": 25000, "max_loan": 1000000, "accepts_bad_credit": True, "min_credit_score": 550, "accepts_low_income": True, "min_income": 20000, "lender_type": "specialist", "product_fee": 1995, "cashback": 0},
    {"lender": "Shawbrook Bank", "rate": 5.19, "ltv_max": 75, "min_loan": 50000, "max_loan": 1500000, "accepts_bad_credit": True, "min_credit_score": 500, "accepts_low_income": True, "min_income": 15000, "lender_type": "specialist", "product_fee": 1995, "cashback": 0},
    {"lender": "Paragon Bank", "rate": 4.99, "ltv_max": 75, "min_loan": 25000, "max_loan": 1000000, "accepts_bad_credit": True, "min_credit_score": 550, "accepts_low_income": True, "min_income": 18000, "lender_type": "specialist", "product_fee": 1495, "cashback": 0},
    {"lender": "Precise Mortgages", "rate": 5.29, "ltv_max": 75, "min_loan": 50000, "max_loan": 750000, "accepts_bad_credit": True, "min_credit_score": 500, "accepts_low_income": True, "min_income": 15000, "lender_type": "specialist", "product_fee": 1995, "cashback": 0},
    {"lender": "Foundation Home Loans", "rate": 5.49, "ltv_max": 75, "min_loan": 50000, "max_loan": 1000000, "accepts_bad_credit": True, "min_credit_score": 450, "accepts_low_income": True, "min_income": 12000, "lender_type": "specialist", "product_fee": 1995, "cashback": 0},
    {"lender": "Vida Homeloans", "rate": 5.69, "ltv_max": 75, "min_loan": 25000, "max_loan": 500000, "accepts_bad_credit": True, "min_credit_score": 400, "accepts_low_income": True, "min_income": 10000, "lender_type": "specialist", "product_fee": 1495, "cashback": 0},
    {"lender": "Kensington Mortgages", "rate": 5.39, "ltv_max": 75, "min_loan": 50000, "max_loan": 1000000, "accepts_bad_credit": True, "min_credit_score": 500, "accepts_low_income": True, "min_income": 15000, "lender_type": "specialist", "product_fee": 1995, "cashback": 0},

    # Asset-Based Mortgages (5 deals)
    {"lender": "United Trust Bank", "rate": 5.79, "ltv_max": 70, "min_loan": 100000, "max_loan": 5000000, "accepts_bad_credit": True, "min_credit_score": 0, "accepts_low_income": True, "min_income": 0, "lender_type": "specialist", "product_fee": 2995, "cashback": 0},
    {"lender": "Masthaven Bank", "rate": 5.99, "ltv_max": 75, "min_loan": 100000, "max_loan": 3000000, "accepts_bad_credit": True, "min_credit_score": 0, "accepts_low_income": True, "min_income": 0, "lender_type": "specialist", "product_fee": 2495, "cashback": 0},
    {"lender": "Pepper Money", "rate": 5.89, "ltv_max": 70, "min_loan": 50000, "max_loan": 2000000, "accepts_bad_credit": True, "min_credit_score": 400, "accepts_low_income": True, "min_income": 0, "lender_type": "specialist", "product_fee": 1995, "cashback": 0},
    {"lender": "Together Money", "rate": 6.19, "ltv_max": 75, "min_loan": 25000, "max_loan": 1500000, "accepts_bad_credit": True, "min_credit_score": 0, "accepts_low_income": True, "min_income": 0, "lender_type": "specialist", "product_fee": 1995, "cashback": 0},
    {"lender": "Bluestone Mortgages", "rate": 5.99, "ltv_max": 75, "min_loan": 25000, "max_loan": 500000, "accepts_bad_credit": True, "min_credit_score": 350, "accepts_low_income": True, "min_income": 0, "lender_type": "specialist", "product_fee": 1495, "cashback": 0},

    # Bridging Loans (8 deals)
    {"lender": "Alternative Bridging Corporation", "rate": 0.69, "ltv_max": 75, "min_loan": 50000, "max_loan": 5000000, "accepts_bad_credit": True, "min_credit_score": 0, "accepts_low_income": True, "min_income": 0, "lender_type": "specialist", "product_fee": 3995, "cashback": 0},
    {"lender": "MT Finance", "rate": 0.75, "ltv_max": 75, "min_loan": 50000, "max_loan": 10000000, "accepts_bad_credit": True, "min_credit_score": 0, "accepts_low_income": True, "min_income": 0, "lender_type": "specialist", "product_fee": 3995, "cashback": 0},
    {"lender": "Precise Mortgages Bridging", "rate": 0.65, "ltv_max": 75, "min_loan": 25000, "max_loan": 5000000, "accepts_bad_credit": True, "min_credit_score": 0, "accepts_low_income": True, "min_income": 0, "lender_type": "specialist", "product_fee": 2995, "cashback": 0},
    {"lender": "West One Loans", "rate": 0.70, "ltv_max": 75, "min_loan": 100000, "max_loan": 25000000, "accepts_bad_credit": True, "min_credit_score": 0, "accepts_low_income": True, "min_income": 0, "lender_type": "specialist", "product_fee": 4995, "cashback": 0},
    {"lender": "Lendinvest Bridging", "rate": 0.68, "ltv_max": 75, "min_loan": 50000, "max_loan": 10000000, "accepts_bad_credit": True, "min_credit_score": 0, "accepts_low_income": True, "min_income": 0, "lender_type": "specialist", "product_fee": 3495, "cashback": 0},
    {"lender": "Octopus Real Estate", "rate": 0.72, "ltv_max": 70, "min_loan": 100000, "max_loan": 50000000, "accepts_bad_credit": True, "min_credit_score": 0, "accepts_low_income": True, "min_income": 0, "lender_type": "specialist", "product_fee": 4995, "cashback": 0},
    {"lender": "Enra Bridging", "rate": 0.79, "ltv_max": 75, "min_loan": 50000, "max_loan": 3000000, "accepts_bad_credit": True, "min_credit_score": 0, "accepts_low_income": True, "min_income": 0, "lender_type": "specialist", "product_fee": 2995, "cashback": 0},
    {"lender": "Roma Finance", "rate": 0.75, "ltv_max": 70, "min_loan": 50000, "max_loan": 5000000, "accepts_bad_credit": True, "min_credit_score": 0, "accepts_low_income": True, "min_income": 0, "lender_type": "specialist", "product_fee": 3495, "cashback": 0},

    # Credit Union Mortgages (7 deals)
    {"lender": "London Mutual Credit Union", "rate": 4.25, "ltv_max": 90, "min_loan": 10000, "max_loan": 250000, "accepts_bad_credit": True, "min_credit_score": 300, "accepts_low_income": True, "min_income": 10000, "lender_type": "building_society", "product_fee": 0, "cashback": 0},
    {"lender": "Manchester Credit Union", "rate": 4.35, "ltv_max": 90, "min_loan": 10000, "max_loan": 200000, "accepts_bad_credit": True, "min_credit_score": 300, "accepts_low_income": True, "min_income": 8000, "lender_type": "building_society", "product_fee": 0, "cashback": 0},
    {"lender": "Liverpool Credit Union", "rate": 4.40, "ltv_max": 85, "min_loan": 10000, "max_loan": 150000, "accepts_bad_credit": True, "min_credit_score": 300, "accepts_low_income": True, "min_income": 10000, "lender_type": "building_society", "product_fee": 0, "cashback": 0},
    {"lender": "Glasgow Credit Union", "rate": 4.30, "ltv_max": 90, "min_loan": 10000, "max_loan": 180000, "accepts_bad_credit": True, "min_credit_score": 300, "accepts_low_income": True, "min_income": 10000, "lender_type": "building_society", "product_fee": 0, "cashback": 0},
    {"lender": "Birmingham Credit Union", "rate": 4.45, "ltv_max": 85, "min_loan": 10000, "max_loan": 175000, "accepts_bad_credit": True, "min_credit_score": 300, "accepts_low_income": True, "min_income": 8000, "lender_type": "building_society", "product_fee": 0, "cashback": 0},
    {"lender": "Leeds Credit Union", "rate": 4.38, "ltv_max": 85, "min_loan": 10000, "max_loan": 150000, "accepts_bad_credit": True, "min_credit_score": 300, "accepts_low_income": True, "min_income": 10000, "lender_type": "building_society", "product_fee": 0, "cashback": 0},
    {"lender": "Capital Credit Union", "rate": 4.29, "ltv_max": 90, "min_loan": 10000, "max_loan": 250000, "accepts_bad_credit": True, "min_credit_score": 300, "accepts_low_income": True, "min_income": 10000, "lender_type": "building_society", "product_fee": 0, "cashback": 0},

    # Guarantor Mortgages (3 deals)
    {"lender": "Lloyds (Lend a Hand)", "rate": 4.79, "ltv_max": 100, "min_loan": 50000, "max_loan": 500000, "accepts_bad_credit": False, "min_credit_score": 600, "accepts_low_income": True, "min_income": 15000, "lender_type": "mainstream", "product_fee": 999, "cashback": 0},
    {"lender": "Barclays (Family Springboard)", "rate": 4.99, "ltv_max": 100, "min_loan": 50000, "max_loan": 600000, "accepts_bad_credit": False, "min_credit_score": 600, "accepts_low_income": True, "min_income": 18000, "lender_type": "mainstream", "product_fee": 999, "cashback": 0},
    {"lender": "NewDay Guarantor Mortgages", "rate": 5.49, "ltv_max": 100, "min_loan": 25000, "max_loan": 350000, "accepts_bad_credit": True, "min_credit_score": 450, "accepts_low_income": True, "min_income": 12000, "lender_type": "specialist", "product_fee": 1495, "cashback": 0},

    # Shared Ownership (5 deals)
    {"lender": "L&Q (Shared Ownership)", "rate": 4.59, "ltv_max": 95, "min_loan": 10000, "max_loan": 300000, "accepts_bad_credit": False, "min_credit_score": 550, "accepts_low_income": True, "min_income": 15000, "lender_type": "mainstream", "product_fee": 500, "cashback": 0},
    {"lender": "Peabody (Shared Ownership)", "rate": 4.69, "ltv_max": 95, "min_loan": 10000, "max_loan": 250000, "accepts_bad_credit": False, "min_credit_score": 550, "accepts_low_income": True, "min_income": 15000, "lender_type": "mainstream", "product_fee": 500, "cashback": 0},
    {"lender": "Clarion (Shared Ownership)", "rate": 4.65, "ltv_max": 95, "min_loan": 10000, "max_loan": 275000, "accepts_bad_credit": False, "min_credit_score": 550, "accepts_low_income": True, "min_income": 15000, "lender_type": "mainstream", "product_fee": 500, "cashback": 0},
    {"lender": "Notting Hill Genesis (Shared Ownership)", "rate": 4.72, "ltv_max": 95, "min_loan": 10000, "max_loan": 300000, "accepts_bad_credit": False, "min_credit_score": 550, "accepts_low_income": True, "min_income": 15000, "lender_type": "mainstream", "product_fee": 500, "cashback": 0},
    {"lender": "Homes England (Shared Ownership)", "rate": 4.55, "ltv_max": 95, "min_loan": 10000, "max_loan": 350000, "accepts_bad_credit": False, "min_credit_score": 600, "accepts_low_income": True, "min_income": 18000, "lender_type": "mainstream", "product_fee": 0, "cashback": 500},

    # Alternative Finance (5 deals)
    {"lender": "Zopa Bank", "rate": 4.89, "ltv_max": 75, "min_loan": 50000, "max_loan": 750000, "accepts_bad_credit": False, "min_credit_score": 650, "accepts_low_income": False, "min_income": 25000, "lender_type": "mainstream", "product_fee": 995, "cashback": 0},
    {"lender": "Atom Bank", "rate": 4.79, "ltv_max": 85, "min_loan": 50000, "max_loan": 750000, "accepts_bad_credit": False, "min_credit_score": 650, "accepts_low_income": False, "min_income": 25000, "lender_type": "mainstream", "product_fee": 0, "cashback": 1000},
    {"lender": "Habito", "rate": 4.69, "ltv_max": 85, "min_loan": 25000, "max_loan": 500000, "accepts_bad_credit": False, "min_credit_score": 650, "accepts_low_income": False, "min_income": 25000, "lender_type": "mainstream", "product_fee": 0, "cashback": 1500},
    {"lender": "Trussle", "rate": 4.75, "ltv_max": 80, "min_loan": 50000, "max_loan": 500000, "accepts_bad_credit": False, "min_credit_score": 650, "accepts_low_income": False, "min_income": 25000, "lender_type": "mainstream", "product_fee": 0, "cashback": 1000},
    {"lender": "Molo Finance", "rate": 4.99, "ltv_max": 75, "min_loan": 50000, "max_loan": 1000000, "accepts_bad_credit": False, "min_credit_score": 700, "accepts_low_income": False, "min_income": 30000, "lender_type": "mainstream", "product_fee": 0, "cashback": 2000},
]

def add_deals():
    """Add alternative deals to database"""
    with app.app_context():
        added = 0
        skipped = 0

        print("=" * 60)
        print("🚀 ADDING 40 ALTERNATIVE MORTGAGE DEALS")
        print("=" * 60)
        print()

        for deal_data in ALTERNATIVE_DEALS:
            # Check if deal already exists
            existing = Deal.query.filter_by(lender=deal_data['lender']).first()

            if existing:
                print(f"⏭️  {deal_data['lender']}: Already exists")
                skipped += 1
            else:
                deal = Deal(**deal_data)
                db.session.add(deal)
                added += 1
                print(f"✅ {deal_data['lender']}: Added ({deal_data['rate']}% LTV {deal_data['ltv_max']}%)")

        db.session.commit()

        print()
        print("=" * 60)
        print(f"✅ Added {added} new deals")
        print(f"⏭️  Skipped {skipped} existing deals")
        print(f"📊 Total alternative deals: {len(ALTERNATIVE_DEALS)}")
        print("=" * 60)

if __name__ == "__main__":
    add_deals()
