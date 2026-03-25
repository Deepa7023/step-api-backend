FROM python:3.10-slim

# System packages needed by OCP wheels and FastAPI
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libgl1-mesa-dev libglu1-mesa \
    libxrender1 libsm6 libxext6 \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic==1.10.13 numpy
# Open Cascade Python bindings (prebuilt wheel)
RUN pip install --no-cache-dir OCP==7.7.0

# Copy your code (assumes main.py at repo root)
COPY . /app

EXPOSE 8000

# If your entry file is main.py and the FastAPI app is named "app"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
