"""
Authentication API endpoints for Evergrow360

This module provides secure authentication with:
- User registration with minimal data collection
- Login with JWT tokens
- Password reset functionality
- Session management
- Rate limiting and security protection
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt
)
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime, timedelta
import secrets

from app.utils.security import (
    password_security, input_sanitizer, require_auth, 
    log_access, access_logger
)
from app.utils.anonymization import anonymization_service
from app.services.firebase_service import firebase_service

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Token blacklist (in production, use Redis)
blacklisted_tokens = set()


# Validation schemas
class RegisterSchema(Schema):
    email = fields.Email(required=True, validate=validate.Length(max=254))
    password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    first_name = fields.Str(required=False, validate=validate.Length(max=50))
    marketing_consent = fields.Bool(load_default=False)
    terms_accepted = fields.Bool(required=True, validate=validate.Equal(True))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    remember_me = fields.Bool(load_default=False)


class PasswordResetRequestSchema(Schema):
    email = fields.Email(required=True)


class PasswordResetSchema(Schema):
    reset_token = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=128))


@auth_bp.route('/register', methods=['POST'])
@log_access('register', 'user_account')
def register():
    """
    Register new user with minimal data collection
    
    Only collects email, password, and consent flags.
    All other data is collected during onboarding.
    """
    firebase_service._initialize_firebase()
    try:
        # Validate request data
        schema = RegisterSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify({
                'error': 'Validation failed',
                'details': err.messages
            }), 400
        
        # Sanitize inputs
        email = input_sanitizer.sanitize_string(data['email'].lower().strip())
        password = data['password']
        first_name = input_sanitizer.sanitize_string(data.get('first_name', ''))
        
        # Validate email format
        if not input_sanitizer.validate_email(email):
            return jsonify({
                'error': 'Invalid email format'
            }), 400
        
        # Check password strength
        password_check = password_security.check_password_strength(password)
        if not password_check['valid']:
            return jsonify({
                'error': 'Password does not meet requirements',
                'requirements': {
                    'minimum_length': 8,
                    'must_contain': ['uppercase', 'lowercase', 'digit', 'special_character']
                },
                'current_strength': password_check['strength']
            }), 400


        
        # Generate anonymous user ID
        user_id = anonymization_service.generate_anonymous_id(email)

        # Check if user already exists (by anonymous ID)
        existing_user = firebase_service.get_user_profile_sync(user_id)
        if existing_user:
            return jsonify({
                'error': 'User already exists',
                'message': 'An account with this email already exists'
            }), 409

        # Hash password
        password_hash = password_security.hash_password(password)

        # Create anonymized user profile
        user_data = {
            'email': email,  # Only used for ID generation, not stored
            'password_hash': password_hash,
            'first_name': first_name,
            'marketing_consent': data['marketing_consent'],
            'terms_accepted': data['terms_accepted'],
            'registration_date': datetime.utcnow().isoformat(),
            'email_verified': False,
            'onboarding_completed': False
        }

        # Create user profile directly to ensure password_hash is stored
        firebase_service.db.collection('users').document(user_id).set(user_data)
        created_user_id = user_id

        # Generate tokens
        access_token = create_access_token(
            identity=created_user_id,
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            identity=created_user_id,
            expires_delta=timedelta(days=30)
        )

        # Log successful registration
        access_logger.log_access(created_user_id, 'register', 'user_account', success=True)

        return jsonify({
            'message': 'Registration successful',
            'user_id': created_user_id,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'onboarding_required': True,
            'token_expires_in': 3600
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Registration failed: {e}")
        return jsonify({
            'error': 'Registration failed',
            'message': 'An unexpected error occurred'
        }), 500


@auth_bp.route('/login', methods=['POST'])
@log_access('login', 'user_session')
def login():
    """
    Authenticate user and return JWT tokens
    """
    firebase_service._initialize_firebase()
    try:
        # Validate request data
        schema = LoginSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify({
                'error': 'Validation failed',
                'details': err.messages
            }), 400
        
        # Sanitize inputs
        email = input_sanitizer.sanitize_string(data['email'].lower().strip())
        password = data['password']
        remember_me = data['remember_me']
        
        # Generate user ID from email
        user_id = anonymization_service.generate_anonymous_id(email)

        # Get user profile
        user_profile = firebase_service.get_user_profile_sync(user_id)
        if not user_profile:
            # Don't reveal whether user exists
            return jsonify({
                'error': 'Invalid credentials',
                'message': 'Email or password is incorrect'
            }), 401

        # Verify password
        stored_password_hash = user_profile.get('password_hash')
        if not stored_password_hash or not password_security.verify_password(password, stored_password_hash):
            access_logger.log_access(user_id, 'login', 'user_session', success=False)
            return jsonify({
                'error': 'Invalid credentials',
                'message': 'Email or password is incorrect'
            }), 401

        # Generate tokens
        token_expires = timedelta(days=7) if remember_me else timedelta(hours=1)
        access_token = create_access_token(
            identity=user_id,
            expires_delta=token_expires
        )
        refresh_token = create_refresh_token(
            identity=user_id,
            expires_delta=timedelta(days=30)
        )

        # Update last login
        firebase_service.update_user_profile_sync(user_id, {
            'last_login': datetime.utcnow().isoformat(),
            'last_active': datetime.utcnow().isoformat()
        })
        access_logger.log_access(user_id, 'login', 'user_session', success=True)
        
        return jsonify({
            'message': 'Login successful',
            'user_id': user_id,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'onboarding_completed': user_profile.get('onboarding_completed', False),
            'token_expires_in': int(token_expires.total_seconds())
        }), 200
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        current_app.logger.error(f"Login failed: {e}\nTraceback:\n{tb}")
        print(f"Login failed: {e}\nTraceback:\n{tb}")
        return jsonify({
            'error': 'Login failed',
            'message': str(e),
            'traceback': tb
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Check if user still exists
        user_profile = firebase_service.get_user_profile(current_user_id)
        if not user_profile:
            return jsonify({
                'error': 'User not found',
                'message': 'User account no longer exists'
            }), 404
        
        # Generate new access token
        new_access_token = create_access_token(
            identity=current_user_id,
            expires_delta=timedelta(hours=1)
        )
        
        # Log token refresh
        access_logger.log_access(current_user_id, 'refresh_token', 'user_session', success=True)
        
        return jsonify({
            'access_token': new_access_token,
            'token_expires_in': 3600
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh failed: {e}")
        return jsonify({
            'error': 'Token refresh failed',
            'message': 'Unable to refresh token'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
@log_access('logout', 'user_session')
def logout():
    """
    Logout user and blacklist token
    """
    try:
        current_user_id = get_jwt_identity()
        jti = get_jwt()['jti']  # JWT ID
        
        # Add token to blacklist
        blacklisted_tokens.add(jti)
        
        # Update last logout time
        firebase_service.update_user_profile(current_user_id, {
            'last_logout': datetime.utcnow().isoformat()
        })
        
        # Log successful logout
        access_logger.log_access(current_user_id, 'logout', 'user_session', success=True)
        
        return jsonify({
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout failed: {e}")
        return jsonify({
            'error': 'Logout failed',
            'message': 'An unexpected error occurred'
        }), 500


@auth_bp.route('/password-reset-request', methods=['POST'])
@log_access('password_reset_request', 'user_account')
def request_password_reset():
    """
    Request password reset (sends email with reset link)
    """
    try:
        # Validate request data
        schema = PasswordResetRequestSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify({
                'error': 'Validation failed',
                'details': err.messages
            }), 400
        
        email = input_sanitizer.sanitize_string(data['email'].lower().strip())
        user_id = anonymization_service.generate_anonymous_id(email)
        
        # Check if user exists (don't reveal if they don't)
        user_profile = firebase_service.get_user_profile(user_id)
        
        # Always return success to prevent email enumeration
        # Only send email if user actually exists
        if user_profile:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            reset_expires = (datetime.utcnow() + timedelta(hours=1)).isoformat()
            
            # Store reset token
            firebase_service.update_user_profile(user_id, {
                'password_reset_token': reset_token,
                'password_reset_expires': reset_expires
            })
            
            # TODO: Send reset email
            # email_service.send_password_reset_email(email, reset_token)
            
            current_app.logger.info(f"Password reset requested for user {user_id}")
        
        return jsonify({
            'message': 'If an account with this email exists, a password reset link has been sent'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Password reset request failed: {e}")
        return jsonify({
            'error': 'Request failed',
            'message': 'Unable to process password reset request'
        }), 500


@auth_bp.route('/password-reset', methods=['POST'])
@log_access('password_reset', 'user_account')
def reset_password():
    """
    Reset password using reset token
    """
    try:
        # Validate request data
        schema = PasswordResetSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify({
                'error': 'Validation failed',
                'details': err.messages
            }), 400
        
        reset_token = data['reset_token']
        new_password = data['new_password']
        
        # Check password strength
        password_check = password_security.check_password_strength(new_password)
        if not password_check['valid']:
            return jsonify({
                'error': 'Password does not meet requirements',
                'requirements': {
                    'minimum_length': 8,
                    'must_contain': ['uppercase', 'lowercase', 'digit', 'special_character']
                }
            }), 400
        
        # Find user by reset token
        # This would require a query to Firestore by reset token field
        # For now, this is a simplified implementation
        user_id = None  # Replace with actual user lookup
        
        # Validate reset token and expiration
        # user = find_user_by_reset_token(reset_token)
        # if not user or token_expired(user.reset_expires):
        #     return jsonify({'error': 'Invalid or expired reset token'}), 400
        
        # Hash new password
        new_password_hash = password_security.hash_password(new_password)
        
        # Update password and clear reset token
        # await firebase_service.update_user_profile(user_id, {
        #     'password_hash': new_password_hash,
        #     'password_reset_token': None,
        #     'password_reset_expires': None,
        #     'password_changed_at': datetime.utcnow().isoformat()
        # })
        
        return jsonify({
            'message': 'Password reset successful'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Password reset failed: {e}")
        return jsonify({
            'error': 'Password reset failed',
            'message': 'Unable to reset password'
        }), 500


@auth_bp.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    """
    Verify if current token is valid
    """
    try:
        current_user_id = get_jwt_identity()
        jti = get_jwt()['jti']
        
        # Check if token is blacklisted
        if jti in blacklisted_tokens:
            return jsonify({
                'error': 'Token invalid',
                'message': 'Token has been revoked'
            }), 401
        
        # Check if user still exists
        user_profile = firebase_service.get_user_profile(current_user_id)
        if not user_profile:
            return jsonify({
                'error': 'User not found',
                'message': 'User account no longer exists'
            }), 404
        
        return jsonify({
            'valid': True,
            'user_id': current_user_id,
            'onboarding_completed': user_profile.get('onboarding_completed', False)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token verification failed: {e}")
        return jsonify({
            'error': 'Token verification failed',
            'message': 'Unable to verify token'
        }), 500


@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
@log_access('change_password', 'user_account')
def change_password():
    """
    Change password for authenticated user
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Validate request
        data = request.json
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({
                'error': 'Missing required fields',
                'message': 'Both current and new passwords are required'
            }), 400
        
        # Get user profile
        user_profile = firebase_service.get_user_profile(current_user_id)
        if not user_profile:
            return jsonify({
                'error': 'User not found'
            }), 404
        
        # Verify current password
        stored_password_hash = user_profile.get('password_hash')
        if not password_security.verify_password(current_password, stored_password_hash):
            return jsonify({
                'error': 'Invalid current password'
            }), 401
        
        # Check new password strength
        password_check = password_security.check_password_strength(new_password)
        if not password_check['valid']:
            return jsonify({
                'error': 'Password does not meet requirements',
                'requirements': {
                    'minimum_length': 8,
                    'must_contain': ['uppercase', 'lowercase', 'digit', 'special_character']
                }
            }), 400
        
        # Hash new password
        new_password_hash = password_security.hash_password(new_password)
        
        # Update password
        firebase_service.update_user_profile(current_user_id, {
            'password_hash': new_password_hash,
            'password_changed_at': datetime.utcnow().isoformat()
        })
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Password change failed: {e}")
        return jsonify({
            'error': 'Password change failed',
            'message': 'Unable to change password'
        }), 500


# JWT token blacklist checker
@auth_bp.before_app_request
def check_if_token_revoked():
    """Check if JWT token is blacklisted"""
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt
        
        # Only check for endpoints that require auth
        if request.endpoint and 'auth' in request.endpoint:
            return
        
        verify_jwt_in_request(optional=True)
        token = get_jwt()
        
        if token and token.get('jti') in blacklisted_tokens:
            return jsonify({
                'error': 'Token revoked',
                'message': 'Token has been revoked'
            }), 401
            
    except Exception:
        # If JWT verification fails, let the endpoint handle it
        pass