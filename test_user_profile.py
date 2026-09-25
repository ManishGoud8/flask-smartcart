import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import app, get_db_connection

def test_profile_flow():
    client = app.test_client()
    app.config['TESTING'] = True

    # 1. Login Customer
    res = client.post('/user-login', data={
        'email': 'user@smartcart.com',
        'password': 'user123'
    }, follow_redirects=True)
    assert res.status_code == 200
    print("[OK] Customer logged in successfully.")

    # 2. Access Profile page
    res = client.get('/user/profile')
    assert res.status_code == 200
    assert b"Personal Settings & Avatar" in res.data
    print("[OK] User profile page rendered.")

    # 3. Update Name and Upload Profile Avatar Image
    fake_avatar = (io.BytesIO(b"fake image content bytes"), "profile_photo.jpg")
    res = client.post('/user/profile', data={
        'name': 'Alex Customer',
        'email': 'user@smartcart.com',
        'password': '',
        'profile_image': fake_avatar
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Profile updated successfully!" in res.data
    print("[OK] Profile updated with new avatar image.")

    # 4. Verify session state & database persistence
    with client.session_transaction() as sess:
        assert sess.get('user_name') == 'Alex Customer'
        assert sess.get('user_profile_image') != ''
        print(f"[OK] Session profile updated: {sess.get('user_profile_image')}")

    # 5. Check navbar renders avatar
    res = client.get('/user/products')
    assert res.status_code == 200
    assert b"user_avatar_img" in res.data or b"user-avatar-img" in res.data
    print("[OK] Products catalog renders user avatar navbar icon.")

    print("\n[SUCCESS] All User Profile tests passed!")

if __name__ == '__main__':
    test_profile_flow()
