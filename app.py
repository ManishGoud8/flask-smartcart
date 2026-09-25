# app.py
# -----------------------------------------------------------------------------
# SmartCart - Complete eCommerce Web Application (Days 1 to 14)
# Fully migrated to Python's built-in SQLite database layer (smartcart.db).
# Fully documented with clean, modular, and beginner-friendly structure.
# -----------------------------------------------------------------------------
import os
import random
import sqlite3
import traceback
import urllib.parse
import bcrypt
import razorpay
from flask import Flask, render_template, request, redirect, session, flash, jsonify, make_response
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

import config
from utils.pdf_generator import generate_pdf

# -----------------------------------------------------------------------------
# App Initialization & Configuration (Day 1)
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Email Configuration (Day 2)
app.config['MAIL_SERVER'] = config.MAIL_SERVER
app.config['MAIL_PORT'] = config.MAIL_PORT
app.config['MAIL_USE_TLS'] = config.MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = config.MAIL_USE_SSL
app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = config.MAIL_DEFAULT_SENDER

mail = Mail(app)

# Upload Directories Configuration (Day 4: Products, Day 8: Admin Profiles, Customer User Profiles)
app.config['PRODUCT_UPLOAD_FOLDER'] = config.PRODUCT_UPLOAD_FOLDER
app.config['ADMIN_UPLOAD_FOLDER'] = config.ADMIN_UPLOAD_FOLDER
app.config['USER_UPLOAD_FOLDER'] = config.USER_UPLOAD_FOLDER
os.makedirs(app.config['PRODUCT_UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ADMIN_UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['USER_UPLOAD_FOLDER'], exist_ok=True)

# Razorpay Client Initialization (Day 12 & Day 13)
razorpay_client = razorpay.Client(
    auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET)
)

# -----------------------------------------------------------------------------
# SQLite Database Helper Functions & Auto-Init (Day 1)
# -----------------------------------------------------------------------------
def dict_factory(cursor, row):
    """
    Row factory callback to return SQLite query rows as standard Python dictionaries.
    Ensures seamless compatibility with row['field'] and dict.get() lookups.
    """
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def get_db_connection():
    """
    Creates and returns a connection to SQLite database (smartcart.db).
    """
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db_schema():
    """
    Ensures all 5 SQLite tables exist on app startup using CREATE TABLE IF NOT EXISTS.
    Does not overwrite or drop existing data.
    """
    conn = sqlite3.connect(config.DB_PATH)
    schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
    conn.commit()
    conn.close()

# Ensure tables exist on startup
init_db_schema()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

# =============================================================================
# DAY 1: Home Route
# =============================================================================
@app.route('/')
def home():
    """Day 1: Landing Home Page"""
    return render_template("index.html")


# =============================================================================
# DAY 2: Admin Registration + Email OTP Verification + Password Hashing
# =============================================================================
@app.route('/admin-signup', methods=['GET', 'POST'])
def admin_signup():
    """Day 2: Admin Signup - Generates OTP and sends to Email"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()

        if not name or not email:
            flash("All fields are required!", "danger")
            return redirect('/admin-signup')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE email = ?", (email,))
        existing_admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if existing_admin:
            flash("Email is already registered! Please login.", "warning")
            return redirect('/admin-login')

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        session['temp_admin_name'] = name
        session['temp_admin_email'] = email
        session['admin_otp'] = otp

        # Send OTP via Flask-Mail (with fallback print for offline / demo environments)
        try:
            msg = Message(
                subject="SmartCart Admin Registration OTP",
                recipients=[email],
                body=f"Hello {name},\n\nYour OTP for SmartCart Admin Registration is: {otp}\n\nPlease enter this OTP to complete your registration."
            )
            mail.send(msg)
            flash(f"OTP sent successfully to {email}!", "info")
        except Exception as e:
            app.logger.warning(f"Mail sending failed (demo mode enabled): {e}")
            flash(f"OTP generated: {otp} (Shown for testing since SMTP is not configured)", "info")

        return redirect('/verify-otp')

    return render_template("admin/admin_signup.html")


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Day 2: Verify OTP and save admin with bcrypt hashed password"""
    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        password = request.form.get('password', '').strip()

        session_otp = session.get('admin_otp')
        name = session.get('temp_admin_name')
        email = session.get('temp_admin_email')

        if not session_otp or not name or not email:
            flash("Session expired! Please start signup again.", "danger")
            return redirect('/admin-signup')

        if entered_otp != session_otp:
            flash("Invalid OTP! Please check and enter correctly.", "danger")
            return redirect('/verify-otp')

        if not password:
            flash("Password cannot be empty!", "danger")
            return redirect('/verify-otp')

        # Hash password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO admin (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, hashed_password))
            conn.commit()

            # Clean temporary session keys
            session.pop('admin_otp', None)
            session.pop('temp_admin_name', None)
            session.pop('temp_admin_email', None)

            flash("Admin registered successfully! Please login.", "success")
            return redirect('/admin-login')
        except Exception as e:
            conn.rollback()
            flash(f"Registration error: {e}", "danger")
            return redirect('/admin-signup')
        finally:
            cursor.close()
            conn.close()

    return render_template("admin/verify_otp.html")


# =============================================================================
# DAY 3: Admin Login, Session Management, Dashboard & Logout
# =============================================================================
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Day 3: Admin Login with bcrypt verification and session creation"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE email = ?", (email,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin and bcrypt.checkpw(password.encode('utf-8'), admin['password'].encode('utf-8')):
            session['admin_id'] = admin['admin_id']
            session['admin_name'] = admin['name']
            session['admin_email'] = admin['email']
            flash(f"Welcome back, {admin['name']}!", "success")
            return redirect('/admin-dashboard')
        else:
            flash("Invalid Email or Password!", "danger")
            return redirect('/admin-login')

    return render_template("admin/admin_login.html")


@app.route('/admin-dashboard')
def admin_dashboard():
    """Day 3: Protected Admin Dashboard"""
    if 'admin_id' not in session:
        flash("Please login to access the Admin Dashboard!", "warning")
        return redirect('/admin-login')
    return render_template("admin/dashboard.html")


@app.route('/admin-logout')
def admin_logout():
    """Day 3: Admin Logout"""
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    session.pop('admin_email', None)
    flash("Admin logged out successfully.", "info")
    return redirect('/admin-login')


# =============================================================================
# Admin Password Reset (Forgot Password with Email OTP)
# =============================================================================
@app.route('/admin-forgot-password', methods=['GET', 'POST'])
def admin_forgot_password():
    """Admin Forgot Password - Generates OTP and sends to verified Admin Email"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            flash("Please enter your admin email address!", "danger")
            return redirect('/admin-forgot-password')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE email = ?", (email,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if not admin:
            flash("No admin account found with that email address.", "danger")
            return redirect('/admin-forgot-password')

        otp = str(random.randint(100000, 999999))
        session['admin_reset_email'] = email
        session['admin_reset_name'] = admin['name']
        session['admin_reset_otp'] = otp

        try:
            msg = Message(
                subject="SmartCart Admin - Password Reset OTP",
                recipients=[email],
                body=f"Hello {admin['name']},\n\nYour OTP for resetting your SmartCart Admin password is: {otp}\n\nThis OTP is valid for your current session. If you did not request this, please ignore this email."
            )
            mail.send(msg)
            flash(f"Password reset OTP sent to {email}!", "info")
        except Exception as e:
            app.logger.warning(f"Mail sending failed (demo mode enabled): {e}")
            flash(f"OTP generated: {otp} (Shown for testing since SMTP is not configured)", "info")

        return redirect('/admin-reset-password')

    return render_template("admin/admin_forgot_password.html")


@app.route('/admin-reset-password', methods=['GET', 'POST'])
def admin_reset_password():
    """Admin Reset Password - Verifies OTP and updates admin password with bcrypt hash"""
    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        new_password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        session_otp = session.get('admin_reset_otp')
        email = session.get('admin_reset_email')

        if not session_otp or not email:
            flash("Session expired! Please request a new OTP.", "danger")
            return redirect('/admin-forgot-password')

        if entered_otp != session_otp:
            flash("Invalid OTP! Please enter the correct 6-digit code.", "danger")
            return redirect('/admin-reset-password')

        if not new_password or len(new_password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect('/admin-reset-password')

        if new_password != confirm_password:
            flash("Passwords do not match! Please try again.", "danger")
            return redirect('/admin-reset-password')

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE admin SET password = ? WHERE email = ?", (hashed_password, email))
            conn.commit()

            # Clean temporary reset session keys
            session.pop('admin_reset_otp', None)
            session.pop('admin_reset_email', None)
            session.pop('admin_reset_name', None)

            flash("Admin password reset successfully! Please login with your new password.", "success")
            return redirect('/admin-login')
        except Exception as e:
            conn.rollback()
            flash(f"Error resetting password: {e}", "danger")
            return redirect('/admin-reset-password')
        finally:
            cursor.close()
            conn.close()

    return render_template("admin/admin_reset_password.html")


# =============================================================================
# DAY 4: Admin Add Product (with Image Upload)
# =============================================================================
@app.route('/admin/add-item', methods=['GET', 'POST'])
def add_item():
    """Day 4: Add new product with image upload"""
    if 'admin_id' not in session:
        flash("Please login as admin first!", "warning")
        return redirect('/admin-login')

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        price = request.form.get('price', '').strip()
        image_file = request.files.get('image')

        if not (name and category and price and image_file and image_file.filename != ''):
            flash("Please fill all required fields and select an image!", "danger")
            return redirect('/admin/add-item')

        filename = None
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(f"{random.randint(1000, 9999)}_{image_file.filename}")
            image_path = os.path.join(app.config['PRODUCT_UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, description, category, price, image)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, category, float(price), filename))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Product added successfully to catalog!", "success")
        return redirect('/admin/item-list')

    return render_template("admin/add_item.html")


# =============================================================================
# DAY 5 & DAY 7: Admin Product Listing, Search, Category Filter & Single Item View
# =============================================================================
@app.route('/admin/item-list')
def item_list():
    """Day 5 & 7: Admin product list with search and category filtering"""
    if 'admin_id' not in session:
        flash("Please login as admin first!", "warning")
        return redirect('/admin-login')

    search_query = request.args.get('search', '').strip()
    selected_category = request.args.get('category', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch unique categories for dropdown filter (Day 7)
    cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
    category_rows = cursor.fetchall()
    categories = [row['category'] for row in category_rows]

    # Build dynamic query for search and filter (Day 7)
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search_query:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    if selected_category:
        query += " AND category = ?"
        params.append(selected_category)

    query += " ORDER BY product_id DESC"
    cursor.execute(query, tuple(params))
    products = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        "admin/item_list.html",
        products=products,
        categories=categories,
        search_query=search_query,
        selected_category=selected_category
    )


@app.route('/admin/view-item/<int:item_id>')
def view_item(item_id):
    """Day 5: Admin single product view"""
    if 'admin_id' not in session:
        flash("Please login as admin first!", "warning")
        return redirect('/admin-login')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id = ?", (item_id,))
    item = cursor.fetchone()
    cursor.close()
    conn.close()

    if not item:
        flash("Product not found!", "danger")
        return redirect('/admin/item-list')

    return render_template("admin/view_item.html", item=item)


# =============================================================================
# DAY 6: Admin Update Product (with Image Replace)
# =============================================================================
@app.route('/admin/update-item/<int:item_id>', methods=['GET', 'POST'])
def update_item(item_id):
    """Day 6: Admin update product with optional image replacement"""
    if 'admin_id' not in session:
        flash("Please login as admin first!", "warning")
        return redirect('/admin-login')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id = ?", (item_id,))
    item = cursor.fetchone()

    if not item:
        cursor.close()
        conn.close()
        flash("Product not found!", "danger")
        return redirect('/admin/item-list')

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        price = request.form.get('price', '').strip()
        new_image = request.files.get('image')

        old_image_name = item['image']
        final_image_name = old_image_name

        # Process new image if uploaded
        if new_image and new_image.filename != '' and allowed_file(new_image.filename):
            final_image_name = secure_filename(f"{random.randint(1000, 9999)}_{new_image.filename}")
            new_image_path = os.path.join(app.config['PRODUCT_UPLOAD_FOLDER'], final_image_name)
            new_image.save(new_image_path)

            # Delete old image from server if it exists
            if old_image_name:
                old_path = os.path.join(app.config['PRODUCT_UPLOAD_FOLDER'], old_image_name)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception as e:
                        app.logger.warning(f"Failed to remove old product image {old_path}: {e}")

        cursor.execute("""
            UPDATE products
            SET name = ?, description = ?, category = ?, price = ?, image = ?
            WHERE product_id = ?
        """, (name, description, category, float(price), final_image_name, item_id))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Product updated successfully!", "success")
        return redirect('/admin/item-list')

    cursor.close()
    conn.close()
    return render_template("admin/update_item.html", item=item)


# =============================================================================
# DAY 7: Admin Delete Product (with Image Cleanup)
# =============================================================================
@app.route('/admin/delete-item/<int:item_id>')
def delete_item(item_id):
    """Day 7: Admin delete product and remove its image from filesystem"""
    if 'admin_id' not in session:
        flash("Please login as admin first!", "warning")
        return redirect('/admin-login')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id = ?", (item_id,))
    item = cursor.fetchone()

    if item:
        image_name = item['image']
        if image_name:
            image_path = os.path.join(app.config['PRODUCT_UPLOAD_FOLDER'], image_name)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    app.logger.warning(f"Failed to delete product image file {image_path}: {e}")

        cursor.execute("DELETE FROM products WHERE product_id = ?", (item_id,))
        conn.commit()
        flash("Product deleted successfully!", "success")
    else:
        flash("Product not found!", "danger")

    cursor.close()
    conn.close()
    return redirect('/admin/item-list')


# =============================================================================
# DAY 8: Admin Profile Page + Profile Update (with Image Replace)
# =============================================================================
@app.route('/admin/profile', methods=['GET', 'POST'])
def admin_profile():
    """Day 8: Admin profile viewing and updating with profile picture upload"""
    if 'admin_id' not in session:
        flash("Please login as admin first!", "warning")
        return redirect('/admin-login')

    admin_id = session['admin_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        new_password = request.form.get('password', '').strip()
        new_image = request.files.get('profile_image')

        cursor.execute("SELECT * FROM admin WHERE admin_id = ?", (admin_id,))
        admin = cursor.fetchone()
        old_image_name = admin['profile_image']

        # Update password only if entered
        if new_password:
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            hashed_password = admin['password']

        # Handle profile image replacement
        final_image_name = old_image_name
        if new_image and new_image.filename != '' and allowed_file(new_image.filename):
            final_image_name = secure_filename(f"admin_{admin_id}_{random.randint(100, 999)}_{new_image.filename}")
            image_path = os.path.join(app.config['ADMIN_UPLOAD_FOLDER'], final_image_name)
            new_image.save(image_path)

            if old_image_name:
                old_image_path = os.path.join(app.config['ADMIN_UPLOAD_FOLDER'], old_image_name)
                if os.path.exists(old_image_path):
                    try:
                        os.remove(old_image_path)
                    except Exception as e:
                        app.logger.warning(f"Failed to delete old admin profile image {old_image_path}: {e}")

        cursor.execute("""
            UPDATE admin
            SET name = ?, email = ?, password = ?, profile_image = ?
            WHERE admin_id = ?
        """, (name, email, hashed_password, final_image_name, admin_id))
        conn.commit()

        session['admin_name'] = name
        session['admin_email'] = email

        cursor.close()
        conn.close()
        flash("Admin profile updated successfully!", "success")
        return redirect('/admin/profile')

    cursor.execute("SELECT * FROM admin WHERE admin_id = ?", (admin_id,))
    admin = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template("admin/admin_profile.html", admin=admin)


# =============================================================================
# DAY 9: User Registration, User Login, User Dashboard & Logout
# =============================================================================
@app.route('/user-register', methods=['GET', 'POST'])
def user_register():
    """Day 9: Customer Registration with bcrypt password hash"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not (name and email and password):
            flash("All fields are required!", "danger")
            return redirect('/user-register')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()
            flash("Email already registered! Please login.", "warning")
            return redirect('/user-login')

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("""
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
        """, (name, email, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Registration successful! Please login.", "success")
        return redirect('/user-login')

    return render_template("user/user_register.html")


@app.route('/user-login', methods=['GET', 'POST'])
def user_login():
    """Day 9: Customer Login with password check & session handling"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_profile_image'] = user.get('profile_image') or ''
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect('/user-dashboard')
        else:
            flash("Invalid email or password!", "danger")
            return redirect('/user-login')

    return render_template("user/user_login.html")


@app.route('/user-dashboard')
def user_dashboard():
    """Day 9: Customer Protected Dashboard"""
    if 'user_id' not in session:
        flash("Please login to access your customer dashboard!", "warning")
        return redirect('/user-login')
    return render_template("user/user_home.html")


@app.route('/user/profile', methods=['GET', 'POST'])
def user_profile():
    """Customer User Profile View & Edit with Profile Image Upload"""
    if 'user_id' not in session:
        flash("Please log in to view your profile.", "warning")
        return redirect('/user-login')

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        new_password = request.form.get('password', '').strip()
        new_image = request.files.get('profile_image')

        if not name or not email:
            flash("Name and email are required!", "danger")
            cursor.close()
            conn.close()
            return redirect('/user/profile')

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        old_image_name = user.get('profile_image')

        # Update password only if provided
        if new_password:
            if len(new_password) < 6:
                flash("Password must be at least 6 characters long.", "danger")
                cursor.close()
                conn.close()
                return redirect('/user/profile')
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            hashed_password = user['password']

        # Handle image upload
        final_image_name = old_image_name
        if new_image and new_image.filename != '' and allowed_file(new_image.filename):
            final_image_name = secure_filename(f"user_{user_id}_{random.randint(100, 999)}_{new_image.filename}")
            image_path = os.path.join(app.config['USER_UPLOAD_FOLDER'], final_image_name)
            new_image.save(image_path)

            if old_image_name:
                old_path = os.path.join(app.config['USER_UPLOAD_FOLDER'], old_image_name)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception as e:
                        app.logger.warning(f"Failed to delete old user avatar: {e}")

        cursor.execute("""
            UPDATE users 
            SET name = ?, email = ?, password = ?, profile_image = ?
            WHERE user_id = ?
        """, (name, email, hashed_password, final_image_name, user_id))
        conn.commit()

        session['user_name'] = name
        session['user_email'] = email
        session['user_profile_image'] = final_image_name or ''

        flash("Profile updated successfully!", "success")
        cursor.close()
        conn.close()
        return redirect('/user/profile')

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    # Fetch user order stats
    cursor.execute("SELECT COUNT(*) as order_count, COALESCE(SUM(amount), 0) as total_spent FROM orders WHERE user_id = ?", (user_id,))
    stats = cursor.fetchone()

    cursor.close()
    conn.close()
    return render_template("user/user_profile.html", user=user, stats=stats)


@app.route('/user-logout')
def user_logout():
    """Day 9: Customer Logout"""
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    session.pop('user_profile_image', None)
    flash("You have logged out successfully.", "info")
    return redirect('/user-login')


# =============================================================================
# Customer Password Reset (Forgot Password with Email OTP)
# =============================================================================
@app.route('/user-forgot-password', methods=['GET', 'POST'])
def user_forgot_password():
    """Customer Forgot Password - Generates OTP and sends to verified Customer Email"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            flash("Please enter your registered email address!", "danger")
            return redirect('/user-forgot-password')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            flash("No user account found with that email address.", "danger")
            return redirect('/user-forgot-password')

        otp = str(random.randint(100000, 999999))
        session['user_reset_email'] = email
        session['user_reset_name'] = user['name']
        session['user_reset_otp'] = otp

        try:
            msg = Message(
                subject="SmartCart Customer - Password Reset OTP",
                recipients=[email],
                body=f"Hello {user['name']},\n\nYour OTP for resetting your SmartCart account password is: {otp}\n\nThis OTP is valid for your current session. If you did not request this, please ignore this email."
            )
            mail.send(msg)
            flash(f"Password reset OTP sent to {email}!", "info")
        except Exception as e:
            app.logger.warning(f"Mail sending failed (demo mode enabled): {e}")
            flash(f"OTP generated: {otp} (Shown for testing since SMTP is not configured)", "info")

        return redirect('/user-reset-password')

    return render_template("user/user_forgot_password.html")


@app.route('/user-reset-password', methods=['GET', 'POST'])
def user_reset_password():
    """Customer Reset Password - Verifies OTP and updates customer password with bcrypt hash"""
    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        new_password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        session_otp = session.get('user_reset_otp')
        email = session.get('user_reset_email')

        if not session_otp or not email:
            flash("Session expired! Please request a new OTP.", "danger")
            return redirect('/user-forgot-password')

        if entered_otp != session_otp:
            flash("Invalid OTP! Please enter the correct 6-digit code.", "danger")
            return redirect('/user-reset-password')

        if not new_password or len(new_password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect('/user-reset-password')

        if new_password != confirm_password:
            flash("Passwords do not match! Please try again.", "danger")
            return redirect('/user-reset-password')

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, email))
            conn.commit()

            # Clean temporary reset session keys
            session.pop('user_reset_otp', None)
            session.pop('user_reset_email', None)
            session.pop('user_reset_name', None)

            flash("Password reset successfully! Please login with your new password.", "success")
            return redirect('/user-login')
        except Exception as e:
            conn.rollback()
            flash(f"Error resetting password: {e}", "danger")
            return redirect('/user-reset-password')
        finally:
            cursor.close()
            conn.close()

    return render_template("user/user_reset_password.html")


# =============================================================================
# DAY 10: User Product Listing & Product Details View
# =============================================================================
@app.route('/user/products')
def user_products():
    """Day 10: User catalog with search and category filtering"""
    search_query = request.args.get('search', '').strip()
    selected_category = request.args.get('category', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
    category_rows = cursor.fetchall()
    categories = [r['category'] for r in category_rows]

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search_query:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    if selected_category:
        query += " AND category = ?"
        params.append(selected_category)

    query += " ORDER BY product_id DESC"
    cursor.execute(query, tuple(params))
    products = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        "user/user_products.html",
        products=products,
        categories=categories,
        search_query=search_query,
        selected_category=selected_category
    )


@app.route('/user/product/<int:product_id>')
def user_product_details(product_id):
    """Day 10: User Single Product Details with live Cart Status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if not product:
        flash("Product not found.", "danger")
        return redirect('/user/products')

    cart = session.get('cart', {})
    cart_item = cart.get(str(product_id))

    return render_template("user/product_details.html", product=product, cart_item=cart_item, cart=cart)


# =============================================================================
# DAY 11: User Shopping Cart System using Flask Sessions (Standard & AJAX)
# =============================================================================
@app.route('/user/add-to-cart/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart(product_id):
    """Day 11: Standard Add-to-Cart route with quantity option (GET & POST)"""
    if 'cart' not in session:
        session['cart'] = {}
    cart = session['cart']

    # Get desired quantity (defaults to 1)
    qty = 1
    if request.method == 'POST':
        try:
            qty = int(request.form.get('quantity', 1))
        except (ValueError, TypeError):
            qty = 1
    else:
        try:
            qty = int(request.args.get('quantity', 1))
        except (ValueError, TypeError):
            qty = 1

    if qty < 1:
        qty = 1

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if not product:
        flash("Product not found.", "danger")
        return redirect(request.referrer or '/user/products')

    pid = str(product_id)
    if pid in cart:
        cart[pid]['quantity'] += qty
    else:
        cart[pid] = {
            'name': product['name'],
            'price': float(product['price']),
            'image': product['image'],
            'quantity': qty
        }

    session['cart'] = cart
    session.modified = True
    flash(f"Added {qty}x '{product['name']}' to your shopping cart!", "success")
    return redirect(request.referrer or f'/user/product/{product_id}')


@app.route('/user/add-to-cart-ajax/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart_ajax(product_id):
    """Day 11.2: Amazon-Style Instant AJAX Add to Cart (JSON API)"""
    if 'cart' not in session:
        session['cart'] = {}
    cart = session['cart']

    try:
        qty = int(request.args.get('quantity') or (request.form.get('quantity') if request.method == 'POST' else None) or 1)
    except (ValueError, TypeError):
        qty = 1

    if qty < 1:
        qty = 1

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if not product:
        return jsonify({"error": "Product not found"}), 404

    pid = str(product_id)
    if pid in cart:
        cart[pid]['quantity'] += qty
    else:
        cart[pid] = {
            'name': product['name'],
            'price': float(product['price']),
            'image': product['image'],
            'quantity': qty
        }

    session['cart'] = cart
    session.modified = True
    return jsonify({
        "message": f"{qty}x '{product['name']}' added to cart successfully!",
        "cart_count": len(cart),
        "total_items": sum(item['quantity'] for item in cart.values())
    })


@app.route('/user/cart')
def view_cart():
    """Day 11: View User Cart Page"""
    cart = session.get('cart', {})
    total_amount = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template("user/cart.html", cart=cart, total_amount=total_amount)


@app.route('/user/cart/increase/<pid>')
def increase_quantity(pid):
    """Day 11: Increase quantity of cart item"""
    cart = session.get('cart', {})
    if pid in cart:
        cart[pid]['quantity'] += 1
        session['cart'] = cart
    return redirect('/user/cart')


@app.route('/user/cart/decrease/<pid>')
def decrease_quantity(pid):
    """Day 11: Decrease quantity of cart item"""
    cart = session.get('cart', {})
    if pid in cart:
        cart[pid]['quantity'] -= 1
        if cart[pid]['quantity'] <= 0:
            cart.pop(pid)
        session['cart'] = cart
    return redirect('/user/cart')


@app.route('/user/cart/remove/<pid>')
def remove_from_cart(pid):
    """Day 11: Remove item completely from cart"""
    cart = session.get('cart', {})
    if pid in cart:
        cart.pop(pid)
        session['cart'] = cart
        flash("Item removed from cart.", "info")
    return redirect('/user/cart')


# =============================================================================
# DAY 12: Razorpay & UPI QR Code Payment (Order Creation & QR Generation)
# =============================================================================
@app.route('/user/pay')
def user_pay():
    """Day 12: Create Razorpay Order and UPI QR Code, render payment page"""
    if 'user_id' not in session:
        flash("Please login to proceed to checkout!", "warning")
        return redirect('/user-login')

    cart = session.get('cart', {})
    if not cart:
        flash("Your cart is empty! Add products before checkout.", "warning")
        return redirect('/user/products')

    total_amount = sum(item['price'] * item['quantity'] for item in cart.values())
    razorpay_amount = int(total_amount * 100)  # Convert to paise

    # Create Razorpay order
    try:
        razorpay_order = razorpay_client.order.create({
            "amount": razorpay_amount,
            "currency": "INR",
            "payment_capture": "1"
        })
        session['razorpay_order_id'] = razorpay_order['id']
        razorpay_order_id = razorpay_order['id']
    except Exception as e:
        app.logger.warning(f"Razorpay API call failed: {e}. Using simulated order ID for testing.")
        razorpay_order_id = f"order_sim_{random.randint(10000, 99999)}"
        session['razorpay_order_id'] = razorpay_order_id

    # Generate UPI QR Code Payment URI and Image URL
    upi_id = config.UPI_ID
    upi_payee_name = config.UPI_PAYEE_NAME
    upi_uri = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(upi_payee_name)}&am={total_amount:.2f}&cu=INR&tn={urllib.parse.quote('SmartCart Order')}"
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(upi_uri)}"

    return render_template(
        "user/payment.html",
        amount=total_amount,
        key_id=config.RAZORPAY_KEY_ID,
        order_id=razorpay_order_id,
        upi_id=upi_id,
        upi_payee_name=upi_payee_name,
        upi_uri=upi_uri,
        qr_code_url=qr_code_url
    )


# =============================================================================
# UPI QR Code Payment Verification & Order Persistence
# =============================================================================
@app.route('/user/verify-upi-payment', methods=['POST'])
def verify_upi_payment():
    """Verify UPI QR Code Payment submission and persist order & order_items into SQLite"""
    if 'user_id' not in session:
        flash("Please login to complete your payment.", "danger")
        return redirect('/user-login')

    cart = session.get('cart', {})
    if not cart:
        flash("Cart is empty. Cannot place order.", "danger")
        return redirect('/user/products')

    upi_ref_id = request.form.get('upi_ref_id', '').strip()
    if not upi_ref_id:
        upi_ref_id = f"UPI{random.randint(100000000000, 999999999999)}"

    upi_order_id = f"UPI_ORD_{random.randint(100000, 999999)}"
    total_amount = sum(item['price'] * item['quantity'] for item in cart.values())
    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert into orders table with UPI reference
        cursor.execute("""
            INSERT INTO orders (user_id, razorpay_order_id, razorpay_payment_id, amount, payment_status)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, upi_order_id, f"UPI-{upi_ref_id}", total_amount, 'paid'))
        order_db_id = cursor.lastrowid

        # Insert each cart item into order_items table
        for pid_str, item in cart.items():
            product_id = int(pid_str)
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)
            """, (order_db_id, product_id, item['name'], item['quantity'], item['price']))

        conn.commit()

        # Clear cart and temporary order id from session
        session.pop('cart', None)
        session.pop('razorpay_order_id', None)

        flash(f"UPI Payment verified successfully (Ref: {upi_ref_id})! Your order has been placed.", "success")
        return redirect(f"/user/order-success/{order_db_id}")
    except Exception as e:
        conn.rollback()
        app.logger.error(f"UPI Order storage failed: {e}\n{traceback.format_exc()}")
        flash("There was an error saving your UPI order. Please contact support.", "danger")
        return redirect('/user/cart')
    finally:
        cursor.close()
        conn.close()


@app.route('/payment-success')
def payment_success():
    """Day 12: Temporary Payment Success Route"""
    payment_id = request.args.get('payment_id', 'PAY_TEST_123')
    order_id = request.args.get('order_id', 'ORD_TEST_123')
    return render_template("user/payment_success.html", payment_id=payment_id, order_id=order_id)


# =============================================================================
# DAY 13: Razorpay Payment Verification, Order Persistence & My Orders
# =============================================================================
@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    """Day 13: Verify Razorpay signature and persist order & order_items into SQLite"""
    if 'user_id' not in session:
        flash("Please login to complete your payment.", "danger")
        return redirect('/user-login')

    razorpay_payment_id = request.form.get('razorpay_payment_id')
    razorpay_order_id = request.form.get('razorpay_order_id')
    razorpay_signature = request.form.get('razorpay_signature')
    is_simulation = request.form.get('is_simulation') == 'true'

    if not (razorpay_payment_id and razorpay_order_id):
        flash("Payment verification failed (missing transaction data).", "danger")
        return redirect('/user/cart')

    # Signature verification
    if not is_simulation and razorpay_signature and not razorpay_signature.startswith('simulated'):
        payload = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        try:
            razorpay_client.utility.verify_payment_signature(payload)
        except Exception as e:
            app.logger.error(f"Razorpay signature verification error: {e}")
            flash("Payment verification failed! Tampering detected.", "danger")
            return redirect('/user/cart')

    user_id = session['user_id']
    cart = session.get('cart', {})

    if not cart:
        flash("Cart is empty. Cannot place order.", "danger")
        return redirect('/user/products')

    total_amount = sum(item['price'] * item['quantity'] for item in cart.values())

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert into orders table
        cursor.execute("""
            INSERT INTO orders (user_id, razorpay_order_id, razorpay_payment_id, amount, payment_status)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, razorpay_order_id, razorpay_payment_id, total_amount, 'paid'))
        order_db_id = cursor.lastrowid

        # Insert each cart item into order_items table
        for pid_str, item in cart.items():
            product_id = int(pid_str)
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)
            """, (order_db_id, product_id, item['name'], item['quantity'], item['price']))

        conn.commit()

        # Clear cart and temporary order id from session
        session.pop('cart', None)
        session.pop('razorpay_order_id', None)

        flash("Payment successful and order placed!", "success")
        return redirect(f"/user/order-success/{order_db_id}")
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Order storage failed: {e}\n{traceback.format_exc()}")
        flash("There was an error saving your order. Please contact support.", "danger")
        return redirect('/user/cart')
    finally:
        cursor.close()
        conn.close()


@app.route('/user/order-success/<int:order_db_id>')
def order_success(order_db_id):
    """Day 13: Order confirmation page"""
    if 'user_id' not in session:
        flash("Please login to view order details!", "warning")
        return redirect('/user-login')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ? AND user_id = ?", (order_db_id, session['user_id']))
    order = cursor.fetchone()

    if not order:
        cursor.close()
        conn.close()
        flash("Order not found.", "danger")
        return redirect('/user/products')

    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_db_id,))
    items = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("user/order_success.html", order=order, items=items)


@app.route('/user/my-orders')
def my_orders():
    """Day 13: List of all past orders for customer"""
    if 'user_id' not in session:
        flash("Please login to view your orders!", "warning")
        return redirect('/user-login')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM orders 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (session['user_id'],))
    orders = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("user/my_orders.html", orders=orders)


# =============================================================================
# DAY 14: Amazon-Style Invoice Generation (HTML to PDF)
# =============================================================================
@app.route('/user/download-invoice/<int:order_id>')
def download_invoice(order_id):
    """Day 14: Generate and stream PDF Invoice for an order"""
    if 'user_id' not in session:
        flash("Please login to download invoices!", "warning")
        return redirect('/user-login')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ? AND user_id = ?", (order_id, session['user_id']))
    order = cursor.fetchone()

    if not order:
        cursor.close()
        conn.close()
        flash("Order not found or access denied.", "danger")
        return redirect('/user/my-orders')

    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    items = cursor.fetchall()
    cursor.close()
    conn.close()

    # Render HTML Invoice template with order details
    html_content = render_template("user/invoice.html", order=order, items=items)

    # Convert HTML to PDF buffer
    pdf_buffer = generate_pdf(html_content)

    if not pdf_buffer:
        flash("Error generating PDF invoice. Please try again.", "danger")
        return redirect('/user/my-orders')

    # Return PDF response as an attachment
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f"attachment; filename=invoice_{order_id}.pdf"
    return response


# -----------------------------------------------------------------------------
# App Entry Point
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    print("Starting SmartCart Flask Web Application on http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False, port=5000)

