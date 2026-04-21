#!/bin/bash

# Script to run and stop the McNugget simulation in Docker

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

function install_docker() {
    echo "Docker not detected. Attempting to install Docker..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Check if it's Ubuntu/Debian
        if [ -f /etc/debian_version ]; then
            echo "Detected Debian-based system. Installing using apt..."
            sudo apt-get update
            sudo apt-get install -y docker.io docker-compose-v2
            
            # Add current user to docker group if possible
            sudo usermod -aG docker $USER
            echo "Docker installed. You may need to log out and back in for group changes to take effect."
        else
            echo "Unsupported Linux distribution for auto-install. Please install Docker manually."
            exit 1
        fi
    else
        echo "Auto-installation only supported on Linux. Please install Docker for your OS."
        exit 1
    fi
}

function check_docker() {
    if ! command -v docker &> /dev/null; then
        install_docker
    fi
    
    # Identify which docker compose command to use
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        echo "Docker Compose not detected. Attempting to install..."
        if [ -f /etc/debian_version ]; then
            sudo apt-get update && sudo apt-get install -y docker-compose-plugin || sudo apt-get install -y docker-compose
            # Try again
            if docker compose version &> /dev/null; then
                DOCKER_COMPOSE_CMD="docker compose"
            else
                DOCKER_COMPOSE_CMD="docker-compose"
            fi
        else
            echo "Unsupported Linux distribution for auto-install of Compose. Please install it manually."
            exit 1
        fi
    fi
}

function usage() {
    echo "Usage: $0 [start|stop|restart|logs|install]"
    echo ""
    echo "Commands:"
    echo "  start    Build and start the simulation and Synnax containers"
    echo "  stop     Stop and remove the containers"
    echo "  restart  Restart the containers"
    echo "  logs     Follow the logs of the containers"
    echo "  install  Just install Docker and dependencies"
}

# Always ensure we have a valid command even for restart
check_docker

case "$1" in
    start)
        echo "Building and starting containers..."
        sudo $DOCKER_COMPOSE_CMD up --build -d
        echo "Containers started. You can view logs with '$0 logs'"
        ;;
    stop)
        echo "Stopping containers..."
        sudo $DOCKER_COMPOSE_CMD down
        ;;
    restart)
        $0 stop
        $0 start
        ;;
    logs)
        sudo $DOCKER_COMPOSE_CMD logs -f
        ;;
    install)
        echo "Docker and dependencies are ready."
        ;;
    *)
        usage
        exit 1
        ;;
esac
