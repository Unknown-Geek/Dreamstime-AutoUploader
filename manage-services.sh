#!/bin/bash
# Dreamstime Automation Services Manager

SERVICES="xvfb x11vnc novnc chromium-dreamstime dreamstime-bot"

case "$1" in
    start)
        echo "Starting all services..."
        for svc in $SERVICES; do
            sudo systemctl start $svc
            sleep 2
        done
        echo "All services started."
        ;;
    stop)
        echo "Stopping all services..."
        for svc in $(echo $SERVICES | tr ' ' '\n' | tac | tr '\n' ' '); do
            sudo systemctl stop $svc
        done
        echo "All services stopped."
        ;;
    restart)
        echo "Restarting all services..."
        $0 stop
        sleep 3
        $0 start
        ;;
    status)
        echo "Service Status:"
        echo "==============="
        for svc in $SERVICES; do
            status=$(systemctl is-active $svc)
            printf "%-25s %s\n" "$svc:" "$status"
        done
        echo ""
        echo "URLs:"
        echo "  VNC Viewer: https://n8n.shravanpandala.me/vnc/vnc.html"
        echo "  Bot API:    https://n8n.shravanpandala.me/dreamstime/"
        echo ""
        echo "API Commands:"
        echo "  Start automation: curl -X POST https://n8n.shravanpandala.me/dreamstime/api/start -H 'Content-Type: application/json' -d '{\"repeat_count\": 10}'"
        echo "  Check status:     curl https://n8n.shravanpandala.me/dreamstime/api/status"
        echo "  Stop automation:  curl -X POST https://n8n.shravanpandala.me/dreamstime/api/stop"
        ;;
    logs)
        echo "Showing dreamstime-bot logs..."
        sudo journalctl -u dreamstime-bot -f
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
