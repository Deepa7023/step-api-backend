FROM python:3.10-slim

# System libs needed by OCP wheels + FastAPI
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libgl1-mesa-dev libglu1-mesa \
    libxrender1 libsm6 libxext6 \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps (installed via pip)
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic==1.10.13 numpy python-multipart
# Open Cascade Python bindings (prebuilt wheel; no compiling OCCT)
RUN pip install --no-cache-dir OCP==7.7.0

# Copy your app (repo root) into container
COPY . /app

EXPOSE 8000

# Start FastAPI (main.py at repo root; FastAPI app is "app")
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
