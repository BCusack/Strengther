# Use Python 3.13 slim image as base
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Installing separately from its dependencies allows optimal layer caching
ADD . /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create UV cache directory with proper permissions and change ownership of app directory
RUN mkdir -p /home/appuser/.cache/uv && \
    chown -R appuser:appuser /home/appuser && \
    chown -R appuser:appuser /app

# Switch to appuser before creating the virtual environment
USER appuser

# Create virtual environment in user's home directory
ENV UV_PROJECT_ENVIRONMENT=/home/appuser/.venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/home/appuser/.venv/bin:$PATH"

ENV PYTHONPATH=/app

# Expose port for FastAPI
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Default command to run the application
CMD ["uv", "run", "uvicorn", "strengther.app:app", "--host", "0.0.0.0", "--port", "8000"]
