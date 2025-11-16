# main.py
from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, flash, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from flask_mail import Mail
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os
import bcrypt
import stripe

# -------------------------------------------------
# Extensions (created once; app-bound in create_app)
# -------------------------------------------------
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

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

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

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
# Routes
# -------------------------------------------------
def register_routes(app):

    @app.route('/')
    def index():
        return render_template('index.html')

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
    def login():
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')

            user = User.query.filter_by(email=email).first()

            ok = False
            if user:
                try:
                    ok = bcrypt.checkpw(password.encode('utf-8'), user.password_hash)
                except ValueError:
                    # Old/bad password value in DB – just treat as invalid login
                    ok = False

            if ok:
                login_user(user)
                flash('Logged in successfully.', 'success')
                return redirect(url_for('dashboard'))

            flash('Invalid credentials', 'danger')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logged out successfully.', 'info')
        return redirect(url_for('login'))

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            if not (name and email and password):
                flash('All fields are required.', 'warning')
                return render_template('signup.html')

            if User.query.filter_by(email=email).first():
                flash('Email already registered. Try logging in.', 'info')
                return redirect(url_for('login'))

            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            new_user = User(name=name, email=email, password_hash=hashed)
            db.session.add(new_user)
            db.session.commit()
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
        checkout = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{
                "price": "price_1STXcVD2EDcoPFLNECjwrN1p",  # YOUR YEARLY PRICE
                "quantity": 1
            }],
            success_url=url_for('payment_success', _external=True),
            cancel_url=url_for('dashboard', _external=True),
            customer_email=current_user.email
        )
        return redirect(checkout.url)

    # MONTHLY PAYMENT (£4.99/month)
    @app.route('/upgrade_monthly')
    @login_required
    def upgrade_monthly():
        checkout = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{
                "price": "price_1STXbDD2EDcoPFLN6hEU2gS9",  # YOUR MONTHLY PRICE
                "quantity": 1
            }],
            success_url=url_for('payment_success', _external=True),
            cancel_url=url_for('dashboard', _external=True),
            customer_email=current_user.email
        )
        return redirect(checkout.url)

    from flask_login import current_user

    @app.route('/payment_success')
    def payment_success():
        if current_user.is_authenticated:
            current_user.is_pro_member = True
            db.session.commit()

        return render_template('payment_success.html')
 



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
    def subscribe():
        email = (request.form.get('email') or '').strip().lower()
        if not email:
            flash('Please enter a valid email.', 'warning')
            return redirect(url_for('index'))

        exists = Subscriber.query.filter_by(email=email).first()
        if exists:
            flash("You're already subscribed. 👍", 'info')
            return redirect(url_for('index'))

        db.session.add(Subscriber(email=email))
        db.session.commit()
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
        example_deals = [
            Deal(lender="Example Lender A", rate=5.2, ltv_max=75, min_loan=100000, max_loan=500000),
            Deal(lender="Example Lender B", rate=4.8, ltv_max=80, min_loan=50000,  max_loan=400000),
        ]
        db.session.add_all(example_deals)
        db.session.commit()
        print("✅ Added sample deals")


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
    app.run(debug=True, host='0.0.0.0', port=5000)

