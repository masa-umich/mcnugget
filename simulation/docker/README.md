# Simulation Docker Guide

This directory contains the necessary files to run the McNugget simulation together with a Synnax cluster in Docker containers.

## Quick Start

To build and start both the Synnax and Simulation containers, run:

```sh
./run_sim.sh start
```

**Note:** If Docker is not installed on your Linux system, the script will attempt to install it for you (requires `sudo`).

## Commands

The `./run_sim.sh` script provides several commands:

- `start`: Build and start the containers in the background.
- `stop`: Stop and remove the containers.
- `restart`: Restart the containers (useful after code or config changes).
- `logs`: Follow the logs of both containers.
- `install`: Just perform the Docker installation check/setup.

## Configuration

- **`docker-compose.yml`**: Defines the services and their relationship.
- **`Dockerfile`**: Defines how the simulation image is built.
- **`aliases.yaml` & `press-sim.yaml`**: Simulation configuration files (copied into the container).

## Connecting to Synnax

By default, the simulator connects to the `synnax` service inside the Docker network. If you want to connect to this local Synnax cluster from your host machine (e.g., using a script running locally or the Synnax Console), use:

- **Host:** `localhost`
- **Port:** `9090`
- **Insecure:** `TRUE` (No TLS/Authentication)
