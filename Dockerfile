FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files and database
COPY . .

# Expose ports for Hugging Face (7860), Render/Railway/Cloud Run (8000/PORT)
EXPOSE 7860
EXPOSE 8000

ENV HOST=0.0.0.0
ENV ENVIRONMENT=production
ENV DATABASE_PATH=dawaai.db

# Launch server dynamically on the port specified by the cloud provider
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
