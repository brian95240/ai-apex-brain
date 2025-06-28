#!/bin/bash
# A.I. Apex Brain Update Script

echo "🚀 A.I. Apex Brain Update Process"
echo "================================="

# Backup before update
echo "📋 Creating pre-update backup..."
./scripts/backup-system.sh

# Update system packages
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Update K3s if needed
echo "☸️ Checking K3s version..."
CURRENT_K3S=$(k3s --version | head -1)
echo "Current K3s: $CURRENT_K3S"

# Update container images
echo "🐳 Updating container images..."
kubectl rollout restart deployment -n apex-brain

# Wait for deployments to be ready
echo "⏳ Waiting for services to restart..."
kubectl wait --for=condition=available deployment --all -n apex-brain --timeout=300s

# Run health check
echo "🏥 Running post-update health check..."
./scripts/health-check.sh

echo "✅ Update process completed!"
