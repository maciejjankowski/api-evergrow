#!/usr/bin/env python3
"""
Evergrow360 Backend Application Runner

This script starts the Flask development or production server
with proper configuration and error handling.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app

def main():
    """Main application runner"""
    
    # Get configuration from environment
    config_name = os.environ.get('FLASK_ENV', 'development')
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5001))
    
    # Create Flask application
    app = create_app(config_name)
    
    if not app:
        print("Failed to create Flask application")
        sys.exit(1)
    
    print(f"Starting Evergrow360 API server...")
    print(f"Environment: {config_name}")
    print(f"Debug mode: {debug}")
    print(f"Server: http://{host}:{port}")
    
    # Development vs Production server
    if config_name == 'development':
        # Use Flask development server
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=False,  # Disable reloader for testing
            use_debugger=debug
        )
    else:
        # Use Gunicorn for production (imported here to avoid development dependency)
        try:
            from gunicorn.app.wsgiapp import WSGIApplication
            
            class GunicornApplication(WSGIApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()
                
                def load_config(self):
                    config = {key: value for key, value in self.options.items()
                             if key in self.cfg.settings and value is not None}
                    for key, value in config.items():
                        self.cfg.set(key.lower(), value)
                
                def load(self):
                    return self.application
            
            options = {
                'bind': f"{host}:{port}",
                'workers': int(os.environ.get('GUNICORN_WORKERS', 4)),
                'worker_class': 'sync',
                'timeout': 30,
                'keepalive': 2,
                'max_requests': 1000,
                'max_requests_jitter': 100,
                'preload_app': True,
                'access_log_format': '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s',
                'accesslog': '-',
                'errorlog': '-',
                'loglevel': 'info'
            }
            
            GunicornApplication(app, options).run()
            
        except ImportError:
            print("Gunicorn not available, falling back to Flask development server")
            app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    main()