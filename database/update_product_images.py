import os
import shutil
import sqlite3
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

ARTIFACT_DIR = r"C:\Users\manish goud\.gemini\antigravity-ide\brain\619f8cc0-4dae-4a80-8da1-f050cb9f4493"
DEST_DIR = config.PRODUCT_UPLOAD_FOLDER

os.makedirs(DEST_DIR, exist_ok=True)

# Map of clean filename -> artifact filename prefix
IMAGES_MAPPING = {
    "headphones.jpg": "wireless_headphones",
    "asus_laptop.jpg": "asus_laptop",
    "cotton_shirt.jpg": "cotton_shirt",
    "mechanical_keyboard.jpg": "mechanical_keyboard",
    "gaming_mouse.jpg": "gaming_mouse",
    "water_bottle.jpg": "water_bottle",
    "notebook.jpg": "notebook_stationery",
    "sunscreen.jpg": "sunscreen_cream",
    "bicycle.jpg": "urban_bicycle",
    "motorcycle.jpg": "sports_motorcycle",
    "python_book.jpg": "python_book",
}

def copy_images():
    artifact_files = os.listdir(ARTIFACT_DIR)
    print("Copying generated images from artifacts to uploads directory...")
    for target_name, prefix in IMAGES_MAPPING.items():
        # Find matching artifact file
        match = None
        for f in artifact_files:
            if f.startswith(prefix) and f.endswith(('.jpg', '.png', '.webp')):
                match = f
                break
        if match:
            src_path = os.path.join(ARTIFACT_DIR, match)
            dst_path = os.path.join(DEST_DIR, target_name)
            shutil.copy2(src_path, dst_path)
            print(f"Copied {match} -> {target_name} ({os.path.getsize(dst_path)} bytes)")
        else:
            print(f"Warning: No match found for prefix {prefix}")

    # Also make sure legacy filenames in test or previous uploads resolve to real images
    legacy_aliases = {
        "TRQK9140.JPG": "cotton_shirt.jpg",
        "2684_WhatsApp_Image_2026-08-31_at_10.22.50_AM_1.jpeg": "notebook.jpg",
        "5018_th.jpg": "asus_laptop.jpg",
        "8042_2024-Merida-eOne-Sixty-10K-07508.jpg": "bicycle.jpg",
        "6791_p1_Sunscreen_W1807_gi172423347.jpg": "sunscreen.jpg",
        "6610_OIP.webp": "motorcycle.jpg",
    }
    for legacy_name, source_name in legacy_aliases.items():
        src_path = os.path.join(DEST_DIR, source_name)
        if os.path.exists(src_path):
            dst_path = os.path.join(DEST_DIR, legacy_name)
            shutil.copy2(src_path, dst_path)
            print(f"Created alias {legacy_name} -> {source_name}")

    # Ensure test dummy images have real headphone photo
    for f in os.listdir(DEST_DIR):
        if "test_headphone" in f:
            src_path = os.path.join(DEST_DIR, "headphones.jpg")
            if os.path.exists(src_path):
                shutil.copy2(src_path, os.path.join(DEST_DIR, f))

def update_database_records():
    print("\nUpdating database product image references in SQLite...")
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = lambda c, r: {col[0]: r[idx] for idx, col in enumerate(c.description)}
    cursor = conn.cursor()

    # Update known items to clean image filenames
    updates = [
        ("shirt", "cotton_shirt.jpg"),
        ("paper", "notebook.jpg"),
        ("laptop", "asus_laptop.jpg"),
        ("bicycle", "bicycle.jpg"),
        ("cream", "sunscreen.jpg"),
        ("motor cycle", "motorcycle.jpg"),
        ("Gaming Mouse", "gaming_mouse.jpg"),
        ("Mechanical Keyboard", "mechanical_keyboard.jpg"),
        ("Water Bottle", "water_bottle.jpg"),
        ("Python", "python_book.jpg"),
        ("Headphone", "headphones.jpg")
    ]

    for key, img_file in updates:
        cursor.execute("""
            UPDATE products 
            SET image = ? 
            WHERE name LIKE ? OR category LIKE ?
        """, (img_file, f"%{key}%", f"%{key}%"))
        print(f"Updated records matching '{key}' to image '{img_file}' (affected: {cursor.rowcount})")

    # If any remaining product has NULL image, assign based on id or default
    cursor.execute("SELECT product_id, name, category, image FROM products")
    all_prods = cursor.fetchall()
    for p in all_prods:
        if not p['image']:
            # fallback based on category or default
            cat = (p['category'] or '').lower()
            img = 'headphones.jpg'
            if 'book' in cat or 'python' in (p['name'] or '').lower():
                img = 'python_book.jpg'
            elif 'fashion' in cat or 'shirt' in cat:
                img = 'cotton_shirt.jpg'
            elif 'electro' in cat:
                img = 'headphones.jpg'
            elif 'home' in cat or 'kitchen' in cat:
                img = 'water_bottle.jpg'
            cursor.execute("UPDATE products SET image = ? WHERE product_id = ?", (img, p['product_id']))
            print(f"Set fallback image '{img}' for product #{p['product_id']} ({p['name']})")

    conn.commit()
    cursor.close()
    conn.close()
    print("Database product images successfully updated!")

if __name__ == '__main__':
    copy_images()
    update_database_records()
