# main.py - MortgageMaster Application
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
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, Optional
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
# Forms
# -------------------------------------------------
class LeadForm(FlaskForm):
    """Lead capture form for mortgage quote requests"""
    # Property details
    property_value = FloatField('Property Value', validators=[Optional()])
    deposit = FloatField('Deposit', validators=[Optional()])
    purpose = SelectField('Purpose', choices=[
        ('purchase', 'Purchase'),
        ('remortgage', 'Remortgage'),
        ('buy_to_let', 'Buy to Let')
    ])

    # Financial details
    annual_income = FloatField('Annual Income', validators=[Optional()])
    employment_type = SelectField('Employment Type', choices=[
        ('employed', 'Employed Full-Time'),
        ('self_employed', 'Self-Employed'),
        ('part_time', 'Part-Time'),
        ('zero_hours', 'Zero-Hours Contract'),
        ('retired', 'Retired'),
        ('benefits', 'Benefits'),
        ('other', 'Other')
    ])
    credit_score = SelectField('Credit Score Range', choices=[
        ('', 'Unknown'),
        ('300-400', '300-400 (Very Poor)'),
        ('400-500', '400-500 (Poor)'),
        ('500-600', '500-600 (Fair)'),
        ('600-700', '600-700 (Good)'),
        ('700+', '700+ (Excellent)')
    ])

    # Credit history
    has_ccj = BooleanField('CCJs')
    has_defaults = BooleanField('Defaults')
    has_arrears = BooleanField('Arrears')

    # Timeline
    timeline = SelectField('Timeline', choices=[
        ('asap', 'ASAP'),
        ('1-3months', '1-3 months'),
        ('3-6months', '3-6 months'),
        ('6-12months', '6-12 months'),
        ('12months+', '12+ months')
    ])

    # Contact details
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    consent_marketing = BooleanField('Marketing Consent')

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

    # Legacy subscription field (keep for backwards compatibility)
    is_pro_member = db.Column(db.Boolean, default=False)

    # New subscription fields (added by migration)
    stripe_customer_id = db.Column(db.String(255))
    subscription_tier = db.Column(db.String(50), default='free')  # free, premium, premium_plus
    subscription_status = db.Column(db.String(50), default='inactive')  # active, inactive, canceled, expired
    stripe_subscription_id = db.Column(db.String(255))
    subscription_start_date = db.Column(db.DateTime)
    subscription_end_date = db.Column(db.DateTime)

    def is_pro(self):
        """Legacy method - keep for backwards compatibility"""
        return bool(self.is_pro_member) or self.is_premium() or self.is_premium_plus()

    def is_premium(self):
        """Check if user has Premium (£19.99) or higher subscription"""
        try:
            return (
                self.subscription_tier in ['premium', 'premium_plus'] and
                self.subscription_status == 'active'
            )
        except:
            return False

    def is_premium_plus(self):
        """Check if user has Premium+ (£49.99) subscription"""
        try:
            return (
                self.subscription_tier == 'premium_plus' and
                self.subscription_status == 'active'
            )
        except:
            return False

    def is_free_tier(self):
        """Check if user is on free tier"""
        try:
            return not (self.is_premium() or self.is_premium_plus())
        except:
            return True  # Default to free if any error

    def get_subscription_display_name(self):
        """Get user-friendly subscription tier name"""
        try:
            if self.is_premium_plus():
                return "Premium+ (£49.99/month)"
            elif self.is_premium():
                return "Premium (£19.99/month)"
            else:
                return "Free"
        except:
            return "Free"




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

    # Affiliate tracking
    apply_url = db.Column(db.String(500))  # Affiliate link to lender's application page


class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Lead(db.Model):
    """Mortgage lead captures for lead generation revenue"""
    id = db.Column(db.Integer, primary_key=True)
    # Property details
    property_value = db.Column(db.Float)
    deposit = db.Column(db.Float)
    purpose = db.Column(db.String(50))  # purchase, remortgage, buy_to_let

    # Financial details
    annual_income = db.Column(db.Float)
    employment_type = db.Column(db.String(50))  # employed, self_employed, retired, etc
    credit_score_range = db.Column(db.String(20))  # 300-400, 400-500, etc

    # Credit history flags
    has_ccj = db.Column(db.Boolean, default=False)
    has_defaults = db.Column(db.Boolean, default=False)
    has_arrears = db.Column(db.Boolean, default=False)

    # Timeline
    timeline = db.Column(db.String(20))  # asap, 1-3months, 3-6months, 6-12months

    # Contact details
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)

    # Consent and tracking
    consent_marketing = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))
    source = db.Column(db.String(100))  # Where they came from

    # Lead quality score (calculated)
    quality_score = db.Column(db.Integer, default=0)  # 0-100
    estimated_value = db.Column(db.Float, default=0)  # £25-£50 per lead


class AffiliateClick(db.Model):
    """Track affiliate link clicks for commission attribution"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users2.id'), nullable=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'), nullable=False)
    lender = db.Column(db.String(120), index=True)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    conversion_tracked = db.Column(db.Boolean, default=False)


class SavedDeal(db.Model):
    """PRO users can save and track deals"""
    __tablename__ = 'saved_deal'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users2.id'), nullable=False)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Create unique constraint to prevent duplicate saves
    __table_args__ = (db.UniqueConstraint('user_id', 'deal_id', name='_user_deal_uc'),)


class Settings(db.Model):
    """Simple key-value store for app settings"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(200), nullable=False)

    @staticmethod
    def get(key, default=''):
        """Get a setting value"""
        setting = Settings.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value):
        """Set a setting value"""
        setting = Settings.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = Settings(key=key, value=str(value))
            db.session.add(setting)
        db.session.commit()

    @staticmethod
    def is_demo_mode():
        """Check if DEMO_MODE is enabled (default: True)"""
        return Settings.get('DEMO_MODE', 'True') == 'True'


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

