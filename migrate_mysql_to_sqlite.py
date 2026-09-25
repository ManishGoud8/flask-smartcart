"""
migrate_mysql_to_sqlite.py
-----------------------------------------------------------------------------
Automated Data Migration Script from MySQL to SQLite for SmartCart.
Reads data from MySQL (smartcart_db / smartcard_db) and transfers all 5 tables
(admin, products, users, orders, order_items) into smartcart.db with proper
type conversions (Decimal -> float, DATETIME strings) while preserving IDs.
Prevents duplication on multiple runs using INSERT OR REPLACE.
-----------------------------------------------------------------------------
"""
import os
import sys
import sqlite3
from decimal import Decimal
import datetime

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import project configuration
import config
from database.init_db import initialize_database

def convert_val(val):
    """Converts MySQL-specific types to SQLite-compatible Python types."""
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.strftime('%Y-%m-%d %H:%M:%S')
    return val

def migrate_data():
    print("=" * 65)
    print("🚀 SmartCart MySQL to SQLite Database Migration")
    print("=" * 65)

    # 1. Ensure SQLite schema exists
    initialize_database()

    # 2. Connect to MySQL
    mysql_conn = None
    try:
        import mysql.connector
        
        # Try both smartcart_db and smartcard_db
        db_candidates = ['smartcart_db', 'smartcard_db']
        for db in db_candidates:
            try:
                mysql_conn = mysql.connector.connect(
                    host='localhost',
                    user='root',
                    password='Mani@2004',
                    database=db
                )
                print(f"✓ Connected to MySQL database '{db}'.")
                break
            except Exception:
                continue

        if not mysql_conn:
            print("❌ Could not connect to MySQL server. Please check credentials.")
            return False

    except ImportError:
        print("⚠️ mysql-connector-python not installed. Skipping live MySQL fetch.")
        return False
    except Exception as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return False

    mysql_cursor = mysql_conn.cursor(dictionary=True)
    sqlite_conn = sqlite3.connect(config.DB_PATH)
    sqlite_conn.execute("PRAGMA foreign_keys = OFF;")  # temporarily off during bulk insertion
    sqlite_cursor = sqlite_conn.cursor()

    try:
        # Check available tables in MySQL
        mysql_cursor.execute("SHOW TABLES;")
        mysql_tables = [list(r.values())[0] for r in mysql_cursor.fetchall()]
        print(f"Found MySQL tables: {mysql_tables}\n")

        # --- A. Migrate admin / admin_sc table ---
        admin_tbl = 'admin' if 'admin' in mysql_tables else ('admin_sc' if 'admin_sc' in mysql_tables else None)
        if admin_tbl:
            mysql_cursor.execute(f"SELECT * FROM {admin_tbl}")
            admin_rows = mysql_cursor.fetchall()
            for r in admin_rows:
                admin_id = r.get('admin_id') or r.get('id')
                name = r.get('name') or r.get('anime') or 'Admin'
                email = r.get('email')
                password = r.get('password') or r.get('apassword')
                profile_image = r.get('profile_image')
                
                sqlite_cursor.execute("""
                    INSERT OR REPLACE INTO admin (admin_id, name, email, password, profile_image)
                    VALUES (?, ?, ?, ?, ?)
                """, (admin_id, name, email, password, profile_image))
            print(f"✓ Migrated {len(admin_rows)} admin records.")

        # --- B. Migrate users table ---
        if 'users' in mysql_tables:
            mysql_cursor.execute("SELECT * FROM users")
            user_rows = mysql_cursor.fetchall()
            for r in user_rows:
                user_id = r.get('user_id') or r.get('id')
                name = r.get('name')
                email = r.get('email')
                password = r.get('password')
                profile_image = r.get('profile_image')

                sqlite_cursor.execute("""
                    INSERT OR REPLACE INTO users (user_id, name, email, password, profile_image)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, name, email, password, profile_image))
            print(f"✓ Migrated {len(user_rows)} user records.")

        # --- C. Migrate products table ---
        if 'products' in mysql_tables:
            mysql_cursor.execute("SELECT * FROM products")
            prod_rows = mysql_cursor.fetchall()
            for r in prod_rows:
                product_id = r.get('product_id') or r.get('id')
                name = r.get('name')
                description = r.get('description')
                category = r.get('category')
                price = convert_val(r.get('price'))
                image = r.get('image')

                sqlite_cursor.execute("""
                    INSERT OR REPLACE INTO products (product_id, name, description, category, price, image)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (product_id, name, description, category, price, image))
            print(f"✓ Migrated {len(prod_rows)} product records.")

        # --- D. Migrate orders table ---
        if 'orders' in mysql_tables:
            mysql_cursor.execute("SELECT * FROM orders")
            order_rows = mysql_cursor.fetchall()
            for r in order_rows:
                order_id = r.get('order_id') or r.get('id')
                user_id = r.get('user_id')
                razorpay_order_id = r.get('razorpay_order_id')
                razorpay_payment_id = r.get('razorpay_payment_id') or r.get('payment_id')
                amount = convert_val(r.get('amount') or r.get('total_amount'))
                payment_status = r.get('payment_status') or r.get('status') or 'paid'
                created_at = convert_val(r.get('created_at'))

                sqlite_cursor.execute("""
                    INSERT OR REPLACE INTO orders (order_id, user_id, razorpay_order_id, razorpay_payment_id, amount, payment_status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (order_id, user_id, razorpay_order_id, razorpay_payment_id, amount, payment_status, created_at))
            print(f"✓ Migrated {len(order_rows)} order records.")

        # --- E. Migrate order_items table ---
        if 'order_items' in mysql_tables:
            mysql_cursor.execute("SELECT * FROM order_items")
            item_rows = mysql_cursor.fetchall()
            for r in item_rows:
                item_id = r.get('id')
                order_id = r.get('order_id')
                product_id = r.get('product_id')
                product_name = r.get('product_name')
                quantity = r.get('quantity', 1)
                price = convert_val(r.get('price') or r.get('product_price') or r.get('subtotal'))

                sqlite_cursor.execute("""
                    INSERT OR REPLACE INTO order_items (id, order_id, product_id, product_name, quantity, price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (item_id, order_id, product_id, product_name, quantity, price))
            print(f"✓ Migrated {len(item_rows)} order_items records.")

        sqlite_conn.commit()
        sqlite_conn.execute("PRAGMA foreign_keys = ON;")
        print("\n🎉 Migration committed successfully to smartcart.db!\n")

        # --- Verification Summary ---
        print("=" * 65)
        print("📊 SQLite Database Verification (smartcart.db)")
        print("=" * 65)
        for tbl in ['admin', 'products', 'users', 'orders', 'order_items']:
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
            count = sqlite_cursor.fetchone()[0]
            print(f"  Table '{tbl}': {count} total rows")
        print("=" * 65)

        return True

    except Exception as e:
        sqlite_conn.rollback()
        print(f"❌ Error during data migration: {e}")
        raise e
    finally:
        mysql_cursor.close()
        mysql_conn.close()
        sqlite_cursor.close()
        sqlite_conn.close()

if __name__ == '__main__':
    migrate_data()
