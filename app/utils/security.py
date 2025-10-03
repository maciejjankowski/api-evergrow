"""
Security utilities for Evergrow360 backend

This module provides comprehensive security features including:
- Data encryption/decryption
- Password hashing
- Input sanitization
- Security headers
- Access logging
"""

import os
import hashlib
import secrets
import base64
from datetime import datetime, timezone
from functools import wraps
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from passlib.context import CryptContext
from flask import request, current_app, g
import bleach


class DataEncryption:
    """Data encryption service for sensitive information"""
    
    def __init__(self, key=None):
        self._fernet = None
        self._key = key
    
    def _get_fernet(self):
        """Lazy initialization of Fernet cipher"""
        if self._fernet is None:
            if self._key:
                self._fernet = Fernet(self._key.encode() if isinstance(self._key, str) else self._key)
            else:
                # Generate key from environment variable or create new one
                encryption_key = os.environ.get('DATA_ENCRYPTION_KEY')
                if not encryption_key:
                    # In production, this should come from secure key management
                    key = Fernet.generate_key()
                    # Only log if we have app context
                    try:
                        from flask import current_app
                        current_app.logger.warning("Generated new encryption key - store securely!")
                    except RuntimeError:
                        # Outside app context, just generate key
                        pass
                else:
                    key = base64.urlsafe_b64decode(encryption_key.encode())
                self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        if not data:
            return data
        return self._get_fernet().encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        if not encrypted_data:
            return encrypted_data
        try:
            return self._get_fernet().decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            # Handle decryption errors gracefully
            try:
                from flask import current_app
                current_app.logger.error(f"Decryption failed: {e}")
            except RuntimeError:
                # Outside app context
                pass
            raise ValueError("Invalid encrypted data")
    
    def encrypt_dict(self, data_dict: dict, fields_to_encrypt: list) -> dict:
        """Encrypt specific fields in a dictionary"""
        encrypted_dict = data_dict.copy()
        for field in fields_to_encrypt:
            if field in encrypted_dict and encrypted_dict[field]:
                encrypted_dict[field] = self.encrypt(str(encrypted_dict[field]))
        return encrypted_dict
    
    def decrypt_dict(self, encrypted_dict: dict, fields_to_decrypt: list) -> dict:
        """Decrypt specific fields in a dictionary"""
        decrypted_dict = encrypted_dict.copy()
        for field in fields_to_decrypt:
            if field in decrypted_dict and decrypted_dict[field]:
                decrypted_dict[field] = self.decrypt(decrypted_dict[field])
        return decrypted_dict


