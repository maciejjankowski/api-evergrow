#!/bin/bash
# Command runner for Evergrow360 development tasks

COMMAND="$1"
shift

case "$COMMAND" in
    "start")
        echo "Starting Flask server..."
        source .venv/bin/activate
        ./server.sh start
        ;;
    "stop")
        echo "Stopping Flask server..."
        ./server.sh stop
        ;;
    "restart")
        echo "Restarting Flask server..."
        ./server.sh stop
        sleep 2
        ./server.sh start
        ;;
    "test")
        echo "Running comprehensive tests..."
        ./scripts/site_test.sh
        ;;
    "browser-test")
        echo "Running browser compatibility tests..."
        source .venv/bin/activate
        python scripts/test_browser_compatibility.py
        ;;
    "cors-test")
        echo "Running CORS-specific tests..."
        ./site_test.sh | grep -E "(CORS|✅|❌)"
        ;;
    "health")
        echo "Checking API health..."
        curl -s http://127.0.0.1:5001/health | jq .
        ;;
    "login-test")
        echo "Testing login functionality..."
        ./site_test.sh | grep -A 10 "Testing login"
        ;;
    "status")
        echo "Checking system status..."
        echo "Server status:"
        ./server.sh status
        echo ""
        echo "API health:"
        curl -s http://127.0.0.1:5001/health 2>/dev/null || echo "Server not responding"
        ;;
    "clean")
        echo "Cleaning up test files..."
        rm -f test_*.py *.pyc __pycache__/
        ;;
    *)
        echo "Usage: ./command.sh {start|stop|restart|test|browser-test|cors-test|health|login-test|status|clean}"
        echo ""
        echo "Available commands:"
        echo "  start        - Start the Flask server"
        echo "  stop         - Stop the Flask server"
        echo "  restart      - Restart the Flask server"
        echo "  test         - Run comprehensive tests"
        echo "  browser-test - Run browser compatibility tests"
        echo "  cors-test    - Run CORS-specific tests"
        echo "  health       - Check API health"
        echo "  login-test   - Test login functionality"
        echo "  status       - Check system status"
        echo "  clean        - Clean up test files"
        exit 1
        ;;
esac