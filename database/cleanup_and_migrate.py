import sqlite3
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def run_cleanup():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    # 1. Add profile_image column to users table if not exists
    cursor.execute("PRAGMA table_info(users)")
    cols = [r['name'] for r in cursor.fetchall()]
    if 'profile_image' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_image TEXT DEFAULT NULL")
        print("[OK] Added profile_image column to users table.")
    else:
        print("[OK] profile_image column already present in users table.")

    # 2. Check and delete duplicate / test products
    cursor.execute("DELETE FROM products WHERE image LIKE '%test_headphone%' OR name LIKE '%test%'")
    print(f"[OK] Removed test/duplicate items: {cursor.rowcount} rows deleted.")

    # Standard 11 clean products
    standard_products = [
        ("Asus Performance Laptop", "Ultra-thin lightweight 15.6-inch laptop with crisp 4K OLED display, 16GB RAM and 512GB high-speed NVMe SSD", "Electronics", 59999.00, "asus_laptop.jpg"),
        ("Wireless Pro Studio Headphones", "Active noise-cancelling studio over-ear headphones with 40-hour battery life and deep bass", "Electronics", 2799.00, "headphones.jpg"),
        ("Mechanical Gaming Keyboard", "White backlit tactile mechanical keyboard with blue switches, aluminum frame, and detachable wrist rest", "Electronics", 3299.00, "mechanical_keyboard.jpg"),
        ("Wireless Precision Gaming Mouse", "Ergonomic 2.4GHz ultra-fast optical precision gaming mouse with matte finish and RGB accents", "Electronics", 1499.00, "gaming_mouse.jpg"),
        ("Cotton Casual Slim Fit Shirt", "Premium 100% breathable tailored cotton slim fit shirt in classic navy blue", "Fashion", 899.00, "cotton_shirt.jpg"),
        ("Urban Commuter Road Bicycle", "Lightweight aerodynamic matte black road bicycle with 21-speed gears and dual disc brakes", "Sports", 7999.00, "bicycle.jpg"),
        ("Honda Sports Street Motorcycle", "High performance modern 300cc street motorcycle with aerodynamic styling and ABS brakes", "Automotive", 129999.00, "motorcycle.jpg"),
        ("Fox Mineral Daily Sunscreen SPF 50+", "Hydrating broad-spectrum SPF 50+ mineral daily facial sunscreen with zinc oxide and niacinamide", "Skincare", 359.00, "sunscreen.jpg"),
        ("Insulated Stainless Water Bottle", "Double-wall vacuum insulated 1L leakproof matte black flask water bottle (24hr cold / 12hr hot)", "Home & Kitchen", 599.00, "water_bottle.jpg"),
        ("Python Programming & Web Guide", "Comprehensive masterclass guide to Python web development, Flask architecture, and modern APIs", "Books", 499.00, "python_book.jpg"),
        ("Premium Hardcover Journal Notebook", "Luxury ruled hardcover stationery journal with heavyweight 120gsm acid-free paper", "Stationery", 249.00, "notebook.jpg")
    ]

    for name, desc, cat, price, img in standard_products:
        cursor.execute("SELECT * FROM products WHERE name = ? OR image = ?", (name, img))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE products 
                SET name = ?, description = ?, category = ?, price = ?, image = ?
                WHERE product_id = ?
            """, (name, desc, cat, price, img, existing['product_id']))
        else:
            cursor.execute("""
                INSERT INTO products (name, description, category, price, image)
                VALUES (?, ?, ?, ?, ?)
            """, (name, desc, cat, price, img))

    conn.commit()

    # Final query to check catalog
    cursor.execute("SELECT product_id, name, category, price, image FROM products ORDER BY product_id ASC")
    final_prods = cursor.fetchall()
    print(f"\nFinal Clean Catalog ({len(final_prods)} unique products):")
    for p in final_prods:
        print(f"#{p['product_id']}: {p['name']} [{p['category']}] - Rs.{p['price']} -> {p['image']}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    run_cleanup()
