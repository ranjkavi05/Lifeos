FROM python:3.11-slim

WORKDIR /app

# Force unbuffered stdout/stderr for validator
ENV PYTHONUNBUFFERED=1

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose HF Spaces default port
EXPOSE 7860

# Run the FastAPI server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
