# main.py
from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, flash, send_from_directory, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from email_validator import validate_email, EmailNotValidError
import os
import bcrypt
import stripe
import re
import logging

# -------------------------------------------------
# Extensions (created once; app-bound in create_app)
# -------------------------------------------------
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Ensure env vars are loaded locally (Railway uses Variables UI)
load_dotenv()

# -------------------------------------------------
# Models
# -------------------------------------------------
class User(db.Model, UserMixin):

    __tablename__ = "users2"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_pro_member = db.Column(db.Boolean, default=False)

    def is_pro(self):
        return bool(self.is_pro_member)




class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lender = db.Column(db.String(120), index=True)
    rate = db.Column(db.Float, index=True)
    ltv_max = db.Column(db.Float, index=True)
    min_loan = db.Column(db.Float, index=True)
    max_loan = db.Column(db.Float, index=True)

    # Advanced filtering fields
    accepts_bad_credit = db.Column(db.Boolean, default=False, index=True)
    min_credit_score = db.Column(db.Integer, default=0)  # 0 = no minimum
    accepts_low_income = db.Column(db.Boolean, default=False, index=True)
    min_income = db.Column(db.Float, default=0)
    lender_type = db.Column(db.String(50), default='mainstream')  # mainstream, specialist, building_society
    product_fee = db.Column(db.Float, default=0)
    cashback = db.Column(db.Float, default=0)


class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------------------------------------
# App Factory
# -------------------------------------------------
def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Security headers with Talisman (only if not in development)
    if os.environ.get('FLASK_ENV') != 'development':
        Talisman(app,
            force_https=True,
            strict_transport_security=True,
            content_security_policy={
                'default-src': "'self'",
                'script-src': ["'self'", "'unsafe-inline'", "www.googletagmanager.com", "www.google-analytics.com"],
                'style-src': ["'self'", "'unsafe-inline'", "fonts.googleapis.com"],
                'font-src': ["'self'", "fonts.gstatic.com"],
                'img-src': ["'self'", "data:", "https:"],
            }
        )

    login_manager.login_view = 'login'
    stripe.api_key = app.config.get('STRIPE_SECRET_KEY')

    # user_loader must be defined after db model
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register routes
    register_routes(app)

    # DB setup
    with app.app_context():
        init_database()

    # Background scheduler (optional, only in a single process)
    start_scheduler_if_enabled(app)

    return app


# -------------------------------------------------
# Helper Functions
# -------------------------------------------------
def validate_email_address(email):
    """Validate email format"""
    try:
        valid = validate_email(email, check_deliverability=False)
        return valid.normalized
    except EmailNotValidError:
        return None

