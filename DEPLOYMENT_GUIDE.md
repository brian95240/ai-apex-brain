# Advanced A.I. 2nd Brain - Quick Deployment Guide

## Prerequisites

- Python 3.11+
- Docker 20.10+
- 8GB+ RAM
- 20GB+ free disk space
- Hetzner Cloud account (for production)

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/brian95240/ai-apex-brain.git
cd ai-apex-brain
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp apex_brain_env.example apex-brain.env
# Edit apex-brain.env with your configuration
```

### 4. Run Tests
```bash
cd tests
python test_comprehensive.py
```

### 5. Start Dashboard
```bash
cd src/dashboard
python swarm_control_dashboard.py
```

### 6. Access Dashboard
Open http://localhost:3000 in your browser

## Production Deployment

### 1. Set Environment Variables
```bash
export HETZNER_TOKEN="your-hetzner-token"
export NEON_DATABASE_URL="your-neon-db-url"
```

### 2. Run Deployment Script
```bash
cd scripts
python deploy_production.py
```

### 3. Monitor Deployment
- Dashboard: http://your-server-ip:3000
- Grafana: http://your-server-ip:3001
- Prometheus: http://your-server-ip:9090

## Key Features

✅ **42 Optimized Algorithms** - Predictive, ML, Causal, Recursive  
✅ **Vertex-Level Orchestration** - Dynamic resource allocation  
✅ **Lazy-Loading Engine** - Intelligent algorithm caching  
✅ **Granular Swarm Control** - Real-time cost prediction  
✅ **Comprehensive Monitoring** - Prometheus + Grafana  
✅ **100% Test Coverage** - All components validated  

## Support

- Documentation: `docs/ADVANCED_AI_BRAIN_DOCUMENTATION.md`
- Issues: https://github.com/brian95240/ai-apex-brain/issues
- Repository: https://github.com/brian95240/ai-apex-brain