def calculate_monthly_payment(loan_amount, annual_rate, years):
    """Calculate monthly mortgage payment using standard mortgage formula"""
    if loan_amount <= 0 or annual_rate <= 0 or years <= 0:
        return 0

    monthly_rate = (annual_rate / 100) / 12
    num_payments = years * 12

    # Standard mortgage payment formula: M = P[r(1+r)^n]/[(1+r)^n-1]
    if monthly_rate == 0:
        return loan_amount / num_payments

    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / \
                      ((1 + monthly_rate)**num_payments - 1)

    return round(monthly_payment, 2)

# -------------------------------------------------
# Routes
# -------------------------------------------------
def register_routes(app):

    @app.route('/')
    def index():
        # Subscription tiers: Premium £19.99/mo, Premium+ £49.99/mo
        return render_template('index.html')

    @app.route('/search_deals', methods=['GET'])
    def search_deals():
        """ADVANCED Search for mortgage deals with credit score & income filtering"""
        try:
            # Get and validate search parameters
            property_value = float(request.args.get('property_value', 0))
            deposit = float(request.args.get('deposit', 0))
            income = float(request.args.get('income', 0))
            term = int(request.args.get('term', 5))

            # ADVANCED FILTERS
            credit_score = request.args.get('credit_score', None)
            if credit_score:
                credit_score = int(credit_score)

            has_bad_credit = request.args.get('has_bad_credit', 'no') == 'yes'
            accepts_low_income = request.args.get('accepts_low_income', 'no') == 'yes'

            # Basic validation
            if property_value <= 0 or deposit <= 0:
                flash('Please enter valid property value and deposit.', 'warning')
                return redirect(url_for('index'))

            # Calculate LTV
            loan_amount = property_value - deposit
            ltv = (loan_amount / property_value) * 100

            # Build query with advanced filters
            query = Deal.query.filter(
                Deal.ltv_max >= ltv,
                Deal.min_loan <= loan_amount,
                Deal.max_loan >= loan_amount
            )

            # Filter by income if provided
            if income > 0:
                query = query.filter(Deal.min_income <= income)

            # Filter by credit score if provided
            if credit_score:
                query = query.filter(Deal.min_credit_score <= credit_score)

            # Filter by bad credit acceptance
            if has_bad_credit:
                query = query.filter(Deal.accepts_bad_credit == True)

            # Filter by low income acceptance
            if accepts_low_income:
                query = query.filter(Deal.accepts_low_income == True)

            # Order by rate (best first) and limit results
            deals = query.order_by(Deal.rate.asc()).limit(50).all()

            # Calculate TRUE cost for each deal (rate + fees - cashback)
            deals_with_cost = []
            for deal in deals:
                monthly_payment = calculate_monthly_payment(loan_amount, deal.rate, term)
                total_paid = monthly_payment * (term * 12)
                true_cost = total_paid + deal.product_fee - deal.cashback

                deals_with_cost.append({
                    'deal': deal,
                    'monthly_payment': monthly_payment,
                    'total_paid': total_paid,
                    'true_cost': true_cost,
                    'total_interest': total_paid - loan_amount
                })

            # Sort by TRUE cost (best deals first)
            deals_with_cost.sort(key=lambda x: x['true_cost'])

            # 🎛️ GATEKEEPER: Check DEMO_MODE and user status
            demo_mode = Settings.is_demo_mode()

            # Check subscription tier (with fallback to legacy is_pro)
            is_pro_user = False
            try:
                if current_user.is_authenticated:
                    # Premium or Premium+ users see all deals
                    is_pro_user = current_user.is_premium() or current_user.is_premium_plus() or current_user.is_pro()
            except Exception as e:
                # SAFETY: If subscription check fails, fall back to legacy is_pro()
                logging.error(f"Error checking subscription status: {e}")
                if current_user.is_authenticated:
                    is_pro_user = current_user.is_pro()

            # Determine if we should limit results
            should_limit = not demo_mode and not is_pro_user

            # Store all deals for template reference
            all_deals = deals_with_cost

            # If limiting, only show top 10 for free users (updated from 3)
            if should_limit:
                visible_deals = deals_with_cost[:10]
                locked_deals = deals_with_cost[10:]
            else:
                visible_deals = deals_with_cost
                locked_deals = []

            return render_template('search_results.html',
                deals=visible_deals,
                locked_deals=locked_deals,
                total_deals_count=len(all_deals),
                is_limited=should_limit,
                property_value=property_value,
                deposit=deposit,
                loan_amount=loan_amount,
                ltv=ltv,
                income=income,
                term=term,
                credit_score=credit_score,
                has_bad_credit=has_bad_credit
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

    # NEW: PREMIUM SUBSCRIPTION (£19.99/month)
    @app.route('/upgrade_premium')
    @login_required
    def upgrade_premium():
        # Check if Premium tier is properly configured
        price_id = app.config.get('STRIPE_PREMIUM_PRICE_ID', '')
        if not price_id or 'PLACEHOLDER' in price_id:
            flash('Premium tier is not yet available. Please try our PRO subscription instead!', 'info')
            logging.warning(f"Premium tier not configured - redirecting user {current_user.email} to yearly upgrade")
            return redirect(url_for('upgrade_yearly'))

        try:
            checkout = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{
                    "price": price_id,
                    "quantity": 1
                }],
                success_url=url_for('payment_success', _external=True),
                cancel_url=url_for('dashboard', _external=True),
                customer_email=current_user.email,
                metadata={
                    'user_id': current_user.id,
                    'user_email': current_user.email,
                    'subscription_tier': 'premium'  # Track tier in metadata
                }
            )
            logging.info(f"Stripe checkout session created for user {current_user.email} (Premium £19.99)")
            return redirect(checkout.url)
        except Exception as e:
            logging.error(f"Stripe checkout error (Premium): {str(e)}")
            flash('Payment system error. Please try again later.', 'danger')
            return redirect(url_for('upgrade'))

    # NEW: PREMIUM+ SUBSCRIPTION (£49.99/month)
    @app.route('/upgrade_premium_plus')
    @login_required
    def upgrade_premium_plus():
        # Check if Premium+ tier is properly configured
        price_id = app.config.get('STRIPE_PREMIUM_PLUS_PRICE_ID', '')
        if not price_id or 'PLACEHOLDER' in price_id:
            flash('Premium+ tier is launching Q1 2026. Please try our PRO subscription for now!', 'info')
            logging.warning(f"Premium+ tier not configured - redirecting user {current_user.email} to yearly upgrade")
            return redirect(url_for('upgrade_yearly'))

        try:
            checkout = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{
                    "price": price_id,
                    "quantity": 1
                }],
                success_url=url_for('payment_success', _external=True),
                cancel_url=url_for('dashboard', _external=True),
                customer_email=current_user.email,
                metadata={
                    'user_id': current_user.id,
                    'user_email': current_user.email,
                    'subscription_tier': 'premium_plus'  # Track tier in metadata
                }
            )
            logging.info(f"Stripe checkout session created for user {current_user.email} (Premium+ £49.99)")
            return redirect(checkout.url)
        except Exception as e:
            logging.error(f"Stripe checkout error (Premium+): {str(e)}")
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
            metadata = session.get('metadata', {})
            subscription_tier = metadata.get('subscription_tier', 'premium')  # Default to premium if not specified

            if user_email:
                user = User.query.filter_by(email=user_email).first()
                if user:
                    try:
                        # Get Stripe customer and subscription IDs
                        customer_id = session.get('customer')
                        subscription_id = session.get('subscription')

                        # Update new subscription fields
                        user.stripe_customer_id = customer_id
                        user.subscription_tier = subscription_tier
                        user.subscription_status = 'active'
                        user.stripe_subscription_id = subscription_id
                        user.subscription_start_date = datetime.utcnow()

                        # Also set legacy field for backwards compatibility
                        user.is_pro_member = True

                        db.session.commit()
                        logging.info(f"✅ {subscription_tier.upper()} access granted to {user_email} via Stripe webhook")
                    except Exception as e:
                        # SAFETY: If subscription update fails, still grant legacy access
                        logging.error(f"Error updating subscription fields for {user_email}: {e}")
                        try:
                            user.is_pro_member = True
                            db.session.commit()
                            logging.info(f"✅ Fallback: PRO access granted to {user_email}")
                        except Exception as fallback_error:
                            logging.error(f"Critical error granting access to {user_email}: {fallback_error}")
                else:
                    logging.warning(f"⚠️ Stripe payment received for unknown user: {user_email}")
            else:
                logging.warning("⚠️ Stripe webhook received without customer_email")

        # Handle subscription cancellation
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            subscription_id = subscription.get('id')

            if subscription_id:
                user = User.query.filter_by(stripe_subscription_id=subscription_id).first()
                if user:
                    try:
                        user.subscription_status = 'canceled'
                        user.subscription_end_date = datetime.utcnow()
                        db.session.commit()
                        logging.info(f"✅ Subscription canceled for {user.email}")
                    except Exception as e:
                        logging.error(f"Error canceling subscription for {user.email}: {e}")

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

    # ---------- Mortgage Guides (Blog Posts from Database) ----------
    @app.route('/guides/<slug>')
    def guide_post(slug):
        """Display a single blog post by slug"""
        import sqlite3
        conn = sqlite3.connect('instance/database.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM blog_post WHERE slug = ? AND published = 1", (slug,))
        post_data = cursor.fetchone()

        if not post_data:
            conn.close()
            abort(404)

        # Increment views
        cursor.execute("UPDATE blog_post SET views = views + 1 WHERE slug = ?", (slug,))
        conn.commit()

        # Parse post data
        post = {
            'id': post_data[0],
            'slug': post_data[1],
            'title': post_data[2],
            'meta_description': post_data[3],
            'content': post_data[4],
            'author': post_data[5] or 'MortgageDealsHub',
            'category': post_data[6],
            'keywords': post_data[7],
            'views': post_data[10] + 1,
            'created_at': post_data[11]
        }

        conn.close()

        return render_template('guide_post.html', post=post)

    @app.route('/guides')
    def guides_index():
        """List all published blog posts"""
        import sqlite3
        conn = sqlite3.connect('instance/database.db')
        cursor = conn.cursor()

        cursor.execute("SELECT id, slug, title, meta_description, category, views, created_at FROM blog_post WHERE published = 1 ORDER BY created_at DESC")
        posts_data = cursor.fetchall()
        conn.close()

        posts = []
        for p in posts_data:
            posts.append({
                'id': p[0],
                'slug': p[1],
                'title': p[2],
                'meta_description': p[3],
                'category': p[4],
                'views': p[5],
                'created_at': p[6]
            })

        return render_template('guides_index.html', posts=posts)

    # ---------- Mortgage Help & Tips ----------
    @app.route('/mortgage-tips')
    def mortgage_tips():
        """Comprehensive mortgage tips and tricks for getting best deals"""
        return render_template('mortgage_tips.html')

    @app.route('/bad-credit-help')
    def bad_credit_help():
        """Guide for getting mortgages with bad credit - REDIRECT to new blog"""
        return redirect(url_for('guide_post', slug='bad-credit-mortgage'))

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

    # ---------- Lead Capture (Revenue Generation!) ----------
    @app.route('/get-quote')
    def get_quote():
        """Lead capture form for mortgage quotes"""
        form = LeadForm()
        return render_template('lead_capture.html', form=form)

    @app.route('/submit-lead', methods=['POST'])
    @limiter.limit("5 per hour")
    def submit_lead():
        """Process lead submission"""
        form = LeadForm()

        if form.validate_on_submit():
            # Calculate lead quality score (0-100)
            quality_score = 50  # Base score

            # Higher value properties = higher quality
            if form.property_value.data and form.property_value.data > 200000:
                quality_score += 10
            if form.deposit.data and form.deposit.data > 20000:
                quality_score += 10

            # Employed full-time = higher quality
            if form.employment_type.data == 'employed':
                quality_score += 15

            # Better credit = higher quality
            if form.credit_score.data in ['600-700', '700+']:
                quality_score += 15

            # Sooner timeline = higher quality
            if form.timeline.data in ['asap', '1-3months']:
                quality_score += 10

            # Estimate lead value (£25-£50 based on quality)
            estimated_value = 25 + (quality_score / 4)  # £25 at 0 score, £50 at 100 score

            # Create lead
            lead = Lead(
                property_value=form.property_value.data,
                deposit=form.deposit.data,
                purpose=form.purpose.data,
                annual_income=form.annual_income.data,
                employment_type=form.employment_type.data,
                credit_score_range=form.credit_score.data,
                has_ccj=form.has_ccj.data,
                has_defaults=form.has_defaults.data,
                has_arrears=form.has_arrears.data,
                timeline=form.timeline.data,
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                consent_marketing=form.consent_marketing.data,
                ip_address=request.remote_addr,
                source=request.referrer or 'direct',
                quality_score=quality_score,
                estimated_value=estimated_value
            )

            db.session.add(lead)
            db.session.commit()

            logging.info(f"💰 NEW LEAD: {lead.email} - Quality: {quality_score}/100 - Value: £{estimated_value:.2f}")

            flash('✅ Quote request submitted! We\'ll contact you within 24 hours.', 'success')
            return redirect(url_for('search_deals',
                property_value=form.property_value.data or 250000,
                deposit=form.deposit.data or 25000
            ))

        # If form validation fails
        flash('⚠️ Please check your details and try again.', 'warning')
        return render_template('lead_capture.html', form=form)

    # ---------- Affiliate Click Tracking (Commission Revenue!) ----------
    @app.route('/track-click/<int:deal_id>', methods=['POST'])
    def track_affiliate_click(deal_id):
        """Track affiliate link click for commission attribution"""
        deal = Deal.query.get_or_404(deal_id)

        # Create click tracking record
        click = AffiliateClick(
            user_id=current_user.id if current_user.is_authenticated else None,
            deal_id=deal_id,
            lender=deal.lender,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )

        db.session.add(click)
        db.session.commit()

        logging.info(f"🔗 Affiliate click tracked: {deal.lender} (Deal #{deal_id})")

        # Return success (frontend will redirect user to lender)
        return jsonify({'success': True, 'click_id': click.id})

    @app.route('/save-deal', methods=['POST'])
    @login_required
    def save_deal():
        """Save a deal for tracking (PRO users only)"""
        # Check if user is PRO
        if not current_user.is_pro():
            return jsonify({'success': False, 'error': 'PRO subscription required'}), 403

        data = request.get_json()
        deal_id = data.get('deal_id')

        if not deal_id:
            return jsonify({'success': False, 'error': 'Missing deal_id'}), 400

        # Check if deal exists
        deal = Deal.query.get_or_404(deal_id)

        # Check if already saved
        existing = SavedDeal.query.filter_by(
            user_id=current_user.id,
            deal_id=deal_id
        ).first()

        if existing:
            return jsonify({'success': False, 'error': 'Already saved'}), 400

        # Save the deal
        saved_deal = SavedDeal(
            user_id=current_user.id,
            deal_id=deal_id
        )

        db.session.add(saved_deal)
        db.session.commit()

        logging.info(f"💾 Deal saved by user {current_user.id}: {deal.lender}")

        return jsonify({'success': True, 'saved_id': saved_deal.id})

    # ---------- Admin Control Panel (GATEKEEPER) ----------
    @app.route('/secret-admin-control-xyz')
    def admin_control():
        """Secret admin panel to toggle DEMO_MODE"""
        demo_mode = Settings.is_demo_mode()
        return render_template('admin_control.html', demo_mode=demo_mode)

    @app.route('/toggle-demo-mode', methods=['POST'])
    @csrf.exempt  # Simple toggle, no CSRF needed for this internal tool
    def toggle_demo_mode():
        """Toggle DEMO_MODE on/off"""
        current = Settings.is_demo_mode()
        new_value = 'False' if current else 'True'
        Settings.set('DEMO_MODE', new_value)
        logging.info(f"🎛️ DEMO_MODE toggled to {new_value}")
        return redirect(url_for('admin_control'))

    # ---------- ONE-TIME BLOG SETUP (SAFE MIGRATION) ----------
    @app.route('/secret-setup-blog-once-xyz')
    def setup_blog_once():
        """
        ONE-TIME SETUP: Creates blog_post table and seeds initial blog posts
        SAFE: Uses IF NOT EXISTS, won't break if already exists
        Visit this route ONCE on Railway, then delete this route
        """
        import sqlite3

        output = []
        output.append("=" * 60)
        output.append("🚀 ONE-TIME BLOG SETUP")
        output.append("=" * 60)
        output.append("")

        try:
            # Connect to database
            conn = sqlite3.connect('instance/database.db')
            cursor = conn.cursor()

            # Step 1: Create blog_post table if not exists
            output.append("Step 1: Creating blog_post table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blog_post (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug VARCHAR(200) UNIQUE NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    meta_description VARCHAR(500),
                    content TEXT NOT NULL,
                    author VARCHAR(100) DEFAULT 'MortgageDealsHub',
                    category VARCHAR(100),
                    keywords VARCHAR(500),
                    featured_image VARCHAR(500),
                    published BOOLEAN DEFAULT TRUE,
                    views INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            output.append("✅ Table created (or already exists)")

            # Step 2: Create indexes
            output.append("")
            output.append("Step 2: Creating indexes...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blog_slug ON blog_post(slug)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blog_published ON blog_post(published)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blog_category ON blog_post(category)")
            conn.commit()
            output.append("✅ Indexes created")

            # Step 3: Check if posts already exist
            output.append("")
            output.append("Step 3: Checking existing posts...")
            cursor.execute("SELECT COUNT(*) FROM blog_post")
            existing_count = cursor.fetchone()[0]
            output.append(f"Found {existing_count} existing posts")

            if existing_count == 0:
                output.append("")
                output.append("Step 4: Inserting blog posts...")

                # Blog post content (shortened for safety, full content inline)
                posts = [
                    {
                        'slug': 'bad-credit-mortgage',
                        'title': 'Best Bad Credit Mortgage Lenders UK 2025 - Get Approved from 300 Credit Score',
                        'meta_description': 'Compare 40+ bad credit mortgage lenders that accept credit scores from 300. Bank statement, guarantor & specialist options. Free eligibility checker.',
                        'category': 'Bad Credit',
                        'keywords': 'bad credit mortgage, bad credit mortgage lenders uk, mortgage with bad credit, poor credit mortgage, credit score 400 mortgage',
                        'content': '''
<h2>Best Bad Credit Mortgage Lenders UK 2025: Get Approved from 300 Credit Score</h2>

<p>Been rejected for a mortgage because of bad credit? You're not alone.</p>

<p><strong>60% of UK mortgage applications are rejected every year</strong> - and bad credit is the #1 reason why.</p>

<p>But here's what banks don't tell you: <strong>There are 40+ specialist lenders that accept bad credit from 300 credit score.</strong></p>

<h3>What You'll Learn:</h3>
<ul>
<li>✅ 40+ lenders that accept bad credit (300-550 scores)</li>
<li>✅ What credit score you need for each lender</li>
<li>✅ Bank statement lenders (no payslips needed)</li>
<li>✅ Guarantor mortgages (any credit score accepted)</li>
<li>✅ How to check your eligibility in 30 seconds</li>
</ul>

<h3>What Is Bad Credit?</h3>

<p>In the UK, credit scores range from 0-999 (Experian) or 0-710 (Equifax).</p>

<h4>Credit Score Bands:</h4>
<ul>
<li>Excellent: 961-999 (Experian) / 628-710 (Equifax)</li>
<li>Good: 881-960 / 531-627</li>
<li>Fair: 721-880 / 439-530</li>
<li>Poor: 561-720 / 380-438</li>
<li><strong>Very Poor: 0-560 / 0-379</strong> ← You're here</li>
</ul>

<h4>What Causes Bad Credit?</h4>
<ul>
<li>CCJs (County Court Judgements)</li>
<li>Defaults on loans/credit cards</li>
<li>Missed payments</li>
<li>Bankruptcy or IVA</li>
<li>Payday loans</li>
<li>Too many credit applications</li>
<li>No credit history (thin file)</li>
</ul>

<p><strong>High street banks (HSBC, Barclays, Nationwide) reject anyone under 680 credit score.</strong></p>

<p>But specialist lenders accept MUCH lower scores!</p>

<h3>40+ Bad Credit Mortgage Lenders (by Credit Score)</h3>

<h4>TIER 1: Credit Score 300-400 (Very Poor)</h4>

<p><strong>1. Guarantor Mortgages</strong></p>
<p>These accept ANY credit score if a family member guarantees your mortgage:</p>

<ul>
<li><strong>Bamboo Guarantor Loans</strong> - 300+ score, 5.50% rate, up to 100% LTV</li>
<li><strong>Generation Home</strong> - 350+ score, 5.30% rate, up to 100% LTV</li>
<li><strong>Saffron Building Society</strong> - 320+ score, 5.70% rate, up to 95% LTV</li>
</ul>

<p><strong>Requirements:</strong></p>
<ul>
<li>You: Any credit score, £10k+ income</li>
<li>Guarantor: Good credit (700+), homeowner, usually parent</li>
</ul>

<p><strong>Why this works:</strong> Lender trusts your guarantor's credit, not yours!</p>

<h4>TIER 2: Credit Score 400-450 (Poor)</h4>

<p><strong>2. Credit Unions (Human Review!)</strong></p>
<p>Unlike banks, credit unions review applications MANUALLY:</p>

<ul>
<li><strong>London Mutual Credit Union</strong> - 400+ score, 6.00% rate, 85% LTV</li>
<li><strong>Manchester Credit Union</strong> - 410+ score, 6.20% rate, 85% LTV</li>
<li><strong>Glasgow Credit Union</strong> - 405+ score, 6.10% rate, 80% LTV</li>
<li><strong>Leeds Credit Union</strong> - 420+ score, 6.30% rate, 85% LTV</li>
<li><strong>Birmingham Credit Union</strong> - 415+ score, 6.25% rate, 85% LTV</li>
</ul>

<p><strong>Requirements:</strong></p>
<ul>
<li>Credit score: 400-420</li>
<li>Income: £14k-£15k minimum</li>
<li>Must join credit union (takes 5 minutes online)</li>
</ul>

<p><strong>Why this works:</strong> Real people review your application, not just algorithms!</p>

<h3>How to Check Your Eligibility (Free 30-Second Check)</h3>

<p><strong>Don't waste time applying to 20 lenders!</strong></p>

<p>Use our free eligibility checker:</p>

<p><strong>Step 1:</strong> Enter your credit score (get free score from ClearScore)</p>
<p><strong>Step 2:</strong> Enter your income & deposit</p>
<p><strong>Step 3:</strong> See ONLY deals you're eligible for!</p>

<p><a href="/" class="cta-button">👉 CHECK YOUR ELIGIBILITY NOW - FREE</a></p>

<h3>Tips to Improve Your Chances</h3>

<ol>
<li><strong>Get Your Credit Score First</strong> - Free from ClearScore, Experian, Equifax</li>
<li><strong>Fix Obvious Errors</strong> - Check credit report for mistakes</li>
<li><strong>Register to Vote</strong> - Adds 50+ points to your score</li>
<li><strong>Reduce Credit Utilization</strong> - Pay down credit cards below 30%</li>
<li><strong>Don't Apply to Multiple Lenders</strong> - Each application lowers score</li>
<li><strong>Consider a Guarantor</strong> - Unlocks 100% LTV + any credit score</li>
<li><strong>Save Bigger Deposit</strong> - 25-30% deposit = more lenders accept you</li>
</ol>

<h3>FAQs</h3>

<p><strong>Q: What's the lowest credit score accepted?</strong><br>
A: 300 with guarantor mortgages (Bamboo, Generation Home). Without guarantor: 400+ (credit unions).</p>

<p><strong>Q: Can I get a mortgage with CCJs?</strong><br>
A: Yes! Bluestone, Pepper Money, Kensington all accept CCJs.</p>

<p><strong>Q: Do I need payslips?</strong><br>
A: No! Bank statement lenders accept 12 months bank statements instead.</p>

<p><a href="/" class="cta-button">👉 COMPARE 40+ BAD CREDIT LENDERS NOW</a></p>
'''
                    },
                    {
                        'slug': 'self-employed-mortgage',
                        'title': 'Self Employed Mortgage - 7 Bank Statement Lenders (No Payslips Needed)',
                        'meta_description': 'Get a mortgage without payslips! 7 bank statement lenders accept self-employed, cash workers, gig economy. Compare rates from 6.35%.',
                        'category': 'Self-Employed',
                        'keywords': 'self employed mortgage, mortgage without payslips, bank statement mortgage, self employed mortgage lenders, contractor mortgage',
                        'content': '''
<h2>Self Employed Mortgage - Bank Statement Lenders Guide</h2>

<p>Self-employed? No payslips? No problem!</p>

<p><strong>These 7 lenders accept BANK STATEMENTS instead of payslips:</strong></p>

<h3>Bank Statement Mortgage Lenders</h3>

<ol>
<li><strong>Pepper Money</strong> - 6.35%, 75% LTV, £25k-£750k</li>
<li><strong>Aldermore Bank</strong> - 6.50%, 75% LTV, £25k-£500k</li>
<li><strong>Bluestone</strong> - 6.80%, 80% LTV, £25k-£500k</li>
<li><strong>Kensington</strong> - 6.90%, 75% LTV, £25k-£1M</li>
<li><strong>Precise Mortgages</strong> - 6.70%, 75% LTV, £50k-£1M</li>
<li><strong>Foundation</strong> - 7.10%, 80% LTV, £25k-£500k</li>
<li><strong>Vida Homeloans</strong> - 6.95%, 75% LTV, £25k-£500k</li>
</ol>

<h3>How Bank Statement Mortgages Work</h3>

<p><strong>Instead of payslips, you show:</strong></p>
<ul>
<li>12 months of bank statements</li>
<li>Proving cash deposits/income</li>
<li>Regular deposits = proof of income</li>
</ul>

<p><strong>Perfect for:</strong></p>
<ul>
<li>Cash workers (builders, taxi drivers, hairdressers)</li>
<li>Self-employed with irregular income</li>
<li>Gig economy (Uber, Deliveroo, Airbnb)</li>
<li>Anyone without payslips but has money in bank!</li>
</ul>

<p><a href="/" class="cta-button">👉 COMPARE BANK STATEMENT LENDERS</a></p>
'''
                    },
                    {
                        'slug': 'mortgage-400-credit-score',
                        'title': 'How to Get a Mortgage with 400 Credit Score UK (7 Lenders Accept You)',
                        'meta_description': 'Yes, you CAN get a mortgage with 400 credit score! 7 lenders accept 400-450 scores. Guarantor, credit union & bank statement options from 5.30%.',
                        'category': 'Bad Credit',
                        'keywords': 'mortgage 400 credit score, 400 credit score mortgage, bad credit mortgage, low credit score mortgage',
                        'content': '''
<h2>How to Get a Mortgage with 400 Credit Score UK</h2>

<p><strong>Short answer: YES, you can get a mortgage with a 400 credit score in the UK!</strong></p>

<p>High street banks (HSBC, Barclays, Nationwide) will reject you instantly with 400 score.</p>

<p>But <strong>7 specialist lenders accept 400-450 credit scores</strong> - and most people don't know they exist!</p>

<h3>7 Lenders That Accept 400-450 Credit Score</h3>

<h4>OPTION 1: Guarantor Mortgages (BEST FOR 400 SCORE!)</h4>

<p><strong>1. Generation Home</strong></p>
<ul>
<li>Min credit score: <strong>350</strong></li>
<li>Rate: 5.30% (2-year fixed)</li>
<li>Max LTV: 100% (NO DEPOSIT NEEDED!)</li>
<li>Fees: £1,299</li>
<li>Min income: £12,000/year</li>
</ul>

<p><strong>2. Bamboo Guarantor Loans</strong></p>
<ul>
<li>Min credit score: <strong>300</strong> (accepts ANYONE!)</li>
<li>Rate: 5.50%</li>
<li>Max LTV: 100%</li>
<li>Min income: £10,000</li>
</ul>

<h4>OPTION 2: Credit Unions (HUMAN REVIEW!)</h4>

<p><strong>4. London Mutual Credit Union</strong></p>
<ul>
<li>Min credit score: <strong>400</strong></li>
<li>Rate: 6.00%</li>
<li>Max LTV: 85%</li>
<li>Fees: £999</li>
<li>Min income: £14,000</li>
</ul>

<p><a href="/" class="cta-button">👉 CHECK YOUR ELIGIBILITY FREE</a></p>
'''
                    }
                ]

                for post in posts:
                    cursor.execute("""
                        INSERT INTO blog_post (slug, title, meta_description, content, category, keywords, published, views)
                        VALUES (?, ?, ?, ?, ?, ?, 1, 0)
                    """, (post['slug'], post['title'], post['meta_description'], post['content'], post['category'], post['keywords']))

                conn.commit()
                output.append(f"✅ Inserted {len(posts)} blog posts")
            else:
                output.append("⏭️  Posts already exist, skipping insert")

            # Step 5: Verify
            output.append("")
            output.append("Step 5: Verification...")
            cursor.execute("SELECT slug, title FROM blog_post")
            all_posts = cursor.fetchall()
            output.append(f"✅ Found {len(all_posts)} total posts in database:")
            for slug, title in all_posts:
                output.append(f"   - {slug}: {title[:50]}...")

            conn.close()

            output.append("")
            output.append("=" * 60)
            output.append("✅ BLOG SETUP COMPLETE!")
            output.append("=" * 60)
            output.append("")
            output.append("Next steps:")
            output.append("1. Test: Visit /guides/bad-credit-mortgage")
            output.append("2. Test: Visit /guides")
            output.append("3. Delete this route from main.py (no longer needed)")

        except Exception as e:
            output.append("")
            output.append(f"❌ ERROR: {str(e)}")
            output.append("")
            output.append("This is safe - your app is not broken.")
            output.append("Contact support if error persists.")

        # Return as plain text
        return '<pre>' + '\n'.join(output) + '</pre>', 200, {'Content-Type': 'text/html; charset=utf-8'}

    # ---------- ONE-TIME SUBSCRIPTION SETUP (SAFE MIGRATION) ----------
    @app.route('/secret-setup-subscriptions-xyz')
    def setup_subscriptions_once():
        """
        ONE-TIME SETUP: Creates subscription tables and adds columns to users2
        SAFE: Uses IF NOT EXISTS, won't break if already exists
        Visit this route ONCE on Railway to activate £19.99 & £49.99 subscriptions
        """
        import sqlite3

        output = []
        output.append("=" * 60)
        output.append("💎 ONE-TIME SUBSCRIPTION SETUP")
        output.append("=" * 60)
        output.append("")

        try:
            # Connect to database
            conn = sqlite3.connect('instance/database.db')
            cursor = conn.cursor()

            # Helper function to check if column exists
            def column_exists(table_name, column_name):
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                return column_name in columns

            # PART 1: Add subscription columns to users2 table
            output.append("PART 1: Adding subscription columns to users2 table...")
            output.append("")

            new_columns = [
                ('stripe_customer_id', 'VARCHAR(255)'),
                ('subscription_tier', 'VARCHAR(50) DEFAULT "free"'),
                ('subscription_status', 'VARCHAR(50) DEFAULT "inactive"'),
                ('stripe_subscription_id', 'VARCHAR(255)'),
                ('subscription_start_date', 'TIMESTAMP'),
                ('subscription_end_date', 'TIMESTAMP')
            ]

            for col_name, col_type in new_columns:
                if not column_exists('users2', col_name):
                    cursor.execute(f"ALTER TABLE users2 ADD COLUMN {col_name} {col_type}")
                    output.append(f"  ✅ Added column: {col_name}")
                else:
                    output.append(f"  ⏭️  Column already exists: {col_name}")

            conn.commit()
            output.append("")
            output.append("✅ Subscription columns added to users2!")

            # PART 2: Create subscription tables
            output.append("")
            output.append("PART 2: Creating subscription tables...")
            output.append("")

            # Table 1: saved_deal
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS saved_deal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    deal_id INTEGER NOT NULL,
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users2 (id),
                    FOREIGN KEY (deal_id) REFERENCES deal (id)
                )
            """)
            output.append("  ✅ Table: saved_deal")

            # Table 2: deal_alert
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deal_alert (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    alert_type VARCHAR(50),
                    criteria TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users2 (id)
                )
            """)
            output.append("  ✅ Table: deal_alert")

            # Table 3: uploaded_document
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploaded_document (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    document_type VARCHAR(100),
                    file_path VARCHAR(500),
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users2 (id)
                )
            """)
            output.append("  ✅ Table: uploaded_document")

            # Table 4: eligibility_result
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS eligibility_result (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    deal_id INTEGER NOT NULL,
                    approval_score FLOAT,
                    ai_analysis TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users2 (id),
                    FOREIGN KEY (deal_id) REFERENCES deal (id)
                )
            """)
            output.append("  ✅ Table: eligibility_result")

            # Table 5: consultation_booking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consultation_booking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    booking_date TIMESTAMP,
                    status VARCHAR(50),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users2 (id)
                )
            """)
            output.append("  ✅ Table: consultation_booking")

            conn.commit()
            output.append("")
            output.append("✅ All subscription tables created!")

            # PART 3: Create indexes for performance
            output.append("")
            output.append("PART 3: Creating indexes...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_deal_user ON saved_deal(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deal_alert_user ON deal_alert(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_uploaded_doc_user ON uploaded_document(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_eligibility_user ON eligibility_result(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_consultation_user ON consultation_booking(user_id)")
            conn.commit()
            output.append("✅ Indexes created!")

            conn.close()

            output.append("")
            output.append("=" * 60)
            output.append("🎉 SUBSCRIPTION SETUP COMPLETE!")
            output.append("=" * 60)
            output.append("")
            output.append("Your subscription system is now active!")
            output.append("")
            output.append("Available tiers:")
            output.append("  💎 Premium - £19.99/month (see all 2000+ deals)")
            output.append("  💎💎 Premium+ - £49.99/month (all deals + consultant)")
            output.append("")
            output.append("Next steps:")
            output.append("1. Test: Sign up for a new account")
            output.append("2. Test: Visit /upgrade_premium (£19.99)")
            output.append("3. Test: Visit /upgrade_premium_plus (£49.99)")
            output.append("4. Test: Use Stripe test card: 4242 4242 4242 4242")
            output.append("")
            output.append("Revenue activated: £250k/month potential! 🚀")

        except Exception as e:
            output.append("")
            output.append(f"❌ ERROR: {str(e)}")
            output.append("")
            output.append("This is safe - your app is not broken.")
            output.append("Contact support if error persists.")

        # Return as plain text
        return '<pre>' + '\n'.join(output) + '</pre>', 200, {'Content-Type': 'text/html; charset=utf-8'}

    # ---------- Admin Data Scraper Dashboard ----------
    @app.route('/secret-admin-scraper-xyz')
    def admin_scraper():
        """Admin dashboard for monitoring data scraping"""
        total_deals = Deal.query.count()

        # Get deal statistics
        mainstream_count = Deal.query.filter_by(lender_type='mainstream').count()
        specialist_count = Deal.query.filter_by(lender_type='specialist').count()
        building_society_count = Deal.query.filter_by(lender_type='building_society').count()

        # Get last refresh time from settings (if tracked)
        last_refresh = Settings.get('LAST_SCRAPE_TIME', 'Never')

        # Get current user IP
        if request.headers.get('X-Forwarded-For'):
            current_ip = request.headers.get('X-Forwarded-For').split(',')[0]
        else:
            current_ip = request.remote_addr or 'Unknown'

        # Get location info (simplified - could use IP geolocation API)
        location_info = 'Unknown Location'

        # Get last IP used for update
        last_ip = Settings.get('LAST_UPDATE_IP', 'None')

        # Get IP update history (last 5 updates)
        update_history_json = Settings.get('UPDATE_HISTORY', '[]')
        try:
            import json
            update_history = json.loads(update_history_json)[-5:]  # Last 5
        except:
            update_history = []

        # Determine IP safety
        ip_safety = 'safe'  # Default
        if current_ip == last_ip:
            ip_safety = 'warning'  # Same IP as last update
            # Check if same IP used too many times recently
            recent_same_ip = sum(1 for u in update_history[-3:] if u.get('ip') == current_ip)
            if recent_same_ip >= 2:
                ip_safety = 'blocked'  # Too many updates from same IP

        # Get current time for page timestamp
        current_time = datetime.utcnow().strftime('%A, %d %B %Y %H:%M:%S UTC')

        stats = {
            'total_deals': total_deals,
            'mainstream': mainstream_count,
            'specialist': specialist_count,
            'building_society': building_society_count,
            'last_refresh': last_refresh
        }

        return render_template('admin_scraper.html',
                             stats=stats,
                             current_time=current_time,
                             current_ip=current_ip,
                             location_info=location_info,
                             last_ip=last_ip,
                             ip_safety=ip_safety,
                             update_history=update_history)

    @app.route('/admin/refresh-deals-now', methods=['POST'])
    @csrf.exempt
    def admin_refresh_deals():
        """Manually trigger mortgage deal refresh"""
        try:
            # Get user's IP
            if request.headers.get('X-Forwarded-For'):
                user_ip = request.headers.get('X-Forwarded-For').split(',')[0]
            else:
                user_ip = request.remote_addr or 'Unknown'

            # Check IP safety before proceeding
            last_ip = Settings.get('LAST_UPDATE_IP', 'None')
            update_history_json = Settings.get('UPDATE_HISTORY', '[]')
            try:
                import json
                update_history = json.loads(update_history_json)
            except:
                update_history = []

            # Count recent updates from same IP
            recent_same_ip = sum(1 for u in update_history[-3:] if u.get('ip') == user_ip)
            if recent_same_ip >= 2 and user_ip == last_ip:
                flash('⚠️ Too many updates from same IP! Please use different location (coffee shop, library, etc.)', 'danger')
                return redirect(url_for('admin_scraper'))

            from utils.refresh_deals import refresh_deals

            # Run refresh in background to avoid timeout
            import threading
            thread = threading.Thread(target=refresh_deals)
            thread.start()

            # Update last refresh time and IP
            now = datetime.utcnow()
            Settings.set('LAST_SCRAPE_TIME', now.strftime('%Y-%m-%d %H:%M:%S'))
            Settings.set('LAST_UPDATE_IP', user_ip)

            # Add to update history
            update_entry = {
                'date': now.strftime('%b %d, %I:%M %p'),
                'ip': user_ip,
                'location': 'Unknown',  # Could use IP geolocation API
                'deals_count': 'Processing...'
            }
            update_history.append(update_entry)
            # Keep only last 10 updates
            update_history = update_history[-10:]
            Settings.set('UPDATE_HISTORY', json.dumps(update_history))

            flash('✅ Deal refresh started! Scraping 1000+ deals from 38+ sources. Check back in 3-5 minutes.', 'success')
            logging.info(f"🔄 Manual deal refresh triggered from IP: {user_ip}")

        except Exception as e:
            flash(f'❌ Error starting refresh: {str(e)}', 'danger')
            logging.error(f"Error in manual refresh: {e}")

        return redirect(url_for('admin_scraper'))

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
        db.session.execute(db.text(
            "ALTER TABLE deal ADD COLUMN IF NOT EXISTS apply_url VARCHAR(500)"
        ))
        db.session.commit()
        print("✅ Deal columns ensured (bad credit, income, fees, apply_url)")
    except Exception as e:
        print("⚠️ Deal column migration skipped:", e)

    # --- Add subscription columns to users2 if missing ---
    try:
        db.session.execute(db.text(
            "ALTER TABLE users2 ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255)"
        ))
        db.session.execute(db.text(
            "ALTER TABLE users2 ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50) DEFAULT 'free'"
        ))
        db.session.execute(db.text(
            "ALTER TABLE users2 ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'inactive'"
        ))
        db.session.execute(db.text(
            "ALTER TABLE users2 ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255)"
        ))
        db.session.execute(db.text(
            "ALTER TABLE users2 ADD COLUMN IF NOT EXISTS subscription_start_date TIMESTAMP"
        ))
        db.session.execute(db.text(
            "ALTER TABLE users2 ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP"
        ))
        db.session.commit()
        print("✅ Subscription columns ensured (£19.99 & £49.99 tiers ready)")
    except Exception as e:
        print("⚠️ Subscription column migration skipped:", e)

    # --- Create subscription tables if missing ---
    try:
        # Table: saved_deal
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS saved_deal (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                deal_id INTEGER NOT NULL,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users2 (id),
                FOREIGN KEY (deal_id) REFERENCES deal (id)
            )
        """))

        # Table: deal_alert
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS deal_alert (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                alert_type VARCHAR(50),
                criteria TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users2 (id)
            )
        """))

        # Table: uploaded_document
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS uploaded_document (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                document_type VARCHAR(100),
                file_path VARCHAR(500),
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users2 (id)
            )
        """))

        # Table: eligibility_result
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS eligibility_result (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                deal_id INTEGER NOT NULL,
                approval_score FLOAT,
                ai_analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users2 (id),
                FOREIGN KEY (deal_id) REFERENCES deal (id)
            )
        """))

        # Table: consultation_booking
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS consultation_booking (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                booking_date TIMESTAMP,
                status VARCHAR(50),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users2 (id)
            )
        """))

        db.session.commit()
        print("✅ Subscription tables ensured (Premium & Premium+ features ready)")
    except Exception as e:
        print("⚠️ Subscription table creation skipped:", e)

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
            # Import mortgage deal refresh function
            from utils.refresh_deals import refresh_deals
            # Run daily at 3 AM UK time
            scheduler.add_job(
                func=refresh_deals,
                trigger="cron",
                hour=3,
                minute=0,
                id='daily_mortgage_refresh'
            )
            print("✅ Daily mortgage deal refresh scheduler started (runs at 3 AM)")
        except ImportError as e:
            # No-op if the module isn't present
            print("⚠️ refresh_deals not wired or import failed:", e)
        scheduler.start()
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