def validate_password_strength(password):
    """Check if password meets minimum requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    return True, ""

def sanitize_string(text, max_length=200):
    """Sanitize and limit string input"""
    if not text:
        return ""
    # Remove any null bytes and limit length
    text = text.replace('\x00', '').strip()
    return text[:max_length]

# -------------------------------------------------
# Routes
# -------------------------------------------------
def register_routes(app):

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/search_deals', methods=['GET'])
    def search_deals():
        """Search for mortgage deals based on user criteria"""
        try:
            # Get and validate search parameters
            property_value = float(request.args.get('property_value', 0))
            deposit = float(request.args.get('deposit', 0))
            income = float(request.args.get('income', 0))
            term = int(request.args.get('term', 5))

            # Basic validation
            if property_value <= 0 or deposit <= 0:
                flash('Please enter valid property value and deposit.', 'warning')
                return redirect(url_for('index'))

            # Calculate LTV
            loan_amount = property_value - deposit
            ltv = (loan_amount / property_value) * 100

            # Query deals that match criteria
            deals = Deal.query.filter(
                Deal.ltv_max >= ltv,
                Deal.min_loan <= loan_amount,
                Deal.max_loan >= loan_amount
            ).order_by(Deal.rate.asc()).limit(20).all()

            return render_template('search_results.html',
                deals=deals,
                property_value=property_value,
                deposit=deposit,
                loan_amount=loan_amount,
                ltv=ltv,
                income=income,
                term=term
            )
        except ValueError:
            flash('Invalid search parameters.', 'danger')
            return redirect(url_for('index'))

    @app.route('/privacy')
    def privacy():
        return render_template('privacy.html')

    @app.route('/terms')
    def terms():
        return render_template('terms.html')

    @app.route('/sitemap.xml')
    def sitemap():
        return send_from_directory('templates', 'sitemap.xml')

    # ---------- Auth ----------
    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("5 per minute")  # Rate limit login attempts
    def login():
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')

            # Validate email format
            validated_email = validate_email_address(email)
            if not validated_email:
                logging.warning(f"Failed login attempt with invalid email format: {email}")
                flash('Invalid credentials', 'danger')
                return render_template('login.html')

            user = User.query.filter_by(email=validated_email).first()

            ok = False
            if user:
                try:
                    ok = bcrypt.checkpw(password.encode('utf-8'), user.password_hash)
                except ValueError:
                    # Old/bad password value in DB – just treat as invalid login
                    ok = False

            if ok:
                login_user(user)
                logging.info(f"Successful login for user: {user.email}")
                flash('Logged in successfully.', 'success')
                return redirect(url_for('dashboard'))

            logging.warning(f"Failed login attempt for email: {validated_email}")
            flash('Invalid credentials', 'danger')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logged out successfully.', 'info')
        return redirect(url_for('login'))

    @app.route('/signup', methods=['GET', 'POST'])
    @limiter.limit("3 per hour")  # Rate limit signups
    def signup():
        if request.method == 'POST':
            name = sanitize_string(request.form.get('name', ''), max_length=120)
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')

            # Validate all fields are present
            if not (name and email and password):
                flash('All fields are required.', 'warning')
                return render_template('signup.html')

            # Validate email format
            validated_email = validate_email_address(email)
            if not validated_email:
                flash('Please enter a valid email address.', 'warning')
                return render_template('signup.html')

            # Validate password strength
            is_strong, msg = validate_password_strength(password)
            if not is_strong:
                flash(msg, 'warning')
                return render_template('signup.html')

            # Check if email already exists
            if User.query.filter_by(email=validated_email).first():
                flash('Email already registered. Try logging in.', 'info')
                return redirect(url_for('login'))

            # Create new user
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            new_user = User(name=name, email=validated_email, password_hash=hashed)
            db.session.add(new_user)
            db.session.commit()

            logging.info(f"New user registered: {validated_email}")
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))
        return render_template('signup.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', user=current_user)


       # ---------- Upgrade ----------
    # -------------------------------
# UPGRADE OPTIONS (YEARLY + MONTHLY)
# -------------------------------

    # ---------- Upgrade ----------
    @app.route('/upgrade')
    @login_required
    def upgrade():
        return render_template('upgrade.html')

    # YEARLY PAYMENT (£49/year)
    @app.route('/upgrade_yearly')
    @login_required
    def upgrade_yearly():
        try:
            checkout = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{
                    "price": app.config.get('STRIPE_YEARLY_PRICE_ID', 'price_1STXcVD2EDcoPFLNECjwrN1p'),
                    "quantity": 1
                }],
                success_url=url_for('payment_success', _external=True),
                cancel_url=url_for('dashboard', _external=True),
                customer_email=current_user.email,
                metadata={
                    'user_id': current_user.id,
                    'user_email': current_user.email
                }
            )
            logging.info(f"Stripe checkout session created for user {current_user.email} (yearly)")
            return redirect(checkout.url)
        except Exception as e:
            logging.error(f"Stripe checkout error (yearly): {str(e)}")
            flash('Payment system error. Please try again later.', 'danger')
            return redirect(url_for('upgrade'))

    # MONTHLY PAYMENT (£14.99/month)
    @app.route('/upgrade_monthly')
    @login_required
    def upgrade_monthly():
        try:
            checkout = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{
                    "price": app.config.get('STRIPE_MONTHLY_PRICE_ID', 'price_1STXbDD2EDcoPFLN6hEU2gS9'),
                    "quantity": 1
                }],
                success_url=url_for('payment_success', _external=True),
                cancel_url=url_for('dashboard', _external=True),
                customer_email=current_user.email,
                metadata={
                    'user_id': current_user.id,
                    'user_email': current_user.email
                }
            )
            logging.info(f"Stripe checkout session created for user {current_user.email} (monthly)")
            return redirect(checkout.url)
        except Exception as e:
            logging.error(f"Stripe checkout error (monthly): {str(e)}")
            flash('Payment system error. Please try again later.', 'danger')
            return redirect(url_for('upgrade'))

    @app.route('/payment_success')
    @login_required
    def payment_success():
        # ⚠️ DO NOT grant access here! This is just a thank you page.
        # Access is granted via Stripe webhook after payment is verified
        flash('Thank you! Your payment is being processed. You will be upgraded shortly.', 'success')
        return render_template('payment_success.html')

    # STRIPE WEBHOOK - This is where we ACTUALLY verify and grant access
    @app.route('/stripe-webhook', methods=['POST'])
    @csrf.exempt  # Stripe webhooks can't include CSRF tokens
    def stripe_webhook():
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        webhook_secret = app.config.get('STRIPE_WEBHOOK_SECRET')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError:
            logging.error("Invalid Stripe webhook payload")
            abort(400)
        except stripe.error.SignatureVerificationError:
            logging.error("Invalid Stripe webhook signature")
            abort(400)

        # Handle the checkout.session.completed event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_email = session.get('customer_email')

            if user_email:
                user = User.query.filter_by(email=user_email).first()
                if user:
                    user.is_pro_member = True
                    db.session.commit()
                    logging.info(f"✅ PRO access granted to {user_email} via Stripe webhook")
                else:
                    logging.warning(f"⚠️ Stripe payment received for unknown user: {user_email}")
            else:
                logging.warning("⚠️ Stripe webhook received without customer_email")

        return jsonify({'status': 'success'}), 200
 



    # ---------- API / health ----------
    @app.route('/api/ping')
    def ping():
        return jsonify({'message': 'pong'})

    @app.route('/healthz')
    def healthz():
        return 'ok', 200

    # ---------- Blog (minimal placeholders so links don’t break) ----------
    @app.route('/blog')
    def blog():
        return render_template('blog/index.html')

    @app.route('/blog/best-deals')
    def blog_best_deals():
        return render_template('blog/best_deals.html')

    @app.route('/blog/fixed-vs-tracker')
    def blog_fixed_vs_tracker():
        return render_template('blog/fixed_vs_tracker.html')

    @app.route('/blog/affordability')
    def blog_affordability():
        return render_template('blog/affordability.html')

    # Optional post stubs used in your template history
    @app.route('/blog/post<int:n>')
    def blog_post_n(n):
        # Try to render blog/post{n}.html if exists, else index
        tmpl = f'blog/post{n}.html'
        try:
            return render_template(tmpl)
        except Exception:
            return redirect(url_for('blog'))

    # ---------- Subscribe (from index.html form) ----------
    @app.route('/subscribe', methods=['POST'])
    @limiter.limit("10 per hour")
    def subscribe():
        email = (request.form.get('email') or '').strip().lower()

        # Validate email
        validated_email = validate_email_address(email)
        if not validated_email:
            flash('Please enter a valid email address.', 'warning')
            return redirect(url_for('index'))

        # Check if already subscribed
        exists = Subscriber.query.filter_by(email=validated_email).first()
        if exists:
            flash("You're already subscribed. 👍", 'info')
            return redirect(url_for('index'))

        # Add subscriber
        db.session.add(Subscriber(email=validated_email))
        db.session.commit()
        logging.info(f"New subscriber: {validated_email}")
        flash('Thanks! You will receive rate alerts by email.', 'success')
        return redirect(url_for('index'))

    # ---------- Error pages ----------
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500


# -------------------------------------------------
# DB setup & indexes
# -------------------------------------------------
def init_database():
    db.create_all()

    # --- Add is_pro_member column if missing ---
    try:
        db.session.execute(db.text(
            "ALTER TABLE users2 ADD COLUMN IF NOT EXISTS is_pro_member BOOLEAN DEFAULT FALSE"
        ))
        db.session.commit()
        print("✅ Column is_pro_member ensured")
    except Exception as e:
        print("⚠️ Column migration skipped or failed:", e)

    # --- Add new Deal columns if missing ---
    try:
        db.session.execute(db.text(
            "ALTER TABLE deal ADD COLUMN IF NOT EXISTS accepts_bad_credit BOOLEAN DEFAULT FALSE"
        ))
        db.session.execute(db.text(
            "ALTER TABLE deal ADD COLUMN IF NOT EXISTS min_credit_score INTEGER DEFAULT 0"
        ))
        db.session.execute(db.text(
            "ALTER TABLE deal ADD COLUMN IF NOT EXISTS accepts_low_income BOOLEAN DEFAULT FALSE"
        ))
        db.session.execute(db.text(
            "ALTER TABLE deal ADD COLUMN IF NOT EXISTS min_income FLOAT DEFAULT 0"
        ))
        db.session.execute(db.text(
            "ALTER TABLE deal ADD COLUMN IF NOT EXISTS lender_type VARCHAR(50) DEFAULT 'mainstream'"
        ))
        db.session.execute(db.text(
            "ALTER TABLE deal ADD COLUMN IF NOT EXISTS product_fee FLOAT DEFAULT 0"
        ))
        db.session.execute(db.text(
            "ALTER TABLE deal ADD COLUMN IF NOT EXISTS cashback FLOAT DEFAULT 0"
        ))
        db.session.commit()
        print("✅ Deal columns ensured (bad credit, income, fees)")
    except Exception as e:
        print("⚠️ Deal column migration skipped:", e)

    # --- Existing index setup ---
    try:
        db.session.execute(db.text(
            'CREATE INDEX IF NOT EXISTS idx_deal_ltv_max ON deal(ltv_max)'
        ))
        db.session.execute(db.text(
            'CREATE INDEX IF NOT EXISTS idx_deal_min_loan ON deal(min_loan)'
        ))
        db.session.execute(db.text(
            'CREATE INDEX IF NOT EXISTS idx_deal_max_loan ON deal(max_loan)'
        ))
        db.session.commit()
        print("✅ Database indexes created")
    except Exception as e:
        print("⚠️ Index creation skipped:", e)

    # Seed deals if empty
    if Deal.query.count() == 0:
        # Comprehensive UK mortgage deals including SPECIALIST LENDERS for bad credit & low income
        all_deals = [
            # MAINSTREAM LENDERS - Best rates, strict criteria
            Deal(lender="HSBC", rate=4.64, ltv_max=60, min_loan=25000, max_loan=1000000,
                 min_credit_score=700, min_income=25000, lender_type="mainstream", product_fee=999),
            Deal(lender="HSBC", rate=4.79, ltv_max=75, min_loan=25000, max_loan=1000000,
                 min_credit_score=680, min_income=25000, lender_type="mainstream", product_fee=999),
            Deal(lender="HSBC", rate=4.99, ltv_max=85, min_loan=25000, max_loan=500000,
                 min_credit_score=650, min_income=30000, lender_type="mainstream", product_fee=999),

            Deal(lender="Nationwide", rate=4.59, ltv_max=60, min_loan=10000, max_loan=1000000,
                 min_credit_score=720, min_income=20000, lender_type="building_society", product_fee=999, cashback=500),
            Deal(lender="Nationwide", rate=4.74, ltv_max=75, min_loan=10000, max_loan=1000000,
                 min_credit_score=680, min_income=20000, lender_type="building_society", product_fee=999),
            Deal(lender="Nationwide", rate=4.94, ltv_max=85, min_loan=10000, max_loan=750000,
                 min_credit_score=650, min_income=25000, lender_type="building_society", product_fee=999),
            Deal(lender="Nationwide", rate=5.49, ltv_max=95, min_loan=10000, max_loan=300000,
                 min_credit_score=620, min_income=30000, lender_type="building_society", product_fee=1499, accepts_low_income=True),

            Deal(lender="Barclays", rate=4.69, ltv_max=60, min_loan=25000, max_loan=2000000,
                 min_credit_score=700, min_income=30000, lender_type="mainstream", product_fee=999),
            Deal(lender="Barclays", rate=4.84, ltv_max=75, min_loan=25000, max_loan=1000000,
                 min_credit_score=680, min_income=25000, lender_type="mainstream", product_fee=999),

            # SPECIALIST BAD CREDIT LENDERS - Higher rates but accept poor credit
            Deal(lender="Pepper Money", rate=5.89, ltv_max=75, min_loan=25000, max_loan=500000,
                 accepts_bad_credit=True, min_credit_score=400, min_income=18000, lender_type="specialist",
                 product_fee=1995, accepts_low_income=True),
            Deal(lender="Pepper Money", rate=6.29, ltv_max=85, min_loan=25000, max_loan=400000,
                 accepts_bad_credit=True, min_credit_score=350, min_income=15000, lender_type="specialist",
                 product_fee=1995, accepts_low_income=True),

            Deal(lender="Bluestone Mortgages", rate=6.19, ltv_max=75, min_loan=25000, max_loan=500000,
                 accepts_bad_credit=True, min_credit_score=380, min_income=18000, lender_type="specialist",
                 product_fee=1995, accepts_low_income=True),
            Deal(lender="Bluestone Mortgages", rate=6.59, ltv_max=85, min_loan=25000, max_loan=400000,
                 accepts_bad_credit=True, min_credit_score=350, min_income=15000, lender_type="specialist",
                 product_fee=1995, accepts_low_income=True),

            Deal(lender="Vida Homeloans", rate=5.99, ltv_max=70, min_loan=25000, max_loan=500000,
                 accepts_bad_credit=True, min_credit_score=420, min_income=20000, lender_type="specialist",
                 product_fee=1495, accepts_low_income=True),
            Deal(lender="Vida Homeloans", rate=6.49, ltv_max=80, min_loan=25000, max_loan=400000,
                 accepts_bad_credit=True, min_credit_score=380, min_income=18000, lender_type="specialist",
                 product_fee=1495, accepts_low_income=True),

            Deal(lender="Kensington Mortgages", rate=5.79, ltv_max=75, min_loan=50000, max_loan=1000000,
                 accepts_bad_credit=True, min_credit_score=450, min_income=25000, lender_type="specialist",
                 product_fee=1999, accepts_low_income=True),
            Deal(lender="Kensington Mortgages", rate=6.19, ltv_max=85, min_loan=50000, max_loan=750000,
                 accepts_bad_credit=True, min_credit_score=400, min_income=20000, lender_type="specialist",
                 product_fee=1999, accepts_low_income=True),

            Deal(lender="Together Money", rate=6.39, ltv_max=75, min_loan=10000, max_loan=500000,
                 accepts_bad_credit=True, min_credit_score=350, min_income=12000, lender_type="specialist",
                 product_fee=1995, accepts_low_income=True),
            Deal(lender="Together Money", rate=6.89, ltv_max=85, min_loan=10000, max_loan=400000,
                 accepts_bad_credit=True, min_credit_score=300, min_income=10000, lender_type="specialist",
                 product_fee=1995, accepts_low_income=True),

            # LOW INCOME SPECIALISTS - Accept lower incomes
            Deal(lender="Foundation Home Loans", rate=5.69, ltv_max=75, min_loan=25000, max_loan=500000,
                 accepts_bad_credit=True, min_credit_score=420, min_income=15000, lender_type="specialist",
                 product_fee=1495, accepts_low_income=True),

            Deal(lender="Aldermore", rate=5.49, ltv_max=70, min_loan=25000, max_loan=750000,
                 accepts_bad_credit=True, min_credit_score=480, min_income=18000, lender_type="specialist",
                 product_fee=1295, accepts_low_income=True),
            Deal(lender="Aldermore", rate=5.99, ltv_max=80, min_loan=25000, max_loan=600000,
                 accepts_bad_credit=True, min_credit_score=450, min_income=16000, lender_type="specialist",
                 product_fee=1295, accepts_low_income=True),

            # BUILDING SOCIETIES - Often more flexible
            Deal(lender="Coventry Building Society", rate=4.89, ltv_max=75, min_loan=10000, max_loan=500000,
                 min_credit_score=620, min_income=18000, lender_type="building_society",
                 product_fee=999, accepts_low_income=True),
            Deal(lender="Coventry Building Society", rate=5.19, ltv_max=85, min_loan=10000, max_loan=400000,
                 min_credit_score=600, min_income=20000, lender_type="building_society",
                 product_fee=999, accepts_low_income=True),

            Deal(lender="Yorkshire Building Society", rate=4.94, ltv_max=75, min_loan=10000, max_loan=500000,
                 min_credit_score=640, min_income=18000, lender_type="building_society",
                 product_fee=995, accepts_low_income=True),
            Deal(lender="Yorkshire Building Society", rate=5.24, ltv_max=85, min_loan=10000, max_loan=400000,
                 min_credit_score=620, min_income=20000, lender_type="building_society",
                 product_fee=995, accepts_low_income=True),

            Deal(lender="Skipton Building Society", rate=4.99, ltv_max=75, min_loan=10000, max_loan=500000,
                 min_credit_score=630, min_income=17000, lender_type="building_society",
                 product_fee=995, accepts_low_income=True),
            Deal(lender="Skipton Building Society", rate=5.29, ltv_max=85, min_loan=10000, max_loan=400000,
                 min_credit_score=610, min_income=19000, lender_type="building_society",
                 product_fee=995, accepts_low_income=True),

            # Additional mainstream for variety
            Deal(lender="Halifax", rate=4.71, ltv_max=60, min_loan=10000, max_loan=1000000,
                 min_credit_score=700, min_income=22000, lender_type="mainstream", product_fee=999),
            Deal(lender="Halifax", rate=4.89, ltv_max=75, min_loan=10000, max_loan=1000000,
                 min_credit_score=670, min_income=22000, lender_type="mainstream", product_fee=999),
            Deal(lender="Halifax", rate=5.14, ltv_max=85, min_loan=10000, max_loan=750000,
                 min_credit_score=640, min_income=25000, lender_type="mainstream", product_fee=999),

            Deal(lender="Santander", rate=4.67, ltv_max=60, min_loan=25000, max_loan=2000000,
                 min_credit_score=710, min_income=28000, lender_type="mainstream", product_fee=999),
            Deal(lender="Santander", rate=4.82, ltv_max=75, min_loan=25000, max_loan=1000000,
                 min_credit_score=680, min_income=25000, lender_type="mainstream", product_fee=999),

            Deal(lender="NatWest", rate=4.72, ltv_max=60, min_loan=25000, max_loan=1000000,
                 min_credit_score=700, min_income=25000, lender_type="mainstream", product_fee=999),
            Deal(lender="NatWest", rate=4.87, ltv_max=75, min_loan=25000, max_loan=1000000,
                 min_credit_score=670, min_income=23000, lender_type="mainstream", product_fee=999),
        ]
        db.session.add_all(all_deals)
        db.session.commit()
        print(f"✅ Added {len(all_deals)} mortgage deals (mainstream + specialist bad credit & low income lenders)")


# -------------------------------------------------
# Scheduler
# -------------------------------------------------
def start_scheduler_if_enabled(app):
    """
    Avoid multiple schedulers under Gunicorn by guarding with env.
    Set SCHEDULER_ENABLED=1 on one process (or on Railway Variables).
    """
    if os.getenv('SCHEDULER_ENABLED', '1') != '1':
        print("⏭️ Scheduler disabled by SCHEDULER_ENABLED")
        return

    try:
        scheduler = BackgroundScheduler()
        try:
            # optional: only if you actually have this util
            from app.utils.refresh_deals import refresh_deals
            scheduler.add_job(func=refresh_deals, trigger="interval", hours=24)
        except Exception as e:
            # No-op if the module isn't present
            print("⚠️ refresh_deals not wired or import failed:", e)
        scheduler.start()
        print("✅ Daily mortgage deal refresh scheduler started!")
    except Exception as e:
        print("⚠️ Scheduler error:", e)


# -------------------------------------------------
# App instance (Gunicorn imports this via wsgi:app)
# -------------------------------------------------
app = create_app()


if __name__ == '__main__':
    print("🚀 MortgageDealsHub running locally")
    # Only enable debug mode if explicitly in development
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)

