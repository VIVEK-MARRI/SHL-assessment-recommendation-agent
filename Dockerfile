# Use a multi-stage build to keep the final image clean and small
# Stage 1: Builder
FROM python:3.11-slim AS builder

# Set environment variables for builder
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install dependencies (use requirements.txt or directly install packages)
# Here we copy the pyproject.toml if using a modern build system, or install directly.
COPY pyproject.toml .

# Since we might be using pip directly with pyproject.toml
RUN pip install --upgrade pip && \
    pip install build && \
    pip install .

# Stage 2: Runtime
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application source code (excluding files in .dockerignore)
COPY . /app/

# Ensure the non-root user owns the /app directory
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose port
EXPOSE 8000

# Start the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
