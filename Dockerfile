FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment defaults (can be overridden at runtime)
ENV GITLAB_AGENT_MODEL=ollama:gpt-4o
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV GITLAB_COMPACT_RESULTS=true
ENV GITLAB_VERIFY_SSL=true
ENV GITLAB_ALLOW_WRITES=false
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
