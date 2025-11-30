# Production Deployment Guide

## 🚀 Deployment Options

POSIVA Analytics Platform supports multiple deployment strategies:

1. **Docker Compose** - Quick local/cloud deployment
2. **Kubernetes** - Enterprise-scale orchestration
3. **Cloud Platforms** - AWS, GCP, Azure
4. **Bare Metal** - Direct server installation

---

## 1. Docker Compose Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ disk space

### Quick Start
```bash
# Clone repository
git clone https://github.com/yourorg/posiva_data_analytics.git
cd posiva_data_analytics

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f dashboard
```

### Access Points
- **Dashboard**: http://localhost:8501
- **MLflow**: http://localhost:5000
- **Grafana**: http://localhost:3000 (admin/password from .env)
- **Prometheus**: http://localhost:9090

### Stop Services
```bash
docker-compose -f docker-compose.prod.yml down
```

---

## 2. Kubernetes Deployment

### Prerequisites
- Kubernetes cluster 1.24+
- kubectl configured
- Helm 3.0+ (optional)
- Storage class available

### Deploy to Kubernetes
```bash
# Create namespace
kubectl create namespace production

# Apply configurations
kubectl apply -f deployment/kubernetes/deployment.yaml

# Check deployment
kubectl get pods -n production
kubectl get svc -n production

# Get service URL
kubectl get svc posiva-analytics-service -n production
```

### Scale Deployment
```bash
# Manual scaling
kubectl scale deployment posiva-analytics -n production --replicas=5

# Auto-scaling is configured via HPA (2-10 replicas)
kubectl get hpa -n production
```

### Update Deployment
```bash
# Update image
kubectl set image deployment/posiva-analytics \
  dashboard=posiva-analytics:v2.0.0 \
  -n production

# Rolling update
kubectl rollout status deployment/posiva-analytics -n production

# Rollback if needed
kubectl rollout undo deployment/posiva-analytics -n production
```

---

## 3. AWS Deployment

### Option A: ECS Fargate
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -t posiva-analytics .
docker tag posiva-analytics:latest <account>.dkr.ecr.us-east-1.amazonaws.com/posiva-analytics:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/posiva-analytics:latest

# Deploy to ECS (using AWS CLI or Console)
aws ecs create-service \
  --cluster posiva-cluster \
  --service-name posiva-analytics \
  --task-definition posiva-analytics:1 \
  --desired-count 3 \
  --launch-type FARGATE
```

### Option B: EKS (Kubernetes)
```bash
# Create EKS cluster
eksctl create cluster \
  --name posiva-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.large \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5

# Deploy application
kubectl apply -f deployment/kubernetes/deployment.yaml
```

### Option C: EC2 with Docker Compose
```bash
# SSH to EC2 instance
ssh -i key.pem ec2-user@<instance-ip>

# Install Docker and Docker Compose
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Clone and deploy
git clone <repo>
cd posiva_data_analytics
docker-compose -f docker-compose.prod.yml up -d
```

---

## 4. GCP Deployment

### Cloud Run (Serverless)
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/<project-id>/posiva-analytics
gcloud run deploy posiva-analytics \
  --image gcr.io/<project-id>/posiva-analytics \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

### GKE (Kubernetes)
```bash
# Create GKE cluster
gcloud container clusters create posiva-cluster \
  --num-nodes=3 \
  --machine-type=n1-standard-2 \
  --region=us-central1

# Get credentials
gcloud container clusters get-credentials posiva-cluster --region us-central1

# Deploy
kubectl apply -f deployment/kubernetes/deployment.yaml
```

---

## 5. Azure Deployment

### Container Instances
```bash
# Create resource group
az group create --name posiva-rg --location eastus

# Deploy container
az container create \
  --resource-group posiva-rg \
  --name posiva-analytics \
  --image <registry>/posiva-analytics:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8501 \
  --dns-name-label posiva-analytics
```

### AKS (Kubernetes)
```bash
# Create AKS cluster
az aks create \
  --resource-group posiva-rg \
  --name posiva-cluster \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3 \
  --generate-ssh-keys

# Connect
az aks get-credentials --resource-group posiva-rg --name posiva-cluster

# Deploy
kubectl apply -f deployment/kubernetes/deployment.yaml
```

---

## 6. Monitoring and Observability

### Prometheus + Grafana
Already configured in docker-compose.prod.yml

**Key Metrics Monitored:**
- Request rates and latency
- Error rates
- Resource utilization (CPU, Memory)
- Database connections
- Model prediction latency
- Data quality scores

### Access Grafana
1. Open http://localhost:3000
2. Login with credentials from .env
3. Pre-configured dashboards available

### Custom Alerts
Edit `deployment/prometheus/alerts/` to add custom alerting rules.

---

## 7. CI/CD Pipeline

### GitHub Actions (Automated)
Configured in `.github/workflows/ci-cd.yml`

**Pipeline Stages:**
1. **Test** - Run unit tests, linting, type checking
2. **Build** - Build Docker image
3. **Push** - Push to container registry
4. **Deploy** - Deploy to production

### Required Secrets
Set in GitHub repository settings:
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `AWS_ACCESS_KEY_ID` (if using AWS)
- `AWS_SECRET_ACCESS_KEY`
- `KUBECONFIG` (if using Kubernetes)

---

## 8. Security Best Practices

### Environment Variables
```bash
# Never commit .env file
# Use secrets management:
- AWS Secrets Manager
- Azure Key Vault
- GCP Secret Manager
- Kubernetes Secrets
```

### SSL/TLS
```bash
# Generate self-signed certificate (dev only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deployment/nginx/ssl/key.pem \
  -out deployment/nginx/ssl/cert.pem

# Production: Use Let's Encrypt or cloud provider certificates
```

### Database Security
- Use strong passwords
- Enable SSL connections
- Restrict network access
- Regular backups

---

## 9. Backup and Recovery

### Database Backups
```bash
# PostgreSQL backup
docker exec posiva-postgres pg_dump -U posiva_user posiva > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i posiva-postgres psql -U posiva_user posiva < backup.sql
```

### Model Backups
```bash
# Backup models directory
tar -czf models_backup_$(date +%Y%m%d).tar.gz models/

# Restore
tar -xzf models_backup.tar.gz
```

---

## 10. Scaling Strategies

### Horizontal Scaling
```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml up -d --scale dashboard=5

# Kubernetes (automated via HPA)
kubectl get hpa -n production
```

### Vertical Scaling
```yaml
# Update resource limits in deployment.yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "4000m"
```

### Database Scaling
- Read replicas for PostgreSQL
- Redis cluster for caching
- Connection pooling (PgBouncer)

---

## 11. Troubleshooting

### Check Logs
```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml logs -f dashboard

# Kubernetes
kubectl logs -f deployment/posiva-analytics -n production
```

### Health Checks
```bash
# Dashboard health
curl http://localhost:8501/_stcore/health

# Nginx health
curl http://localhost/health
```

### Common Issues
1. **Out of memory**: Increase container memory limits
2. **Slow dashboard**: Enable Redis caching
3. **Database connection errors**: Check network and credentials
4. **SSL errors**: Verify certificate configuration

---

## 12. Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database backups scheduled
- [ ] Monitoring alerts configured
- [ ] Log aggregation setup
- [ ] Security scanning enabled
- [ ] Resource limits set
- [ ] Auto-scaling configured
- [ ] Disaster recovery plan documented
- [ ] Load testing completed

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourorg/posiva_data_analytics/issues
- Documentation: /docs
- Email: support@yourorg.com
