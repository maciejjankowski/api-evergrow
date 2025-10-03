#!/bin/bash
# Script to start and stop the Evergrow360 Python server using .venv and run.py
# Usage: ./server.sh start|stop|status

PID_FILE="server.pid"
LOG_FILE="server.log"

start_server() {
    if [ -f "$PID_FILE" ]; then
        echo "Server already running (PID $(cat $PID_FILE))"
        exit 0
    fi
    source .venv/bin/activate
    nohup python run.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Server started (PID $!)"
}

stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        kill $PID && rm "$PID_FILE"
        echo "Server stopped (PID $PID)"
    else
        echo "Server not running."
    fi
}

status_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null; then
            echo "Server is running (PID $PID)"
        else
            echo "Server PID file exists but process not running."
        fi
    else
        echo "Server not running."
    fi
}

case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    status)
        status_server
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
