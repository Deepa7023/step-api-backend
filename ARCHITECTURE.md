# Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  (Web App, Mobile App, cURL, Python Script, etc.)          │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/HTTPS
                     │ POST /analyze
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer                           │
│              (NGINX, ALB, Cloud LB, etc.)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┬──────────────┐
        ▼                         ▼              ▼
┌──────────────┐          ┌──────────────┐  ┌──────────────┐
│   API        │          │   API        │  │   API        │
│   Instance 1 │          │   Instance 2 │  │   Instance N │
│              │          │              │  │              │
│   FastAPI    │          │   FastAPI    │  │   FastAPI    │
│   Container  │          │   Container  │  │   Container  │
└──────┬───────┘          └──────┬───────┘  └──────┬───────┘
       │                         │                  │
       └─────────────┬───────────┘──────────────────┘
                     ▼
            ┌─────────────────┐
            │  STEP Processor │
            │      (OCCT)     │
            └─────────────────┘
```

## Component Architecture

### 1. API Layer (FastAPI)

**Responsibilities:**
- HTTP request handling
- File upload management
- Input validation
- Response formatting
- Error handling
- API documentation (Swagger/OpenAPI)

**Endpoints:**
- `GET /` - Root/welcome
- `GET /health` - Health check
- `POST /analyze` - Full analysis
- `POST /analyze/geometry` - Geometry only
- `POST /analyze/topology` - Topology only
- `POST /validate` - Validation only

### 2. Processing Layer (STEP Processor)

**Responsibilities:**
- STEP file reading
- Geometric calculations
- Topology extraction
- Validation checks
- Assembly structure analysis

**Key Functions:**
- `_read_step_file()` - Parse STEP format
- `_extract_geometric_properties()` - Calculate volume, area, bbox
- `_extract_topology_info()` - Count elements
- `_validate_shape()` - Quality checks
- `_extract_assembly_structure()` - Part metadata

### 3. OCCT Layer (Open CASCADE)

**Components Used:**
- `STEPControl_Reader` - STEP file parsing
- `BRepGProp` - Geometric property calculations
- `TopExp_Explorer` - Topology traversal
- `BRepCheck_Analyzer` - Shape validation
- `STEPCAFControl_Reader` - Assembly metadata

## Data Flow

```
1. Client Upload
   ↓
2. FastAPI receives file
   ↓
3. Save to temporary file
   ↓
4. STEPProcessor.analyze_file()
   ↓
5. OCCT reads and parses STEP
   ↓
6. Extract data in parallel:
   ├─ Geometric properties
   ├─ Topology information
   ├─ Validation results
   └─ Assembly structure
   ↓
7. Aggregate results
   ↓
8. Return JSON response
   ↓
9. Clean up temp file
```

## Technology Stack

### Backend
- **Language**: Python 3.10+
- **Framework**: FastAPI 0.109+
- **Server**: Uvicorn (ASGI)
- **CAD Library**: pythonocc-core 7.7.2
- **Core Engine**: Open CASCADE Technology (OCCT)

### Containerization
- **Container**: Docker
- **Base Image**: condaforge/miniforge3
- **Orchestration**: Docker Compose / Kubernetes

### Dependencies
```
fastapi==0.109.0          # Web framework
uvicorn[standard]==0.27.0 # ASGI server
python-multipart==0.0.6   # File upload support
pythonocc-core==7.7.2     # CAD processing
pydantic==2.5.3           # Data validation
python-dotenv==1.0.0      # Environment config
```

## Request/Response Flow

### Request
```http
POST /analyze HTTP/1.1
Host: api.example.com
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="part.step"
Content-Type: application/step

ISO-10303-21;
HEADER;
...
------WebKitFormBoundary--
```

### Response
```json
{
  "file_info": {...},
  "metadata": {...},
  "geometry": {
    "volume": {...},
    "surface_area": {...},
    "bounding_box": {...},
    "center_of_mass": {...}
  },
  "topology": {
    "solids": 1,
    "faces": 6,
    "edges": 12,
    "vertices": 8
  },
  "validation": {
    "is_valid": true,
    "issues": []
  },
  "assembly": {...}
}
```

## Error Handling

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Validation     │──── Invalid file type ──→ 400 Bad Request
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  File Upload    │──── Upload failed ──→ 500 Internal Error
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  STEP Reading   │──── Parse error ──→ 500 Internal Error
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Processing     │──── Processing error ──→ 500 Internal Error
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Response       │──── Success ──→ 200 OK
└─────────────────┘
```

## Performance Characteristics

### File Size Handling
- **Small files (<1MB)**: < 1 second
- **Medium files (1-10MB)**: 1-5 seconds
- **Large files (10-100MB)**: 5-30 seconds
- **Very large files (>100MB)**: 30+ seconds

### Memory Usage
- **Base**: ~500MB (OCCT libraries)
- **Per request**: Varies with file complexity
- **Peak**: Can reach 2-4GB for complex assemblies

### Concurrency
- FastAPI handles concurrent requests efficiently
- Recommend 2-4 workers per CPU core
- Consider request queuing for very large files

## Scaling Strategies

### Horizontal Scaling
```
┌──────────────┐
│ Load Balancer│
└──────┬───────┘
       │
   ┌───┴───┬───────┬───────┐
   ▼       ▼       ▼       ▼
┌────┐  ┌────┐  ┌────┐  ┌────┐
│ W1 │  │ W2 │  │ W3 │  │ W4 │
└────┘  └────┘  └────┘  └────┘
```

### Vertical Scaling
- Increase CPU: Faster processing
- Increase RAM: Handle larger files
- Increase storage: More temp space

### Optimization Techniques
1. **Caching**: Cache results for identical files (hash-based)
2. **Async Processing**: Queue long-running jobs
3. **Streaming**: Process large files in chunks
4. **CDN**: Serve static API docs via CDN

## Security Considerations

### Input Validation
- File type checking (.step, .stp only)
- File size limits (configurable)
- Sanitize filenames
- Validate file structure before processing

### Resource Protection
- Request rate limiting
- Timeout limits
- Memory limits per request
- Temporary file cleanup

### Network Security
- HTTPS only in production
- CORS configuration
- API key authentication (optional)
- IP whitelisting (optional)

## Monitoring & Observability

### Health Checks
```python
GET /health
{
  "status": "healthy",
  "occt_available": true,
  "uptime_seconds": 3600
}
```

### Metrics to Monitor
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (%)
- File processing time
- Memory usage
- CPU usage
- Disk I/O

### Logging
```
INFO: Processing file: part.step (45632 bytes)
INFO: Found 1 roots in STEP file
INFO: Calculated volume: 125000.0 cubic_units
INFO: Request completed in 2.3s
```

## Future Enhancements

### Phase 1 (Current)
✅ Basic STEP file analysis
✅ Geometric properties
✅ Topology information
✅ Validation
✅ Docker deployment

### Phase 2
- [ ] Support for IGES, BREP formats
- [ ] Async processing for large files
- [ ] WebSocket progress updates
- [ ] Result caching layer

### Phase 3
- [ ] Authentication & authorization
- [ ] Rate limiting
- [ ] Batch processing
- [ ] Cloud storage integration (S3, Azure Blob)

### Phase 4
- [ ] ML-based quality prediction
- [ ] Advanced assembly analysis
- [ ] CAD format conversion
- [ ] Visualization endpoints
