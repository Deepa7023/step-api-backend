# STEP File Analysis API

A FastAPI-based backend service for analyzing STEP CAD files and extracting geometric, topological, and metadata information using Open CASCADE Technology (OCCT).

## Features

✅ **Comprehensive STEP File Analysis**
- Geometric properties (volume, surface area, center of mass, bounding box)
- Topology information (solids, shells, faces, edges, vertices)
- Assembly structure and part metadata
- Quality validation and error checking

✅ **RESTful API**
- Full analysis endpoint
- Dedicated endpoints for geometry, topology, and validation
- Auto-generated API documentation (Swagger/OpenAPI)
- CORS support for web integration

✅ **Production Ready**
- Docker containerization
- Health check endpoints
- Comprehensive error handling
- Logging and monitoring

## Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) Python 3.10+ for local development

### Using Docker (Recommended)

1. **Build and run the container:**

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

2. **Check API health:**

```bash
curl http://localhost:8000/health
```

### API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## API Endpoints

### Health Check

```bash
GET /health
```

Returns API status and OCCT availability.

### Full Analysis

```bash
POST /analyze
Content-Type: multipart/form-data

file: <STEP file>
```

Returns complete analysis including geometry, topology, metadata, and validation.

**Example Response:**
```json
{
  "file_info": {
    "file_size_bytes": 45632,
    "original_filename": "part.step"
  },
  "geometry": {
    "volume": {
      "value": 1234.56,
      "unit": "cubic_units"
    },
    "surface_area": {
      "value": 567.89,
      "unit": "square_units"
    },
    "bounding_box": {
      "min": {"x": 0, "y": 0, "z": 0},
      "max": {"x": 100, "y": 50, "z": 25},
      "dimensions": {
        "length_x": 100,
        "length_y": 50,
        "length_z": 25
      }
    },
    "center_of_mass": {
      "x": 50.0,
      "y": 25.0,
      "z": 12.5
    }
  },
  "topology": {
    "solids": 1,
    "shells": 1,
    "faces": 6,
    "edges": 12,
    "vertices": 8
  },
  "validation": {
    "is_valid": true,
    "is_done": true,
    "issues": []
  },
  "assembly": {
    "is_assembly": false,
    "part_count": 1
  }
}
```

### Geometry Only

```bash
POST /analyze/geometry
Content-Type: multipart/form-data

file: <STEP file>
```

Returns only geometric properties (volume, surface area, bounding box).

### Topology Only

```bash
POST /analyze/topology
Content-Type: multipart/form-data

file: <STEP file>
```

Returns only topology counts.

### Validation

```bash
POST /validate
Content-Type: multipart/form-data

file: <STEP file>
```

Returns validation results and quality metrics.

## Usage Examples

### Using cURL

```bash
# Full analysis
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@your_file.step"

# Geometry only
curl -X POST "http://localhost:8000/analyze/geometry" \
  -F "file=@your_file.step"

# Validation
curl -X POST "http://localhost:8000/validate" \
  -F "file=@your_file.step"
```

### Using Python

```python
import requests

# Analyze a STEP file
with open('part.step', 'rb') as f:
    files = {'file': ('part.step', f, 'application/step')}
    response = requests.post('http://localhost:8000/analyze', files=files)
    
result = response.json()
print(f"Volume: {result['geometry']['volume']['value']}")
print(f"Faces: {result['topology']['faces']}")
```

### Using the Test Script

```bash
python test_api.py path/to/your/file.step
```

### Using JavaScript/TypeScript

```javascript
const formData = new FormData();
formData.append('file', stepFile);

const response = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Volume:', result.geometry.volume.value);
```

## Development

### Local Development (without Docker)

1. **Create conda environment:**

```bash
conda create -n step-api python=3.10
conda activate step-api
conda install -c conda-forge pythonocc-core=7.7.2
```

2. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

3. **Run the application:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Start the API
docker-compose up -d

# Run test script
python test_api.py path/to/test.step
```

## Deployment

### Docker

```bash
# Build image
docker build -t step-api:latest .

# Run container
docker run -p 8000:8000 step-api:latest
```

### Cloud Deployment

#### AWS ECS/Fargate

1. Push image to ECR:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag step-api:latest <account>.dkr.ecr.us-east-1.amazonaws.com/step-api:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/step-api:latest
```

2. Create ECS task definition and service

#### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/step-api
gcloud run deploy step-api --image gcr.io/PROJECT-ID/step-api --platform managed
```

#### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name step-api \
  --image step-api:latest \
  --dns-name-label step-api \
  --ports 8000
```

### Kubernetes

Example deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: step-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: step-api
  template:
    metadata:
      labels:
        app: step-api
    spec:
      containers:
      - name: step-api
        image: step-api:latest
        ports:
        - containerPort: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: step-api
spec:
  selector:
    app: step-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Configuration

### Environment Variables

- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)
- `LOG_LEVEL`: Logging level (default: INFO)

## Performance Considerations

- **File Size**: The API can handle large STEP files, but processing time increases with complexity
- **Concurrent Requests**: FastAPI handles concurrent requests efficiently
- **Memory**: OCCT operations can be memory-intensive for large assemblies
- **Scaling**: Deploy multiple instances behind a load balancer for high traffic

## Troubleshooting

### "OCCT not available" error

Ensure pythonocc-core is properly installed:
```bash
conda install -c conda-forge pythonocc-core=7.7.2
```

### Invalid STEP file errors

- Verify file is valid STEP format (.step or .stp)
- Check file isn't corrupted
- Ensure file contains valid geometry

### Docker build issues

- Increase Docker memory allocation
- Check conda channel accessibility
- Verify network connectivity

## Technology Stack

- **FastAPI**: Modern, fast web framework
- **pythonocc-core**: Python bindings for Open CASCADE
- **OCCT**: Open CASCADE Technology for CAD processing
- **uvicorn**: ASGI server
- **Docker**: Containerization

## License

This project uses Open CASCADE Technology which is under LGPL 2.1 license.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions:
- Check the API documentation at `/docs`
- Review OCCT documentation
- Open an issue on GitHub

## Roadmap

- [ ] Support for additional CAD formats (IGES, BREP)
- [ ] Async processing for large files
- [ ] WebSocket support for progress updates
- [ ] Cloud storage integration (S3, Azure Blob)
- [ ] Caching layer for repeated analyses
- [ ] Authentication and rate limiting
- [ ] Batch processing endpoint
