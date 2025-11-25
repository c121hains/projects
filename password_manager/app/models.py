from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


def utc_now():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """User model for authentication."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relationship to stored passwords
    passwords = db.relationship('Password', backref='owner', lazy='dynamic',
                                cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the user's password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Password(db.Model):
    """Model for storing encrypted passwords."""
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(128), nullable=False)
    site_url = db.Column(db.String(256))
    username = db.Column(db.String(128), nullable=False)
    encrypted_password = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Foreign key to user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Password {self.site_name}>'


@login_manager.user_loader
def load_user(id):
    """Load user by ID for Flask-Login."""
    return db.session.get(User, int(id))
