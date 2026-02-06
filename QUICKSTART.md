# Quick Start Guide

Get your STEP File Analysis API up and running in minutes!

## Prerequisites

- Docker Desktop installed
- (Optional) Python 3.10+ for testing scripts

## 🚀 30-Second Setup

```bash
# Clone or navigate to the project
cd step-api-backend

# Build and start the API
docker-compose up --build

# API is now running at http://localhost:8000
```

That's it! The API is ready to use.

## ✅ Verify Installation

Open your browser and visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

Or use curl:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "occt_available": true,
  "supported_formats": ["STEP", "STP"]
}
```

## 📤 Test with a STEP File

### Option 1: Using cURL

```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@your_file.step"
```

### Option 2: Using the Test Script

```bash
python test_api.py your_file.step
```

### Option 3: Using the Interactive Docs

1. Visit http://localhost:8000/docs
2. Click on "POST /analyze"
3. Click "Try it out"
4. Upload your STEP file
5. Click "Execute"

### Option 4: Generate Sample Files

```bash
# Install pythonocc-core first (if not using Docker)
conda install -c conda-forge pythonocc-core

# Generate sample files
python generate_samples.py

# Test with generated samples
python test_api.py sample_box.step
```

## 📊 Understanding the Response

The API returns comprehensive data about your STEP file:

```json
{
  "file_info": {
    "file_size_bytes": 45632,
    "original_filename": "part.step"
  },
  "geometry": {
    "volume": {
      "value": 125000.0,
      "unit": "cubic_units"
    },
    "surface_area": {
      "value": 15000.0,
      "unit": "square_units"
    },
    "bounding_box": {
      "min": {"x": 0, "y": 0, "z": 0},
      "max": {"x": 100, "y": 50, "z": 25}
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

## 🎯 Common Use Cases

### 1. Get Only Volume and Surface Area

```bash
curl -X POST "http://localhost:8000/analyze/geometry" \
  -F "file=@part.step"
```

### 2. Count Faces, Edges, Vertices

```bash
curl -X POST "http://localhost:8000/analyze/topology" \
  -F "file=@part.step"
```

### 3. Validate File Quality

```bash
curl -X POST "http://localhost:8000/validate" \
  -F "file=@part.step"
```

### 4. Full Analysis

```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@part.step"
```

## 🔧 Integration Examples

### Python

```python
import requests

with open('part.step', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/analyze', files=files)
    data = response.json()
    
print(f"Volume: {data['geometry']['volume']['value']}")
print(f"Surface Area: {data['geometry']['surface_area']['value']}")
print(f"Faces: {data['topology']['faces']}")
```

### JavaScript/TypeScript

```javascript
const formData = new FormData();
formData.append('file', stepFile);

const response = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log('Volume:', data.geometry.volume.value);
```

### Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('file', fs.createReadStream('part.step'));

const response = await axios.post('http://localhost:8000/analyze', form, {
  headers: form.getHeaders()
});

console.log(response.data);
```

## 🐛 Troubleshooting

### API won't start

```bash
# Check if port 8000 is already in use
lsof -i :8000

# Use a different port
docker-compose down
# Edit docker-compose.yml and change port mapping
docker-compose up
```

### "OCCT not available" error

This means pythonocc-core isn't installed. The Docker image includes it automatically, but for local development:

```bash
conda install -c conda-forge pythonocc-core=7.7.2
```

### File upload fails

- Check file is valid STEP format (.step or .stp)
- Ensure file isn't corrupted
- Check file size isn't too large

### Slow processing

- Large/complex files take longer
- Assembly files with many parts take longer
- Consider using dedicated endpoints for specific data

## 📚 Next Steps

1. **Production Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md) for cloud deployment options
2. **Architecture**: Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
3. **Customize**: Modify endpoints in `app/main.py` for your needs
4. **Scale**: Add load balancing and multiple instances

## 🆘 Getting Help

- Check API documentation: http://localhost:8000/docs
- Review error messages in API response
- Check Docker logs: `docker-compose logs`
- Read README.md for detailed documentation

## 🎉 You're Ready!

Your STEP File Analysis API is now running. Start uploading STEP files and extracting data!

```bash
# View all endpoints
curl http://localhost:8000/docs

# Test with a file
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@your_file.step"
```

Enjoy! 🚀
