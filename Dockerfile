FROM python:3.12-slim

LABEL maintainer="NanoHA"
LABEL description="NanoHA managed hosting — agent tools + health API"

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY pyproject.toml ./
RUN pip install --no-cache-dir httpx websockets

# Copy application
COPY tools/ ./tools/
COPY bridge/ ./bridge/
COPY plugins/ ./plugins/
COPY integrations/ ./integrations/
COPY config/ ./config/
COPY hosting/ ./hosting/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "hosting.server"]
