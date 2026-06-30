FROM python:3.12-slim

WORKDIR /app

# Install system deps for potential C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir -e .

EXPOSE 8765

CMD ["uvicorn", "ai_embedded_company.api.app:app", "--host", "0.0.0.0", "--port", "8765"]
