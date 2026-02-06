# Cloud Deployment Examples

This directory contains example deployment configurations for various cloud platforms.

## AWS Elastic Container Service (ECS)

### Task Definition (task-definition.json)

```json
{
  "family": "step-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "step-api",
      "image": "<AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/step-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "PORT",
          "value": "8000"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/step-api",
          "awslogs-region": "<REGION>",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Deployment Commands

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t step-api:latest .
docker tag step-api:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/step-api:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/step-api:latest

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create or update service
aws ecs create-service \
  --cluster my-cluster \
  --service-name step-api \
  --task-definition step-api \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

## Google Cloud Run

```bash
# Build and submit to Cloud Build
gcloud builds submit --tag gcr.io/PROJECT-ID/step-api

# Deploy to Cloud Run
gcloud run deploy step-api \
  --image gcr.io/PROJECT-ID/step-api \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --port 8000 \
  --allow-unauthenticated \
  --max-instances 10
```

### Cloud Run YAML (service.yaml)

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: step-api
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: '10'
        autoscaling.knative.dev/minScale: '1'
    spec:
      containerConcurrency: 80
      containers:
      - image: gcr.io/PROJECT-ID/step-api
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: '1'
            memory: 2Gi
        env:
        - name: PORT
          value: '8000'
```

## Azure Container Instances

```bash
# Create resource group
az group create --name step-api-rg --location eastus

# Create container instance
az container create \
  --resource-group step-api-rg \
  --name step-api \
  --image step-api:latest \
  --cpu 1 \
  --memory 2 \
  --dns-name-label step-api-unique \
  --ports 8000 \
  --environment-variables PORT=8000
```

## Kubernetes

### Deployment (k8s-deployment.yaml)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: step-api
  labels:
    app: step-api
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
        env:
        - name: PORT
          value: "8000"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: step-api
spec:
  selector:
    app: step-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: step-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: step-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Deploy to Kubernetes

```bash
# Apply configuration
kubectl apply -f k8s-deployment.yaml

# Check status
kubectl get deployments
kubectl get services
kubectl get pods

# Get service URL
kubectl get service step-api
```

## DigitalOcean App Platform

### app.yaml

```yaml
name: step-api
services:
- name: api
  github:
    repo: your-username/step-api-backend
    branch: main
  dockerfile_path: Dockerfile
  http_port: 8000
  instance_count: 2
  instance_size_slug: professional-s
  health_check:
    http_path: /health
  routes:
  - path: /
  envs:
  - key: PORT
    value: "8000"
```

## Heroku

### Procfile

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### heroku.yml

```yaml
build:
  docker:
    web: Dockerfile
run:
  web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Deployment

```bash
# Login to Heroku
heroku login
heroku container:login

# Create app
heroku create step-api

# Set stack to container
heroku stack:set container

# Deploy
git push heroku main

# Scale
heroku ps:scale web=2
```

## Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Create service
docker service create \
  --name step-api \
  --replicas 3 \
  --publish 8000:8000 \
  step-api:latest

# Scale service
docker service scale step-api=5

# Update service
docker service update --image step-api:v2 step-api
```

## NGINX Reverse Proxy

### nginx.conf

```nginx
upstream step_api {
    least_conn;
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    listen 80;
    server_name api.example.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://step_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings for large files
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }
}
```
