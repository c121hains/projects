import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import current_app


def get_encryption_key():
    """Get or derive the encryption key from configuration."""
    key = current_app.config.get('ENCRYPTION_KEY')
    if key:
        return key.encode() if isinstance(key, str) else key
    
    # Derive key from SECRET_KEY for consistency
    secret = current_app.config.get('SECRET_KEY', 'default-secret')
    if isinstance(secret, str):
        secret = secret.encode()
    
    # Use a fixed salt for key derivation (in production, store this securely)
    salt = b'password_manager_salt_v1'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret))
    return key


def encrypt_password(password):
    """Encrypt a password for storage."""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_password(encrypted_password):
    """Decrypt a stored password."""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = base64.urlsafe_b64decode(encrypted_password.encode())
    decrypted = f.decrypt(encrypted)
    return decrypted.decode()
