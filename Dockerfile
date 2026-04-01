FROM python:3.10-slim

# Minimal runtime libs for OpenCascade (OCP) + headless FastAPI
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglu1-mesa \
    libxrender1 \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better Docker cache usage
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy your app
COPY . /app

EXPOSE 10000
CMD ["sh","-c","uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
