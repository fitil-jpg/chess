#!/bin/bash

CONTAINER_NAME="arch-viz-vnc"
VNC_PASSWORD="your_password"

case "$1" in
    start)
        echo "Starting VNC container..."
        docker run -d --name $CONTAINER_NAME \
          -p 5900:5900 -p 8080:8080 \
          -e DISPLAY=:99 \
          ubuntu:22.04 bash -c "
            set -e
            echo 'Updating packages...'
            apt-get update -qq
            echo 'Installing VNC packages...'
            apt-get install -y -qq x11vnc xvfb mesa-utils x11-apps
            echo 'Setting VNC password...'
            mkdir -p ~/.vnc
            echo '$VNC_PASSWORD' | x11vnc -storepasswd /dev/stdin ~/.vnc/passwd
            chmod 600 ~/.vnc/passwd
            echo 'Starting Xvfb...'
            Xvfb :99 -screen 0 1920x1080x24 &
            export DISPLAY=:99
            sleep 3
            echo 'Starting VNC server with password...'
            x11vnc -display :99 -rfbauth ~/.vnc/passwd -listen 0.0.0.0 -xkb -forever -shared &
            sleep 2
            echo 'VNC Server ready on port 5900 with password protection'
            sleep infinity
          "
        echo "Container started. VNC available at localhost:5900"
        echo "Password: $VNC_PASSWORD"
        ;;
    stop)
        echo "Stopping VNC container..."
        docker stop $CONTAINER_NAME
        echo "Container stopped."
        ;;
    remove)
        echo "Removing VNC container..."
        docker stop $CONTAINER_NAME 2>/dev/null || true
        docker rm $CONTAINER_NAME
        echo "Container removed."
        ;;
    restart)
        echo "Restarting VNC container..."
        docker restart $CONTAINER_NAME
        echo "Container restarted."
        ;;
    logs)
        echo "Showing container logs..."
        docker logs $CONTAINER_NAME
        ;;
    status)
        echo "Container status:"
        docker ps -a --filter name=$CONTAINER_NAME
        ;;
    connect)
        echo "Connecting to container..."
        docker exec -it $CONTAINER_NAME bash
        ;;
    *)
        echo "Usage: $0 {start|stop|remove|restart|logs|status|connect}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the VNC container"
        echo "  stop     - Stop the VNC container"
        echo "  remove   - Stop and remove the VNC container"
        echo "  restart  - Restart the VNC container"
        echo "  logs     - Show container logs"
        echo "  status   - Show container status"
        echo "  connect  - Connect to container shell"
        echo ""
        echo "VNC Connection:"
        echo "  Address: localhost:5900"
        echo "  Password: $VNC_PASSWORD"
        exit 1
        ;;
esac