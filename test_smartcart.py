import io
import json
import sys
from app import app, get_db_connection

sys.stdout.reconfigure(encoding='utf-8')

def test_full_application_workflow():
    client = app.test_client()
    app.config['TESTING'] = True

    print("\n--- Testing Day 1: Home Route ---")
    res = client.get('/')
    assert res.status_code == 200
    assert b"Welcome to SmartCart" in res.data
    print("✓ Day 1 Home route passed!")

    print("\n--- Testing Day 2 & 3: Admin Flow ---")
    import random
    admin_test_email = f"superadmin_{random.randint(10000, 99999)}@smartcart.com"
    # Admin Signup
    res = client.post('/admin-signup', data={
        'name': 'Super Admin',
        'email': admin_test_email
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Verify OTP" in res.data or b"verify-otp" in res.data
    print("✓ Admin signup OTP triggered!")

    # Retrieve OTP from session in test client
    with client.session_transaction() as sess:
        otp = sess.get('admin_otp')
        assert otp is not None
        print(f"✓ Retrieved session OTP: {otp}")

    # Verify OTP
    res = client.post('/verify-otp', data={
        'otp': otp,
        'password': 'SuperPassword123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Admin Login" in res.data or b"registered successfully" in res.data
    print("✓ Admin OTP verification passed!")

    # Admin Login
    res = client.post('/admin-login', data={
        'email': admin_test_email,
        'password': 'SuperPassword123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Admin Dashboard" in res.data
    print("✓ Admin login & dashboard session passed!")

    print("\n--- Testing Day 4, 5, 6, 7: Admin Products Flow ---")
    # Add Product (Day 4)
    dummy_img = (io.BytesIO(b"fake image data"), "test_headphone.jpg")
    res = client.post('/admin/add-item', data={
        'name': 'Wireless Headphones',
        'description': 'Noise cancelling bluetooth headphones',
        'category': 'Electronics',
        'price': '2499.00',
        'image': dummy_img
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Wireless Headphones" in res.data
    print("✓ Product added with image upload!")

    # Get added product ID from DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE name = 'Wireless Headphones' ORDER BY product_id DESC LIMIT 1")
    added_prod = cursor.fetchone()
    cursor.close()
    conn.close()
    assert added_prod is not None
    prod_id = added_prod['product_id']
    print(f"✓ Found added product ID: {prod_id}")

    # View Item (Day 5)
    res = client.get(f'/admin/view-item/{prod_id}')
    assert res.status_code == 200
    assert b"Noise cancelling" in res.data
    print("✓ Single product view passed!")

    # Update Item (Day 6)
    res = client.post(f'/admin/update-item/{prod_id}', data={
        'name': 'Wireless Pro Headphones',
        'description': 'Active noise cancelling wireless bluetooth headphones',
        'category': 'Electronics',
        'price': '2799.00'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Wireless Pro Headphones" in res.data
    print("✓ Product updated passed!")

    # Search & Filter (Day 7)
    res = client.get('/admin/item-list?search=Headphones&category=Electronics')
    assert res.status_code == 200
    assert b"Wireless Pro Headphones" in res.data
    print("✓ Product search & category filtering passed!")

    # Admin Profile (Day 8)
    dummy_profile_img = (io.BytesIO(b"fake avatar"), "avatar.jpg")
    res = client.post('/admin/profile', data={
        'name': 'Super Admin Updated',
        'email': admin_test_email,
        'password': '',
        'profile_image': dummy_profile_img
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Admin profile updated successfully" in res.data or b"Super Admin Updated" in res.data
    print("✓ Admin profile update passed!")

    # Admin Logout
    res = client.get('/admin-logout', follow_redirects=True)
    assert res.status_code == 200
    print("✓ Admin logout passed!")

    print("\n--- Testing Day 9: Customer Auth & Dashboard ---")
    # User Registration
    test_user_email = f"customer_{random.randint(10000, 99999)}@smartcart.com"
    res = client.post('/user-register', data={
        'name': 'John Customer',
        'email': test_user_email,
        'password': 'CustomerPass123'
    }, follow_redirects=True)
    assert res.status_code == 200
    print("✓ Customer registered successfully!")

    # User Login
    res = client.post('/user-login', data={
        'email': test_user_email,
        'password': 'CustomerPass123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Customer Dashboard" in res.data
    print("✓ Customer login & dashboard passed!")

    print("\n--- Testing Day 10 & 11: Product Browsing & Cart System ---")
    # User Products (Day 10)
    res = client.get('/user/products')
    assert res.status_code == 200
    assert b"Wireless Pro Headphones" in res.data

    # Product Details (Day 10)
    res = client.get(f'/user/product/{prod_id}')
    assert res.status_code == 200
    assert b"Wireless Pro Headphones" in res.data

    # Add to cart via AJAX (Day 11.2)
    res = client.get(f'/user/add-to-cart-ajax/{prod_id}')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['cart_count'] >= 1
    print(f"✓ AJAX Add to Cart: {data['message']} (Count: {data['cart_count']})")

    # View Cart (Day 11)
    res = client.get('/user/cart')
    assert res.status_code == 200
    assert b"Wireless Pro Headphones" in res.data
    assert b"2799" in res.data
    print("✓ View Cart passed!")

    # Increase quantity
    res = client.get(f'/user/cart/increase/{prod_id}', follow_redirects=True)
    assert res.status_code == 200
    assert b"5598" in res.data
    print("✓ Cart quantity increment passed!")

    print("\n--- Testing Day 12 & 13: Razorpay Payment & Order Persistence ---")
    # Payment Route (Day 12)
    res = client.get('/user/pay')
    assert res.status_code == 200
    assert b"Pay with Razorpay" in res.data
    assert b"Scan & Pay via UPI QR Code" in res.data
    assert b"smartcart@upi" in res.data
    print("✓ Checkout payment order creation & UPI QR generation passed!")

    # Verify Payment & Store Order (Day 13)
    test_payment_id = f"pay_test_{random.randint(100000, 999999)}"
    res = client.post('/verify-payment', data={
        'razorpay_order_id': f'order_test_{random.randint(100000, 999999)}',
        'razorpay_payment_id': test_payment_id,
        'razorpay_signature': 'simulated_test_signature',
        'is_simulation': 'true'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Order Confirmed" in res.data or b"Your Order is Confirmed" in res.data
    assert test_payment_id.encode('utf-8') in res.data
    print("✓ Payment verification and order creation passed!")

    # My Orders (Day 13)
    res = client.get('/user/my-orders')
    assert res.status_code == 200
    assert test_payment_id.encode('utf-8') in res.data
    print("✓ My Orders history view passed!")

    print("\n--- Testing Day 14: PDF Invoice Generation ---")
    # Get created order ID
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT order_id FROM orders WHERE razorpay_payment_id = ? LIMIT 1", (test_payment_id,))
    order_row = cursor.fetchone()
    cursor.close()
    conn.close()
    assert order_row is not None
    order_id = order_row['order_id']

    # Download Invoice PDF (Day 14)
    res = client.get(f'/user/download-invoice/{order_id}')
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/pdf'
    assert f"filename=invoice_{order_id}.pdf" in res.headers['Content-Disposition']
    assert res.data.startswith(b'%PDF')
    print(f"✓ PDF Invoice successfully generated and validated! (Size: {len(res.data)} bytes)")

    print("\n--- Testing UPI QR Code Payment Flow ---")
    # Add product to cart again for UPI test
    client.get(f'/user/add-to-cart-ajax/{prod_id}')
    test_upi_utr = f"UTR{random.randint(1000000000, 9999999999)}"
    res = client.post('/user/verify-upi-payment', data={
        'upi_ref_id': test_upi_utr
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Order Confirmed" in res.data
    assert f"UPI-{test_upi_utr}".encode('utf-8') in res.data
    print(f"✓ UPI QR Code payment verified and order created (UTR: {test_upi_utr})!")

    print("\n--- Testing Admin Forgot & Reset Password Flow ---")
    # Request Admin Reset OTP
    res = client.post('/admin-forgot-password', data={
        'email': admin_test_email
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Reset Admin Password" in res.data or b"admin-reset-password" in res.data
    print("✓ Admin forgot password OTP requested successfully!")

    # Retrieve Admin Reset OTP from session
    with client.session_transaction() as sess:
        admin_reset_otp = sess.get('admin_reset_otp')
        assert admin_reset_otp is not None
        print(f"✓ Retrieved admin reset OTP: {admin_reset_otp}")

    # Submit Admin Reset Password
    new_admin_pass = "NewSuperAdminPass2026!"
    res = client.post('/admin-reset-password', data={
        'otp': admin_reset_otp,
        'password': new_admin_pass,
        'confirm_password': new_admin_pass
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Admin Login" in res.data or b"password reset successfully" in res.data
    print("✓ Admin password reset completed!")

    # Login with new Admin password
    res = client.post('/admin-login', data={
        'email': admin_test_email,
        'password': new_admin_pass
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Admin Dashboard" in res.data
    print("✓ Admin login with new reset password succeeded!")

    print("\n--- Testing Customer Forgot & Reset Password Flow ---")
    # Request Customer Reset OTP
    res = client.post('/user-forgot-password', data={
        'email': test_user_email
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Reset Your Password" in res.data or b"user-reset-password" in res.data
    print("✓ Customer forgot password OTP requested successfully!")

    # Retrieve Customer Reset OTP from session
    with client.session_transaction() as sess:
        user_reset_otp = sess.get('user_reset_otp')
        assert user_reset_otp is not None
        print(f"✓ Retrieved customer reset OTP: {user_reset_otp}")

    # Submit Customer Reset Password
    new_cust_pass = "NewCustPassword2026!"
    res = client.post('/user-reset-password', data={
        'otp': user_reset_otp,
        'password': new_cust_pass,
        'confirm_password': new_cust_pass
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"User Login" in res.data or b"password reset successfully" in res.data
    print("✓ Customer password reset completed!")

    # Login with new Customer password
    res = client.post('/user-login', data={
        'email': test_user_email,
        'password': new_cust_pass
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"User Dashboard" in res.data or b"Welcome back" in res.data
    print("✓ Customer login with new reset password succeeded!")

    print("\n============================================================")
    print("🎉 ALL TESTS (INCLUDING FORGOT/RESET PASSWORD & UPI) PASSED SUCCESSFULLY!")
    print("============================================================\n")

if __name__ == '__main__':
    test_full_application_workflow()


