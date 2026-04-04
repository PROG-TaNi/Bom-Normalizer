FROM python:3.11.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Layer cache: deps first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bom_normalizer/ ./bom_normalizer/
COPY data/ ./data/
COPY inference.py .
COPY openenv.yaml .

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

# MUST bind to 0.0.0.0 for HF Spaces
CMD ["python", "-m", "uvicorn", "bom_normalizer.server:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]

