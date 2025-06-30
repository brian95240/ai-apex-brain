# A.I. Apex Brain - Windows One-Line Deployment
# Usage: iwr -useb https://raw.githubusercontent.com/brian95240/ai-apex-brain/main/deploy-windows.ps1 | iex

Write-Host "🧠 A.I. APEX BRAIN - WINDOWS DEPLOYMENT STARTING..." -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ Please run PowerShell as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Install Chocolatey if not present
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing Chocolatey package manager..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# Install dependencies
Write-Host "📦 Installing system dependencies..." -ForegroundColor Yellow
choco install -y git python nodejs docker-desktop

# Enable WSL2 for Docker (if needed)
if (!(Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux).State -eq "Enabled") {
    Write-Host "🐧 Enabling WSL2 for Docker..." -ForegroundColor Yellow
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart
    Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart
}

# Clone repository
if (!(Test-Path "ai-apex-brain")) {
    Write-Host "📥 Cloning A.I. Apex Brain repository..." -ForegroundColor Yellow
    git clone https://github.com/brian95240/ai-apex-brain.git
}

Set-Location ai-apex-brain

# Install Python dependencies
Write-Host "🐍 Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Start Docker Desktop
Write-Host "🐳 Starting Docker Desktop..." -ForegroundColor Yellow
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
Start-Sleep 30

# Setup monitoring
Write-Host "📊 Setting up monitoring infrastructure..." -ForegroundColor Yellow
docker run -d --name prometheus -p 9090:9090 -v ${PWD}/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
docker run -d --name grafana -p 3001:3000 -e "GF_SECURITY_ADMIN_PASSWORD=admin" grafana/grafana

# Build React frontend
Write-Host "⚛️ Building React frontend..." -ForegroundColor Yellow
Set-Location ai-brain-website
npm install --legacy-peer-deps
npm run build
Copy-Item -Recurse dist/* ../ai-brain-backend/src/static/
Set-Location ..

# Start services
Write-Host "🚀 Starting A.I. Apex Brain services..." -ForegroundColor Yellow

# Start swarm dashboard
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd src/dashboard; python swarm_control_dashboard.py"

# Start Flask backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd ai-brain-backend; python src/main.py"

# Start vertex orchestrator
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd src; python vertex_orchestrator.py"

# Start mobile app
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd mobile-app; python -m http.server 8081"

# Start unified dashboard
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd unified-dashboard; python -m http.server 8080"

# Wait for services
Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep 15

# Health checks
Write-Host "🔍 Performing health checks..." -ForegroundColor Yellow
$healthPassed = $true

try {
    Invoke-WebRequest -Uri "http://localhost:5001/api/ai-brain/status" -UseBasicParsing | Out-Null
} catch {
    Write-Host "❌ Flask backend health check failed" -ForegroundColor Red
    $healthPassed = $false
}

try {
    Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing | Out-Null
} catch {
    Write-Host "❌ Swarm dashboard health check failed" -ForegroundColor Red
    $healthPassed = $false
}

if ($healthPassed) {
    Write-Host ""
    Write-Host "🎉 A.I. APEX BRAIN DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 ACCESS POINTS:" -ForegroundColor Cyan
    Write-Host "├── Main Website: http://localhost:5001" -ForegroundColor White
    Write-Host "├── Swarm Control: http://localhost:3000" -ForegroundColor White
    Write-Host "├── Prometheus: http://localhost:9090" -ForegroundColor White
    Write-Host "├── Grafana: http://localhost:3001 (admin/admin)" -ForegroundColor White
    Write-Host "├── Mobile App: http://localhost:8081" -ForegroundColor White
    Write-Host "└── Unified Dashboard: http://localhost:8080" -ForegroundColor White
    Write-Host ""
    Write-Host "📱 MOBILE APP INSTALLATION:" -ForegroundColor Cyan
    Write-Host "├── Open http://localhost:5001 in your browser" -ForegroundColor White
    Write-Host "├── Click browser menu → 'Install App' or 'Add to Home Screen'" -ForegroundColor White
    Write-Host "└── The A.I. Apex Brain app will install like a native app" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 A.I. Apex Brain is now ready for use on Windows!" -ForegroundColor Green
    
    # Open main interface
    Start-Process "http://localhost:5001"
} else {
    Write-Host ""
    Write-Host "❌ DEPLOYMENT FAILED - Some services are not responding" -ForegroundColor Red
    Write-Host "Please check Docker Desktop is running and try again" -ForegroundColor Yellow
}

