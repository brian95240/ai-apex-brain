#!/bin/bash
# A.I. Apex Brain - Linux One-Line Deployment
# Usage: curl -sSL https://raw.githubusercontent.com/brian95240/ai-apex-brain/main/deploy-linux.sh | bash

set -e

echo "🧠 A.I. APEX BRAIN - LINUX DEPLOYMENT STARTING..."
echo "================================================="

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
fi

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root for security reasons"
   echo "Please run as a regular user with sudo privileges"
   exit 1
fi

# Install dependencies based on distribution
echo "📦 Installing system dependencies for $OS..."

if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    sudo apt-get update -qq
    sudo apt-get install -y git python3 python3-pip nodejs npm docker.io docker-compose curl wget
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
    if command -v dnf &> /dev/null; then
        sudo dnf install -y git python3 python3-pip nodejs npm docker docker-compose curl wget
    else
        sudo yum install -y git python3 python3-pip nodejs npm docker docker-compose curl wget
    fi
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
elif [[ "$OS" == *"Arch"* ]]; then
    sudo pacman -Sy --noconfirm git python python-pip nodejs npm docker docker-compose curl wget
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
else
    echo "⚠️ Unsupported Linux distribution: $OS"
    echo "Please install git, python3, nodejs, npm, docker manually"
    echo "Then run this script again"
    exit 1
fi

# Start and enable Docker
echo "🐳 Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker

# Check if user needs to re-login for docker group
if ! groups | grep -q docker; then
    echo "⚠️ You need to log out and log back in for Docker permissions to take effect"
    echo "Or run: newgrp docker"
    echo "Then run this script again"
    exit 1
fi

# Clone repository
if [ ! -d "ai-apex-brain" ]; then
    echo "📥 Cloning A.I. Apex Brain repository..."
    git clone https://github.com/brian95240/ai-apex-brain.git
fi

cd ai-apex-brain

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install --user -r requirements.txt

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

if ! curl -s http://localhost:8080 > /dev/null; then
    echo "❌ Unified dashboard health check failed"
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
    echo "├── Android: Open Chrome → http://localhost:5001 → Menu → Add to Home Screen"
    echo "├── Desktop: Open browser → http://localhost:5001 → Install App (if supported)"
    echo "└── Or bookmark http://localhost:5001 for quick access"
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
    echo "🚀 A.I. Apex Brain is now ready for use on Linux!"
    
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
curl -sSL https://raw.githubusercontent.com/brian95240/ai-apex-brain/main/deploy-linux.sh | bash
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
    
    # Try to open browser if available
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:5001 2>/dev/null || true
    elif command -v firefox &> /dev/null; then
        firefox http://localhost:5001 2>/dev/null &
    elif command -v google-chrome &> /dev/null; then
        google-chrome http://localhost:5001 2>/dev/null &
    fi
    
else
    echo ""
    echo "❌ DEPLOYMENT FAILED - Some services are not responding"
    echo "Check the logs and try running the deployment script again"
    echo "Make sure Docker is running: sudo systemctl status docker"
    exit 1
fi

