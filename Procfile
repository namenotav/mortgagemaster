# Railway deployment - 2025-11-19 - PRODUCTION
web: gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --log-level info
