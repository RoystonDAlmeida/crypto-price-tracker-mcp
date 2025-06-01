# ---- Builder Stage ----

# This stage will be used to build dependencies and the project.
# It will include build tools like uv and caches, which won't go into the final image.
FROM python:3.12-slim AS builder

# Set environment variables for Python for better behavior in containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Upgrade pip and install uv efficiently, without caching for pip itself.
RUN python -m pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

# Copy the project definition file first to leverage Docker layer caching.
# Dependencies will only be re-installed if pyproject.toml changes.
COPY pyproject.toml ./

# Copy the application source code. This is needed if `uv pip install .`
# builds the project from the current directory.
COPY src/ ./src/

# Install the project and its dependencies specified in pyproject.toml
# Using --system to install into the system Python, common in Docker.
# After installation, clean up the uv cache to reduce the size of this layer's contribution.
RUN uv pip install --system . && \
    rm -rf /root/.cache/uv

# ---- Runtime Stage ----
# This stage will be the final, lean image.

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only the installed Python packages from the builder stage's site-packages.
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/

# Copy any executables (e.g., console scripts from dependencies) from the builder stage.
# This will include our 'crypto-tracker-server' script.
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Command to run the MCP server using the server.py entry point
# FastMCP handles stdio transport internally
CMD ["crypto-price-tracker-server", "--transport", "stdio"]