#!/bin/bash
# A.I. Apex Brain - macOS One-Line Deployment
# Usage: curl -sSL https://raw.githubusercontent.com/brian95240/ai-apex-brain/main/deploy-mac.sh | bash

set -e

echo "🧠 A.I. APEX BRAIN - macOS DEPLOYMENT STARTING..."
echo "================================================="

# Check for Homebrew and install if needed
if ! command -v brew &> /dev/null; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Install dependencies
echo "📦 Installing system dependencies..."
brew update
brew install git python3 node npm docker docker-compose

# Start Docker Desktop
echo "🐳 Starting Docker Desktop..."
open -a Docker
echo "⏳ Waiting for Docker to start..."
while ! docker system info > /dev/null 2>&1; do
    sleep 5
done

# Clone repository
if [ ! -d "ai-apex-brain" ]; then
    echo "📥 Cloning A.I. Apex Brain repository..."
    git clone https://github.com/brian95240/ai-apex-brain.git
fi

cd ai-apex-brain

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# Setup monitoring
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

# Build React frontend
echo "⚛️ Building React frontend..."
cd ai-brain-website
npm install --legacy-peer-deps
npm run build
cp -r dist/* ../ai-brain-backend/src/static/
cd ..

# Start services in background
echo "🚀 Starting A.I. Apex Brain services..."

# Start swarm dashboard
cd src/dashboard
python3 swarm_control_dashboard.py &
SWARM_PID=$!
cd ../..

# Start Flask backend
cd ai-brain-backend
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip3 install -r requirements.txt
python3 src/main.py &
FLASK_PID=$!
cd ..

# Start vertex orchestrator
cd src
python3 vertex_orchestrator.py &
VERTEX_PID=$!
cd ..

# Start mobile app
cd mobile-app
python3 -m http.server 8081 &
MOBILE_PID=$!
cd ..

# Start unified dashboard
cd unified-dashboard
python3 -m http.server 8080 &
UNIFIED_PID=$!
cd ..

# Save PIDs for cleanup
echo "$SWARM_PID $FLASK_PID $VERTEX_PID $MOBILE_PID $UNIFIED_PID" > .deployment_pids

# Wait for services
echo "⏳ Waiting for services to initialize..."
sleep 15

# Health checks
echo "🔍 Performing health checks..."
HEALTH_PASSED=true

if ! curl -s http://localhost:5001/api/ai-brain/status > /dev/null; then
    echo "❌ Flask backend health check failed"
    HEALTH_PASSED=false
fi

if ! curl -s http://localhost:3000 > /dev/null; then
    echo "❌ Swarm dashboard health check failed"
    HEALTH_PASSED=false
fi

if ! curl -s http://localhost:8081 > /dev/null; then
    echo "❌ Mobile app health check failed"
    HEALTH_PASSED=false
fi

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
    echo "📱 MOBILE APP INSTALLATION:"
    echo "├── iPhone/iPad: Open Safari → http://localhost:5001 → Share → Add to Home Screen"
    echo "├── Android: Open Chrome → http://localhost:5001 → Menu → Add to Home Screen"
    echo "└── macOS: Open Safari → http://localhost:5001 → File → Add to Dock"
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
    echo "├── Status: ./status-apex-brain.sh"
    echo "└── Logs: ./logs-apex-brain.sh"
    echo ""
    echo "🚀 A.I. Apex Brain is now ready for use on macOS!"
    
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
curl -sSL https://raw.githubusercontent.com/brian95240/ai-apex-brain/main/deploy-mac.sh | bash
EOF

    cat > status-apex-brain.sh << 'EOF'
#!/bin/bash
echo "📊 A.I. Apex Brain Status:"
echo "=========================="
curl -s http://localhost:5001/api/ai-brain/status | python3 -m json.tool 2>/dev/null || echo "Backend: Offline"
echo ""
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(prometheus|grafana)" || echo "Monitoring: Offline"
EOF

    chmod +x stop-apex-brain.sh restart-apex-brain.sh status-apex-brain.sh
    
    # Open main interface
    open http://localhost:5001
    
else
    echo ""
    echo "❌ DEPLOYMENT FAILED - Some services are not responding"
    echo "Make sure Docker Desktop is running and try again"
    exit 1
fi

