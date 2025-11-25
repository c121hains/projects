"""Tests for the Password Manager application."""
import pytest
from app import create_app, db
from app.models import User, Password
from app.crypto import encrypt_password, decrypt_password
from config import Config


class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key-for-testing'


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_client(client, app):
    """Create authenticated test client."""
    with app.app_context():
        user = User(username='testuser')
        user.set_password('testpassword123')
        db.session.add(user)
        db.session.commit()
    
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    return client


class TestCrypto:
    """Test password encryption/decryption."""
    
    def test_encrypt_decrypt(self, app):
        """Test that encryption and decryption work correctly."""
        with app.app_context():
            original = 'my-secret-password'
            encrypted = encrypt_password(original)
            decrypted = decrypt_password(encrypted)
            assert decrypted == original
    
    def test_encrypted_different_from_original(self, app):
        """Test that encrypted password is different from original."""
        with app.app_context():
            original = 'my-secret-password'
            encrypted = encrypt_password(original)
            assert encrypted != original


class TestUserModel:
    """Test User model."""
    
    def test_password_hashing(self, app):
        """Test password hashing works correctly."""
        with app.app_context():
            user = User(username='testuser')
            user.set_password('mypassword')
            assert user.check_password('mypassword')
            assert not user.check_password('wrongpassword')


class TestAuthentication:
    """Test authentication routes."""
    
    def test_login_page(self, client):
        """Test login page loads."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data
    
    def test_register_page(self, client):
        """Test register page loads."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data
    
    def test_register_user(self, client, app):
        """Test user registration."""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
    
    def test_login_success(self, client, app):
        """Test successful login."""
        with app.app_context():
            user = User(username='testuser')
            user.set_password('testpassword123')
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'Your Passwords' in response.data
    
    def test_login_invalid_credentials(self, client, app):
        """Test login with invalid credentials."""
        with app.app_context():
            user = User(username='testuser')
            user.set_password('testpassword123')
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        assert b'Invalid username or password' in response.data
    
    def test_logout(self, auth_client):
        """Test logout."""
        response = auth_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data


class TestPasswordCRUD:
    """Test password CRUD operations."""
    
    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires authentication."""
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login
    
    def test_dashboard_loads(self, auth_client):
        """Test dashboard loads for authenticated user."""
        response = auth_client.get('/dashboard')
        assert response.status_code == 200
        assert b'Your Passwords' in response.data
    
    def test_create_password(self, auth_client, app):
        """Test creating a new password entry."""
        response = auth_client.post('/password/new', data={
            'site_name': 'Test Site',
            'site_url': 'https://test.com',
            'username': 'testuser@test.com',
            'password': 'sitepassword123',
            'notes': 'Test notes'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Password saved successfully' in response.data
        
        with app.app_context():
            password = Password.query.filter_by(site_name='Test Site').first()
            assert password is not None
            assert password.username == 'testuser@test.com'
    
    def test_view_password(self, auth_client, app):
        """Test viewing a password."""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            encrypted = encrypt_password('mysecretpassword')
            password = Password(
                site_name='View Test',
                username='viewuser',
                encrypted_password=encrypted,
                user_id=user.id
            )
            db.session.add(password)
            db.session.commit()
            password_id = password.id
        
        response = auth_client.get(f'/password/{password_id}')
        assert response.status_code == 200
        assert b'View Test' in response.data
    
    def test_edit_password(self, auth_client, app):
        """Test editing a password."""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            encrypted = encrypt_password('originalpassword')
            password = Password(
                site_name='Edit Test',
                username='edituser',
                encrypted_password=encrypted,
                user_id=user.id
            )
            db.session.add(password)
            db.session.commit()
            password_id = password.id
        
        response = auth_client.post(f'/password/{password_id}/edit', data={
            'site_name': 'Updated Site',
            'site_url': 'https://updated.com',
            'username': 'updateduser',
            'password': '',
            'notes': 'Updated notes'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Password updated successfully' in response.data
        
        with app.app_context():
            password = db.session.get(Password, password_id)
            assert password.site_name == 'Updated Site'
    
    def test_delete_password(self, auth_client, app):
        """Test deleting a password."""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            encrypted = encrypt_password('deletepassword')
            password = Password(
                site_name='Delete Test',
                username='deleteuser',
                encrypted_password=encrypted,
                user_id=user.id
            )
            db.session.add(password)
            db.session.commit()
            password_id = password.id
        
        response = auth_client.post(f'/password/{password_id}/delete', follow_redirects=True)
        assert response.status_code == 200
        assert b'Password deleted successfully' in response.data
        
        with app.app_context():
            password = db.session.get(Password, password_id)
            assert password is None
    
    def test_cannot_view_other_user_password(self, client, app):
        """Test that users cannot view other users' passwords."""
        with app.app_context():
            # Create first user
            user1 = User(username='user1')
            user1.set_password('password1')
            db.session.add(user1)
            db.session.commit()
            
            # Create password for first user
            encrypted = encrypt_password('secretpassword')
            password = Password(
                site_name='User1 Password',
                username='user1@test.com',
                encrypted_password=encrypted,
                user_id=user1.id
            )
            db.session.add(password)
            db.session.commit()
            password_id = password.id
            
            # Create second user
            user2 = User(username='user2')
            user2.set_password('password2')
            db.session.add(user2)
            db.session.commit()
        
        # Login as user2
        client.post('/login', data={
            'username': 'user2',
            'password': 'password2'
        })
        
        # Try to access user1's password
        response = client.get(f'/password/{password_id}', follow_redirects=True)
        assert b'Access denied' in response.data
