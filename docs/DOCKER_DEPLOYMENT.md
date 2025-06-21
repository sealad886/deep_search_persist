# Docker Deployment Guide

This guide provides comprehensive instructions for deploying DeepSearch with Persisting History using Docker - the recommended production method.

## Quick Start

```bash
# 1. Start Ollama (required)
ollama serve

# 2. Pull required models
ollama pull qwen3:14b
ollama pull phi4-reasoning

# 3. Start services
cd docker
docker compose -f docker-compose.persist.yml up --build

# 4. Access WebUI at http://localhost:7860
```

## Prerequisites

### Required
- **Docker** (>= 20.10)
- **Docker Compose** (>= 2.0)
- **Ollama** (running on host machine)

### Optional
- **NVIDIA drivers** (for GPU acceleration)
- **AMD ROCm drivers** (for AMD GPU acceleration)

## Architecture Overview

### Services
- **app-persist**: Main API server (port 8000)
- **gradio-ui**: Web interface (port 7860)
- **mongo**: Session persistence (port 27017)
- **searxng-persist**: Search engine (port 4000)
- **redis**: Caching layer (port 6379)
- **nginx**: Reverse proxy (port 80)
- **backup-persist**: Data backup service

### Data Flow
```
User → WebUI (7860) → API (8000) → MongoDB + SearXNG + Ollama (host)
```

## Configuration

### 1. Ollama Setup (Host Machine)

Ollama **must** run on the host machine, not in Docker:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve

# Pull required models
ollama pull qwen3:14b          # Main reasoning model
ollama pull phi4-reasoning     # Secondary reasoning model
ollama pull nomic-embed-text   # Embedding model (optional)

# Verify models
ollama list
```

### 2. Environment Configuration

Create `docker/.env` file:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_PORT=11434

# MongoDB Configuration
MONGO_URI=mongodb://mongo:27017/deepsearch

# API Configuration
API_PORT=8000
WEBUI_PORT=7860

# Optional: GPU Configuration
NVIDIA_VISIBLE_DEVICES=all
```

### 3. Research Configuration

Copy and customize configuration:

```bash
cp docker/persist-config/research.toml.example research.toml
```

Key settings for Docker deployment:

```toml
[Settings]
use_ollama = true
use_jina = true
with_planning = true
default_model = "qwen3:14b"
reason_model = "phi4-reasoning"

[LocalAI]
ollama_base_url = "${OLLAMA_BASE_URL}"

[API]
searxng_url = "http://searxng:8080"
```

## Deployment Options

### Standard Deployment (CPU)

```bash
cd docker
docker compose -f docker-compose.persist.yml up --build -d
```

### GPU-Accelerated Deployment

#### NVIDIA GPU
```bash
cd docker
docker compose -f docker-compose.persist.yml -f docker-compose.cuda.yml up --build -d
```

#### AMD GPU
```bash
cd docker
docker compose -f docker-compose.persist.yml -f docker-compose.rocm.yml up --build -d
```

### Development Mode
```bash
cd docker
docker compose -f docker-compose.persist.yml -f docker-compose.dev.yml up --build
```

## Service Access

| Service | URL | Purpose |
|---------|-----|---------|
| **Web UI** | http://localhost:7860 | Primary interface |
| **API** | http://localhost:8000 | Research API |
| **Health** | http://localhost:8000/health | Health check |
| **Sessions** | http://localhost:8000/sessions | Session management |
| **SearXNG** | http://localhost:4000 | Search interface |

### WebUI Interface Preview

![WebUI Main Interface](../images/webui-research-tab.png)
*Primary research interface with query input and configuration*

![Session Management](../images/webui-session-management.png)
*Session management with history and controls*

![System Status](../images/webui-system-status.png)
*Real-time system monitoring and Ollama management*

## Monitoring and Validation

### Service Health
```bash
# Check all services
docker compose ps

# Check logs
docker compose logs app-persist
docker compose logs gradio-ui

# Health check
curl http://localhost:8000/health
```

### Ollama Connectivity
```bash
# Test from container
docker exec app-persist curl http://host.docker.internal:11434/api/tags

# Check available models
curl http://localhost:11434/api/tags
```

### Run Test Suite
```bash
# Validate entire deployment
python run_tests.py --docker

# Quick validation
python run_tests.py --validate
```

## Production Considerations

### Security
- Change default API keys in `research.toml`
- Use environment variables for sensitive data
- Configure firewall rules for exposed ports
- Consider using TLS/SSL certificates

### Performance
- Allocate sufficient memory (minimum 8GB recommended)
- Use SSD storage for MongoDB data
- Monitor container resource usage
- Consider scaling search workers

### Backup
```bash
# MongoDB backup
docker exec mongo mongodump --out /data/backup

# Configuration backup
cp research.toml research.toml.backup
```

## Troubleshooting

### Common Issues

#### Ollama Connection Failed
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Verify Docker can reach host
docker run --rm alpine ping host.docker.internal
```

#### MongoDB Connection Issues
```bash
# Check MongoDB logs
docker compose logs mongo

# Verify connectivity
docker exec app-persist ping mongo
```

#### Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep :7860
netstat -tulpn | grep :8000

# Use alternative ports in .env
echo "WEBUI_PORT=7861" >> docker/.env
```

### Log Analysis
```bash
# Real-time logs
docker compose logs -f app-persist

# Container inspection
docker inspect app-persist
docker inspect mongo
```

## Maintenance

### Updates
```bash
# Pull latest images
docker compose pull

# Rebuild services
docker compose up --build -d
```

### Cleanup
```bash
# Remove stopped containers
docker compose down

# Full cleanup (⚠️ removes data)
docker compose down -v
docker system prune -f
```

### Model Management
```bash
# Update models
ollama pull qwen3:14b
ollama pull phi4-reasoning

# Remove old models
ollama rm old-model:version
```

## Performance Tuning

### Resource Allocation
```yaml
# In docker-compose.yml
services:
  app-persist:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

### MongoDB Optimization
```yaml
# MongoDB configuration
mongo:
  command: mongod --wiredTigerCacheSizeGB 2
```

### Concurrent Requests
```toml
# In research.toml
[Settings]
concurrent_limit = 5
request_per_minute = 60
```

## Best Practices

1. **Always start Ollama before Docker services**
2. **Use volume mounts for persistent data**
3. **Monitor resource usage regularly**
4. **Keep configuration files version controlled**
5. **Test deployments with validation suite**
6. **Regular backup of MongoDB data**
7. **Update models and dependencies regularly**

## Support

- **Documentation**: See main README.md
- **Test Validation**: `python run_tests.py --docker`
- **Health Monitoring**: Use `/health` endpoints
- **Logs**: Check container logs for detailed error information