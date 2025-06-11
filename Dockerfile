# Use official Python slim Bookworm image
FROM python:3.12-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages and Node.js
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        gnupg \
        ca-certificates \
        lsb-release \
        vim \
        docker.io \
        unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x from NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN apt-get install -y unzip && \
    ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf aws awscliv2.zip

# Verify installations
RUN node -v && npm -v && npx --version && aws --version

# Copy uv and uvx binaries from the official uv image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the MCP Manager CLI from PyPI
RUN pip install --no-cache-dir mcp-manager-cli

# Create the .cache directory for config and runtime files
RUN mkdir -p /app/.cache

# Expose the default daemon port
EXPOSE 4123

# Set environment variable for unbuffered output (useful for logs)
ENV PYTHONUNBUFFERED=1

# By default, run the daemon
CMD ["mcp-manager-daemon"]
