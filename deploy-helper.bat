@echo off
echo ========================================
echo  MortgageMaster Deployment Helper
echo ========================================
echo.

REM Step 1: Generate SECRET_KEY
echo [STEP 1] Generating SECRET_KEY...
echo.
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" > .secret_key.txt
type .secret_key.txt
echo.
echo ^^ COPY THIS SECRET_KEY - You'll need it for Railway!
echo.
pause

echo.
echo ========================================
echo [STEP 2] Next Steps:
echo ========================================
echo.
echo 1. Go to https://dashboard.stripe.com/test/apikeys
echo 2. Roll your API keys (old ones were exposed!)
echo 3. Copy your new keys
echo.
echo 4. Go to https://myaccount.google.com/security
echo 5. Create Gmail App Password
echo.
echo 6. Go to https://railway.app
echo 7. Login with GitHub
echo 8. Deploy your repository
echo.
pause

echo.
echo ========================================
echo Opening browser windows...
echo ========================================
start https://dashboard.stripe.com/test/apikeys
start https://myaccount.google.com/security
start https://railway.app
echo.
echo Done! Follow the instructions above.
pause
