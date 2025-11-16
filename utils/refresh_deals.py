"""
Mortgage Deal Refresh Utility

This module handles refreshing mortgage deals from scraped data sources
and updating the database with fresh data.
"""

import logging
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


def refresh_deals():
    """
    Main function to refresh mortgage deals from all sources

    This function:
    1. Scrapes data from configured sources
    2. Validates and deduplicates the data
    3. Updates the database with fresh deals
    4. Keeps existing deals if scraping fails (fallback)    """
    from scrapers.mortgage_scraper import scrape_all_sources, validate_and_deduplicate
    from main import app, db, Deal

    logger.info("=" * 60)
    logger.info("🔄 Starting mortgage deal refresh job...")
    logger.info("=" * 60)

    with app.app_context():
        try:
            # 1. Scrape fresh data
            scraped_deals = scrape_all_sources()
            logger.info(f"📊 Scraped {len(scraped_deals)} raw deals")

            # 2. Validate and clean
            clean_deals = validate_and_deduplicate(scraped_deals)
            logger.info(f"✅ {len(clean_deals)} valid deals after validation")

            # 3. Only update if we got good data
            if len(clean_deals) >= 10:  # Minimum threshold
                logger.info("💾 Updating database with fresh deals...")

                # Mark old deals as outdated (add a last_updated field if needed)
                # For now, we'll just add new deals without deleting old ones

                added_count = 0
                updated_count = 0

                for deal_data in clean_deals:
                    try:
                        # Check if deal already exists
                        existing = Deal.query.filter_by(
                            lender=deal_data['lender'],
                            rate=deal_data['rate'],
                            ltv_max=deal_data.get('ltv_max', 75)
                        ).first()

                        if existing:
                            # Update existing deal
                            existing.product_fee = deal_data.get('product_fee', existing.product_fee)
                            existing.cashback = deal_data.get('cashback', existing.cashback)
                            # Update other fields as needed
                            updated_count += 1
                        else:
                            # Add new deal
                            new_deal = Deal(
                                lender=deal_data['lender'],
                                rate=deal_data['rate'],
                                ltv_max=deal_data.get('ltv_max', 75),
                                min_loan=deal_data.get('min_loan', 25000),
                                max_loan=deal_data.get('max_loan', 500000),
                                product_fee=deal_data.get('product_fee', 999),
                                cashback=deal_data.get('cashback', 0),
                                min_credit_score=deal_data.get('min_credit_score', 620),
                                min_income=deal_data.get('min_income', 20000),
                                lender_type=deal_data.get('lender_type', 'mainstream'),
                                accepts_bad_credit=deal_data.get('accepts_bad_credit', False),
                                accepts_low_income=deal_data.get('accepts_low_income', False),
                            )
                            db.session.add(new_deal)
                            added_count += 1

                    except Exception as e:
                        logger.error(f"Error processing deal {deal_data.get('lender')}: {e}")
                        continue

                # Commit changes
                db.session.commit()

                logger.info(f"✅ Database updated: {added_count} added, {updated_count} updated")
                logger.info(f"📊 Total deals in database: {Deal.query.count()}")

            else:
                logger.warning(f"⚠️ Only got {len(clean_deals)} deals - threshold not met")
                logger.warning("⚠️ Keeping existing database unchanged (fallback)")

        except Exception as e:
            logger.error(f"❌ Error during deal refresh: {e}")
            logger.exception(e)
            # Don't delete existing data on error - maintain fallback

        logger.info("=" * 60)
        logger.info("🏁 Mortgage deal refresh job completed")
        logger.info("=" * 60)


def cleanup_old_deals(days=90):
    """
    Remove deals older than X days (optional maintenance)

    Args:
        days: Number of days to keep deals
    """
    from main import app, db, Deal

    logger.info(f"🧹 Cleaning up deals older than {days} days...")

    with app.app_context():
        try:
            # This would require adding a 'created_at' or 'last_updated' timestamp to Deal model
            # cutoff_date = datetime.utcnow() - timedelta(days=days)
            # old_deals = Deal.query.filter(Deal.last_updated < cutoff_date).all()
            # for deal in old_deals:
            #     db.session.delete(deal)
            # db.session.commit()
            # logger.info(f"✅ Removed {len(old_deals)} old deals")

            logger.info("⚠️ Cleanup requires 'last_updated' field in Deal model")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

    # Run refresh
    refresh_deals()
