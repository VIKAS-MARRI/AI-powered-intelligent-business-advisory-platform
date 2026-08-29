# ── Stage 1: Build ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies globally into a separate directory
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Production ────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy installed Python packages
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user and give ownership of the application
RUN useradd -m -u 1000 ruralbiz \
    && chown -R ruralbiz:ruralbiz /app

# Run application as non-root user
USER ruralbiz

# Render provides the PORT environment variable
EXPOSE 8000

# Seed missing business data before startup and then run the API.
# This keeps the production database populated without relying on local SQLite data.
CMD ["sh", "-c", "python -m app.seed_businesses && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]