FROM python:3.10-slim

# Minimal runtime libs for OCP (OpenCascade) + headless FastAPI
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglu1-mesa \
    libxrender1 \
    libsm6 \
    libxext6 \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic==1.10.13 numpy python-multipart
# OCP = CadQuery’s maintained OCCT Python bindings (imports as `from OCP import ...`)
RUN pip install --no-cache-dir cadquery-ocp==7.9.3.1

COPY . /app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host","0.0.0.0","--port","8000"]
``
