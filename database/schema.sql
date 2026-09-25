-- ===================================================================
-- SmartCart Complete SQLite Database Schema (Days 1 to 14)
-- Database: smartcart.db
-- ===================================================================

PRAGMA foreign_keys = ON;

-- -------------------------------------------------------------------
-- 1. Admin Table 
-- Stores admin accounts, credentials, and profile image path
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admin (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    profile_image TEXT DEFAULT NULL
);

-- -------------------------------------------------------------------
-- 2. Products Table 
-- Stores product catalog details and uploaded product image name
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    price REAL NOT NULL,
    image TEXT
);

-- -------------------------------------------------------------------
-- 3. Users Table (Day 9)
-- Stores customer accounts and hashed passwords
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    profile_image TEXT DEFAULT NULL
);

-- -------------------------------------------------------------------
-- 4. Orders Table (Day 13)
-- Stores placed orders, Razorpay/UPI transaction IDs and payment status
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    razorpay_order_id TEXT,
    razorpay_payment_id TEXT,
    amount REAL NOT NULL,
    payment_status TEXT DEFAULT 'paid',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------------
-- 5. Order Items Table (Day 13)
-- Stores individual product line items per order
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);