class PasswordSecurity:
    """Password hashing and verification"""
    
    def __init__(self):
        # Use Argon2 for password hashing (OWASP recommended)
        self.pwd_context = CryptContext(
            schemes=['argon2'],
            deprecated='auto',
            argon2__memory_cost=65536,  # 64 MB
            argon2__time_cost=3,        # 3 iterations
            argon2__parallelism=1,      # 1 thread
        )
    
    def hash_password(self, password: str) -> str:
        """Hash password securely"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(password, password_hash)
    
    def check_password_strength(self, password: str) -> dict:
        """Check password strength and return requirements"""
        checks = {
            'length': len(password) >= 8,
            'uppercase': any(c.isupper() for c in password),
            'lowercase': any(c.islower() for c in password),
            'digit': any(c.isdigit() for c in password),
            'special': any(c in '!@#$%^&*(),.?":{}|<>' for c in password)
        }
        
        score = sum(checks.values())
        strength = 'weak' if score < 3 else 'medium' if score < 5 else 'strong'
        
        return {
            'score': score,
            'strength': strength,
            'checks': checks,
            'valid': score >= 4  # Require at least 4 criteria
        }


class InputSanitizer:
    """Input sanitization and validation"""
    
    @staticmethod
    def sanitize_html(content: str) -> str:
        """Sanitize HTML content to prevent XSS"""
        if not content:
            return content
        
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
        allowed_attributes = {}
        
        return bleach.clean(
            content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
    
    @staticmethod
    def sanitize_string(content: str, max_length: int = 1000) -> str:
        """Sanitize general string input"""
        if not content:
            return content
        
        # Remove null bytes and control characters
        content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\t')
        
        # Truncate to max length
        if len(content) > max_length:
            content = content[:max_length]
        
        return content.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) if email else False


class SecurityHeaders:
    """Security headers middleware"""
    
    @staticmethod
    def init_app(app):
        """Initialize security headers for Flask app"""
        
        @app.after_request
        def set_security_headers(response):
            # Content Security Policy
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.stripe.com; "
                "frame-src https://js.stripe.com; "
                "object-src 'none'; "
                "base-uri 'self';"
            )
            response.headers['Content-Security-Policy'] = csp
            
            # Other security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Permissions-Policy'] = (
                'geolocation=(), microphone=(), camera=(), '
                'payment=(), usb=(), magnetometer=(), gyroscope=()'
            )
            
            # HSTS (only in production over HTTPS)
            if app.config.get('ENV') == 'production':
                response.headers['Strict-Transport-Security'] = (
                    'max-age=31536000; includeSubDomains; preload'
                )
            
            return response


class AccessLogger:
    """Security access logging"""
    
    def __init__(self):
        self.encryption = DataEncryption()
    
    def log_access(self, user_id: str, action: str, resource: str, success: bool = True):
        """Log user access with anonymization"""
        try:
            # Create anonymized log entry
            log_entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'user_hash': self._hash_user_id(user_id),
                'action': action,
                'resource': resource,
                'success': success,
                'ip_hash': self._hash_ip(request.remote_addr),
                'user_agent_hash': self._hash_user_agent(request.headers.get('User-Agent', ''))
            }
            
            # Log to application logger
            current_app.logger.info(f"Access: {log_entry}")
            
            # In production, send to security monitoring system
            if current_app.config.get('ENV') == 'production':
                self._send_to_security_system(log_entry)
                
        except Exception as e:
            current_app.logger.error(f"Access logging failed: {e}")
    
    def _hash_user_id(self, user_id: str) -> str:
        """Create hashed user identifier for logging"""
        if not user_id:
            return 'anonymous'
        return hashlib.sha256(f"{user_id}{current_app.secret_key}".encode()).hexdigest()[:16]
    
    def _hash_ip(self, ip_address: str) -> str:
        """Create hashed IP for logging"""
        if not ip_address:
            return 'unknown'
        return hashlib.sha256(f"{ip_address}{current_app.secret_key}".encode()).hexdigest()[:16]
    
    def _hash_user_agent(self, user_agent: str) -> str:
        """Create hashed user agent for logging"""
        if not user_agent:
            return 'unknown'
        return hashlib.sha256(f"{user_agent}{current_app.secret_key}".encode()).hexdigest()[:16]
    
    def _send_to_security_system(self, log_entry: dict):
        """Send log entry to external security monitoring system"""
        # Implement integration with security monitoring (e.g., Splunk, ELK)
        pass


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        try:
            verify_jwt_in_request()
            g.current_user_id = get_jwt_identity()
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.warning(f"Authentication failed: {e}")
            return {'error': 'Authentication required'}, 401
    return decorated_function


def log_access(action: str, resource: str):
    """Decorator to log access to endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger = AccessLogger()
            user_id = getattr(g, 'current_user_id', 'anonymous')
            
            try:
                result = f(*args, **kwargs)
                logger.log_access(user_id, action, resource, success=True)
                return result
            except Exception as e:
                logger.log_access(user_id, action, resource, success=False)
                raise
        return decorated_function
    return decorator


# Global instances
data_encryption = DataEncryption()
password_security = PasswordSecurity()
input_sanitizer = InputSanitizer()
access_logger = AccessLogger()


class SecurityHeaders:
    """Security headers middleware for Flask applications"""
    
    @staticmethod
    def init_app(app):
        """Initialize security headers for the Flask app"""
        
        @app.after_request
        def add_security_headers(response):
            """Add security headers to all responses"""
            
            # Only add restrictive headers in production
            if not app.debug:
                # Prevent clickjacking
                response.headers['X-Frame-Options'] = 'SAMEORIGIN'
                
                # Prevent MIME type sniffing
                response.headers['X-Content-Type-Options'] = 'nosniff'
                
                # Enable XSS protection
                response.headers['X-XSS-Protection'] = '1; mode=block'
                
                # Referrer policy
                response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
                
                # Content Security Policy (strict for production)
                csp = (
                    "default-src 'self'; "
                    "script-src 'self' https://fonts.googleapis.com; "
                    "style-src 'self' https://fonts.googleapis.com; "
                    "font-src 'self' https://fonts.gstatic.com; "
                    "img-src 'self' data: https:; "
                    "connect-src 'self' https://api.openai.com;"
                )
                response.headers['Content-Security-Policy'] = csp
                
                # HSTS (HTTP Strict Transport Security)
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            return response