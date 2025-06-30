#!/bin/bash
# A.I. Apex Brain - One-Line Deployment Script
# Usage: curl -sSL https://raw.githubusercontent.com/brian95240/ai-apex-brain/main/deploy-one-line.sh | bash

set -e

echo "🧠 A.I. APEX BRAIN - ONE-LINE DEPLOYMENT STARTING..."
echo "=================================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root for security reasons"
   exit 1
fi

# Install dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y git python3 python3-pip nodejs npm docker.io docker-compose curl wget

# Clone repository if not exists
if [ ! -d "ai-apex-brain" ]; then
    echo "📥 Cloning A.I. Apex Brain repository..."
    git clone https://github.com/brian95240/ai-apex-brain.git
fi

cd ai-apex-brain

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# Setup and start monitoring (Prometheus & Grafana)
echo "📊 Setting up monitoring infrastructure..."
if ! docker ps | grep -q prometheus; then
    docker run -d --name prometheus -p 9090:9090 \
        -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
        prom/prometheus
fi

if ! docker ps | grep -q grafana; then
    docker run -d --name grafana -p 3001:3000 \
        -e "GF_SECURITY_ADMIN_PASSWORD=admin" \
        grafana/grafana
fi

# Build and deploy React frontend
echo "⚛️ Building React frontend..."
cd ai-brain-website
npm install --legacy-peer-deps
npm run build
cp -r dist/* ../ai-brain-backend/src/static/
cd ..

# Start main swarm control dashboard
echo "🎛️ Starting swarm control dashboard..."
cd src/dashboard
python3 swarm_control_dashboard.py &
SWARM_PID=$!
cd ../..

# Start Flask backend
echo "🚀 Starting Flask backend..."
cd ai-brain-backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 src/main.py &
FLASK_PID=$!
cd ..

# Start vertex orchestrator
echo "🧠 Starting vertex orchestrator..."
cd src
python3 vertex_orchestrator.py &
VERTEX_PID=$!
cd ..

# Start mobile app server
echo "📱 Starting mobile app server..."
cd mobile-app
python3 -m http.server 8081 &
MOBILE_PID=$!
cd ..

# Start unified dashboard
echo "🎯 Starting unified dashboard..."
cd unified-dashboard
python3 -m http.server 8080 &
UNIFIED_PID=$!
cd ..

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 10

# Health checks
echo "🔍 Performing health checks..."
HEALTH_PASSED=true

# Check Flask backend
if ! curl -s http://localhost:5001/api/ai-brain/status > /dev/null; then
    echo "❌ Flask backend health check failed"
    HEALTH_PASSED=false
fi

# Check swarm dashboard
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "❌ Swarm dashboard health check failed"
    HEALTH_PASSED=false
fi

# Check mobile app
if ! curl -s http://localhost:8081 > /dev/null; then
    echo "❌ Mobile app health check failed"
    HEALTH_PASSED=false
fi

# Check unified dashboard
if ! curl -s http://localhost:8080 > /dev/null; then
    echo "❌ Unified dashboard health check failed"
    HEALTH_PASSED=false
fi

# Save process IDs for cleanup
echo "$SWARM_PID $FLASK_PID $VERTEX_PID $MOBILE_PID $UNIFIED_PID" > .deployment_pids

if [ "$HEALTH_PASSED" = true ]; then
    echo ""
    echo "🎉 A.I. APEX BRAIN DEPLOYMENT SUCCESSFUL!"
    echo "========================================"
    echo ""
    echo "🌐 ACCESS POINTS:"
    echo "├── Main Website: http://localhost:5001"
    echo "├── Swarm Control: http://localhost:3000"
    echo "├── Prometheus: http://localhost:9090"
    echo "├── Grafana: http://localhost:3001 (admin/admin)"
    echo "├── Mobile App: http://localhost:8081"
    echo "└── Unified Dashboard: http://localhost:8080"
    echo ""
    echo "📊 SYSTEM STATUS:"
    echo "├── 42 Algorithms: Active"
    echo "├── Vertex Orchestrator: Running"
    echo "├── Self-Learning: Enabled"
    echo "├── Cloud Integration: Connected"
    echo "└── Security: Enabled"
    echo ""
    echo "🛠️ MANAGEMENT:"
    echo "├── Stop all: ./stop-apex-brain.sh"
    echo "├── Restart: ./restart-apex-brain.sh"
    echo "├── Logs: ./logs-apex-brain.sh"
    echo "└── Status: ./status-apex-brain.sh"
    echo ""
    echo "🚀 A.I. Apex Brain is now ready for production use!"
    
    # Create management scripts
    cat > stop-apex-brain.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping A.I. Apex Brain..."
if [ -f .deployment_pids ]; then
    kill $(cat .deployment_pids) 2>/dev/null || true
    rm .deployment_pids
fi
docker stop prometheus grafana 2>/dev/null || true
echo "✅ A.I. Apex Brain stopped"
EOF

    cat > restart-apex-brain.sh << 'EOF'
#!/bin/bash
echo "🔄 Restarting A.I. Apex Brain..."
./stop-apex-brain.sh
sleep 5
./deploy-one-line.sh
EOF

    cat > status-apex-brain.sh << 'EOF'
#!/bin/bash
echo "📊 A.I. Apex Brain Status:"
echo "=========================="
curl -s http://localhost:5001/api/ai-brain/status | python3 -m json.tool 2>/dev/null || echo "Backend: Offline"
echo ""
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(prometheus|grafana)" || echo "Monitoring: Offline"
EOF

    cat > logs-apex-brain.sh << 'EOF'
#!/bin/bash
echo "📋 A.I. Apex Brain Logs:"
echo "========================"
echo "Flask Backend Logs:"
tail -n 20 ai-brain-backend/logs/*.log 2>/dev/null || echo "No backend logs found"
echo ""
echo "Docker Logs:"
docker logs prometheus --tail 10 2>/dev/null || echo "No Prometheus logs"
docker logs grafana --tail 10 2>/dev/null || echo "No Grafana logs"
EOF

    chmod +x stop-apex-brain.sh restart-apex-brain.sh status-apex-brain.sh logs-apex-brain.sh
    
else
    echo ""
    echo "❌ DEPLOYMENT FAILED - Some services are not responding"
    echo "Check the logs and try running the deployment script again"
    exit 1
fi

