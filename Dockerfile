FROM python:3.12-slim

# Set environment variables for Python for better behavior in containers
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Upgrade pip to ensure it can handle pyproject.toml effectively
# and install uv - a fast Python package installer
RUN python -m pip install --upgrade pip
RUN pip install uv

# Copy the project definition file first to leverage Docker layer caching.
# Dependencies will only be re-installed if pyproject.toml changes.
COPY pyproject.toml ./

# Copy the application source code into the container
COPY src/ ./src/

# Install the project and its dependencies specified in pyproject.toml
# Using --system to install into the system Python, common in Docker.
RUN uv pip install  --system .

# Ensure the server.py is executable
RUN chmod +x src/server.py

# Command to run the MCP server using the server.py entry point
# FastMCP handles stdio transport internally
CMD ["python", "src/server.py", "--transport", "stdio"]