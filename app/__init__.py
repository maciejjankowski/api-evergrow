"""
Evergrow360 Backend Application Factory

This module creates and configures the Flask application with all necessary
extensions, blueprints, and security measures.
"""

import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from config import config_by_name
from app.utils.security import SecurityHeaders
from app.utils.anonymization import AnonymizationService


def create_app(config_name=None):
    """
    Create and configure Flask application
    
    Args:
        config_name (str): Configuration environment name
        
    Returns:
        Flask: Configured Flask application
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # Initialize Sentry for error tracking (production only)
    if config_name == 'production' and app.config.get('SENTRY_DSN'):
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,
        )
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Serve frontend static files
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'front-end')
    app.static_folder = os.path.join(frontend_path, 'shared')
    app.add_url_rule('/app/<path:filename>', 'frontend_static', 
                     lambda filename: send_from_directory(frontend_path, filename))
    
    # Register frontend routes
    register_frontend_routes(app, frontend_path)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Add security headers
    SecurityHeaders.init_app(app)
    
    return app


def init_extensions(app):
    """Initialize Flask extensions"""
    
    # CORS configuration (enabled for frontend development)
    CORS(app,
        origins=["http://localhost:3000", "http://127.0.0.1:3000", 
                "http://localhost:8080", "http://127.0.0.1:8080",
                "http://localhost:5000", "http://127.0.0.1:5000"],
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # JWT Manager
    jwt = JWTManager(app)
    
    # Rate limiting (disabled for debugging)
    # limiter = Limiter(
    #     key_func=get_remote_address,
    #     app=app,
    #     default_limits=["200 per day", "50 per hour"],
    #     storage_uri=app.config.get('RATE_LIMIT_STORAGE_URL', 'memory://')
    # )
    
    # # Make limiter available globally
    # app.limiter = limiter
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has expired',
            'message': 'Please log in again'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Invalid token',
            'message': 'Please provide a valid authentication token'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Authorization required',
            'message': 'Please provide an authentication token'
        }), 401


def register_blueprints(app):
    """Register API blueprints"""
    
    from app.api.auth import auth_bp
    from app.api.user import user_bp
    from app.api.assessment import assessment_bp
    from app.api.coaching import coaching_bp
    from app.api.marketplace import marketplace_bp
    from app.api.booking import booking_bp
    from app.api.payment import payment_bp
    
    # API v1 blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(assessment_bp, url_prefix='/api/assessment')
    app.register_blueprint(coaching_bp, url_prefix='/api/coaching')
    app.register_blueprint(marketplace_bp, url_prefix='/api/marketplace')
    app.register_blueprint(booking_bp, url_prefix='/api/booking')
    app.register_blueprint(payment_bp, url_prefix='/api/payment')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'evergrow360-api',
            'version': '1.0.0'
        })
    
    # API documentation
    @app.route('/api')
    def api_info():
        return jsonify({
            'name': 'Evergrow360 API',
            'version': '1.0.0',
            'description': 'AI-powered coaching platform API',
            'endpoints': {
                'auth': '/api/auth',
                'user': '/api/user',
                'assessment': '/api/assessment', 
                'coaching': '/api/coaching',
                'marketplace': '/api/marketplace',
                'booking': '/api/booking',
                'payment': '/api/payment'
            }
        })


def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication is required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'error': 'Method Not Allowed',
            'message': 'The method is not allowed for this endpoint'
        }), 405
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.',
            'retry_after': str(error.retry_after)
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.before_request
    def debug_request():
        """Debug all requests"""
        print(f"DEBUG: {request.method} {request.url} from {request.remote_addr}")
        print(f"DEBUG: Headers: {dict(request.headers)}")
        if request.data:
            print(f"DEBUG: Data: {request.data.decode()[:200]}")
    
    @app.after_request
    def log_response_info(response):
        """Log response information for monitoring"""
        if app.config['DEBUG']:
            app.logger.info(f'Response: {response.status_code}')
        return response


def register_frontend_routes(app, frontend_path):
    """Register routes to serve frontend HTML pages"""
    
    @app.route('/')
    def index():
        """Serve the main landing page"""
        return send_from_directory(frontend_path, 'index.html')
    
    @app.route('/app/auth/login.html')
    def login_page():
        """Serve login page"""
        return send_from_directory(os.path.join(frontend_path, 'auth'), 'login.html')
    
    @app.route('/app/auth/register.html')
    def register_page():
        """Serve registration page"""
        return send_from_directory(os.path.join(frontend_path, 'auth'), 'register.html')
    
    @app.route('/app/onboarding/welcome.html')
    def welcome_page():
        """Serve onboarding welcome page"""
        return send_from_directory(os.path.join(frontend_path, 'onboarding'), 'welcome.html')
    
    @app.route('/app/onboarding/assessment.html')
    def assessment_page():
        """Serve assessment page"""
        return send_from_directory(os.path.join(frontend_path, 'onboarding'), 'assessment.html')
    
    @app.route('/app/dashboard/index.html')
    def dashboard_page():
        """Serve dashboard page"""
        return send_from_directory(os.path.join(frontend_path, 'dashboard'), 'index.html')
    
    @app.route('/app/marketplace/index.html')
    def marketplace_page():
        """Serve marketplace page"""
        return send_from_directory(os.path.join(frontend_path, 'marketplace'), 'index.html')
    
    @app.route('/app/booking/index.html')
    def booking_page():
        """Serve booking page"""
        return send_from_directory(os.path.join(frontend_path, 'booking'), 'index.html')
    
    # Catch-all route for other frontend pages
    @app.route('/app/<path:filepath>')
    def frontend_files(filepath):
        """Serve other frontend files"""
        return send_from_directory(frontend_path, filepath)