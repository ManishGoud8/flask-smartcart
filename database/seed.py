import sqlite3
import bcrypt
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def seed_database():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    print("Checking database tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r['name'] for r in cursor.fetchall()]
    print("Tables found:", tables)

    # Seed Admin if not exists
    cursor.execute("SELECT * FROM admin WHERE email = 'admin@smartcart.com'")
    if not cursor.fetchone():
        hashed_pwd = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8')
        cursor.execute("""
            INSERT INTO admin (name, email, password)
            VALUES (?, ?, ?)
        """, ("Admin User", "admin@smartcart.com", hashed_pwd))
        print("Seeded default admin: admin@smartcart.com / admin123")

    # Seed Customer User if not exists
    cursor.execute("SELECT * FROM users WHERE email = 'user@smartcart.com'")
    if not cursor.fetchone():
        hashed_pwd = bcrypt.hashpw(b"user123", bcrypt.gensalt()).decode('utf-8')
        cursor.execute("""
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
        """, ("Test Customer", "user@smartcart.com", hashed_pwd))
        print("Seeded default customer: user@smartcart.com / user123")

    # Seed Sample Products if empty
    cursor.execute("SELECT COUNT(*) as count FROM products")
    if cursor.fetchone()['count'] == 0:
        sample_products = [
            ("Wireless Gaming Mouse", "Ergonomic 2.4GHz wireless optical precision gaming mouse with matte noir finish", "Electronics", 1499.00, "gaming_mouse.jpg"),
            ("Mechanical Keyboard", "White backlit mechanical keyboard with tactile blue switches and aluminum frame", "Electronics", 3299.00, "mechanical_keyboard.jpg"),
            ("Cotton Casual Shirt", "Premium 100% breathable tailored cotton slim fit shirt", "Fashion", 899.00, "cotton_shirt.jpg"),
            ("Stainless Steel Water Bottle", "Insulated 1L leakproof matte black flask water bottle", "Home & Kitchen", 599.00, "water_bottle.jpg"),
            ("Python Programming Guide", "Comprehensive guide to Python web development and Flask architecture", "Books", 499.00, "python_book.jpg"),
            ("Wireless Pro Headphones", "Active noise-cancelling studio wireless over-ear headphones", "Electronics", 2799.00, "headphones.jpg"),
            ("Asus Performance Laptop", "Ultra-thin lightweight laptop with crisp 4K OLED display and high-speed SSD", "Electronics", 59999.00, "asus_laptop.jpg"),
            ("Urban Commuter Bicycle", "Precision lightweight matte black road bicycle with disc brakes", "Sports", 7999.00, "bicycle.jpg"),
            ("Fox Mineral Sunscreen", "Hydrating broad-spectrum SPF 50+ mineral daily facial sunscreen", "Skincare", 359.00, "sunscreen.jpg"),
            ("Honda Sports Motorcycle", "High performance modern street motorcycle with aerodynamic styling", "Automotive", 129999.00, "motorcycle.jpg"),
            ("Premium Hardcover Notebook", "Luxury ruled hardcover journal with heavyweight acid-free paper", "Stationery", 249.00, "notebook.jpg")
        ]
        cursor.executemany("""
            INSERT INTO products (name, description, category, price, image)
            VALUES (?, ?, ?, ?, ?)
        """, sample_products)
        print(f"Seeded {len(sample_products)} sample products.")

    conn.commit()
    cursor.close()
    conn.close()
    print("Seeding completed successfully!")

if __name__ == '__main__':
    seed_database()
