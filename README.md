# SmartCart Flask eCommerce Project (Day 1 to Day 14)

SmartCart is a full-featured eCommerce web application built with Flask, MySQL, and pure raw HTML (no CSS) following the Day 1 to Day 14 curriculum.

---

## 🚀 Features

- **Day 1**: Flask setup, MySQL connection helper (`get_db_connection`), configuration (`config.py`).
- **Day 2**: Admin registration with Email OTP generation & verification (Flask-Mail) + bcrypt password hashing.
- **Day 3**: Admin login, session authentication, protected dashboard, and logout.
- **Day 4**: Admin Add Product with image upload to `static/uploads/products/`.
- **Day 5**: Admin Product Listing and Single Product View.
- **Day 6**: Admin Update Product with Image Replacement (and disk cleanup).
- **Day 7**: Admin Delete Product (with disk image cleanup) + Search & Category Filtering.
- **Day 8**: Admin Profile Management (Name, Email, Password, and Profile Photo upload to `static/uploads/admin_profiles/`).
- **Day 9**: Customer Registration, Login, Protected Dashboard & Session Management.
- **Day 10**: Customer Product Catalog Browsing with Search/Filter & Single Product Details.
- **Day 11 (11.1 & 11.2)**: User Cart System (Standard & Amazon-style AJAX Add to Cart, Increment, Decrement, Remove item).
- **Day 12**: Razorpay Payment Gateway & **Easy Pay via Dynamic UPI QR Code** (Scan & Pay with Google Pay, PhonePe, Paytm, BHIM).
- **Day 13**: Payment Verification & Persistence (Razorpay Signature & UPI UTR reference verification, atomic order & items database persistence, order confirmation & My Orders).
- **Day 14**: Amazon-style PDF Invoice Generation using `xhtml2pdf` (`/user/download-invoice/<order_id>`).

---

## 🗄️ Database Setup

Database: SQLite (`smartcart.db`)  
SQLite requires zero manual installation and runs out-of-the-box with Python's built-in `sqlite3` module.

The application automatically creates all necessary tables on startup if `smartcart.db` does not exist.

To initialize, seed, or migrate from MySQL:
```bash
# Initialize schema
python database/init_db.py

# Seed sample items
python database/seed.py

# (Optional) Migrate existing MySQL data into SQLite
python migrate_mysql_to_sqlite.py
```

---

## 🏃‍♂️ How to Run

1. **Start the Flask Application**:
   ```bash
   python app.py
   ```

2. **Open in Browser**:
   ```
   http://127.0.0.1:5000
   ```

3. **Pre-configured Logins**:
   - **Admin Login**: `admin@smartcart.com` | Password: `admin123`
   - **Customer Login**: `user@smartcart.com` | Password: `user123`

---

## 🧪 Run Automated Tests

To test all 14 days of functionality end-to-end:
```bash
python test_smartcart.py
```
