# Use a lightweight Python base image
FROM python:3.13-slim

# Copy the uv binary directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Copy the simulation directory
# Assumes build context is simulation/
COPY . /app

# Install dependencies using uv
RUN uv sync --frozen

# Set the entrypoint to run the simulation script
ENTRYPOINT ["uv", "run", "simulation.py"]

# Default arguments
CMD ["-a", "aliases.yaml", "-s", "press-sim.yaml", "-c", "synnax"]
