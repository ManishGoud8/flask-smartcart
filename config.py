# config.py
# -----------------------------------------------------------------------------
# Configuration settings for SmartCart Project (Days 1 to 14)
# Stores Secret Key, Database credentials, Email SMTP, Razorpay API keys, and Upload paths
# -----------------------------------------------------------------------------
import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Secret key for Flask session management (Days 1, 3, 9, 11)
SECRET_KEY = os.environ.get('SECRET_KEY')

# -----------------------------------------------------------------------------
# SQLite Database Configuration (Days 1 to 14)
# -----------------------------------------------------------------------------
DB_NAME = os.environ.get('DB_NAME', 'smartcart.db')
DB_PATH = os.path.join(BASE_DIR, DB_NAME)

# -----------------------------------------------------------------------------
# Email SMTP Settings (Day 2 - Flask-Mail OTP)
# -----------------------------------------------------------------------------
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your_app_password')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'your_email@gmail.com')

# -----------------------------------------------------------------------------
# Razorpay Payment Gateway Keys (Day 12 & 13)
# -----------------------------------------------------------------------------
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')

# -----------------------------------------------------------------------------
# Upload Folders (Day 4: Products, Day 8: Admin Profiles, Customer User Profiles)
# -----------------------------------------------------------------------------
PRODUCT_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'products')
ADMIN_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'admin_profiles')
USER_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'user_profiles')

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


# -----------------------------------------------------------------------------
# UPI QR Code Payment Settings
# -----------------------------------------------------------------------------
UPI_ID = os.environ.get('UPI_ID', 'smartcart@upi')
UPI_PAYEE_NAME = os.environ.get('UPI_PAYEE_NAME', 'SmartCart Store')

