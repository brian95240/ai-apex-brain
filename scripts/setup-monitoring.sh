#!/bin/bash
# Setup automated monitoring for A.I. Apex Brain

echo "📊 Setting up A.I. Apex Brain monitoring..."

# Create log directory
mkdir -p /var/log/apex-brain

# Setup log rotation
cat > /etc/logrotate.d/apex-brain << 'LOGROTATE'
/var/log/apex-brain/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
LOGROTATE

# Setup cron jobs for monitoring
CRON_JOBS="
# A.I. Apex Brain Monitoring
# Health check every 5 minutes
*/5 * * * * /root/apex-brain-deployment/scripts/health-check.sh >> /var/log/apex-brain/health.log 2>&1

# Resource monitoring every 10 minutes
*/10 * * * * /root/apex-brain-deployment/scripts/monitor-resources.sh

# Auto-scaling check every 15 minutes
*/15 * * * * /root/apex-brain-deployment/scripts/scale-system.sh >> /var/log/apex-brain/scaling.log 2>&1

# Daily backup at 2 AM
0 2 * * * /root/apex-brain-deployment/scripts/backup-system.sh >> /var/log/apex-brain/backup.log 2>&1

# Weekly update check on Sundays at 3 AM
0 3 * * 0 /root/apex-brain-deployment/scripts/update-system.sh >> /var/log/apex-brain/update.log 2>&1
"

# Install cron jobs
echo "$CRON_JOBS" | crontab -

# Install mail if not present (for alerts)
if ! command -v mail &> /dev/null; then
    apt update && apt install -y mailutils
fi

echo "✅ Monitoring setup completed!"
echo "📋 Configured monitoring tasks:"
echo "   - Health checks every 5 minutes"
echo "   - Resource monitoring every 10 minutes" 
echo "   - Auto-scaling every 15 minutes"
echo "   - Daily backups at 2 AM"
echo "   - Weekly updates on Sundays at 3 AM"
echo ""
echo "📁 Logs location: /var/log/apex-brain/"
echo "🔍 View cron jobs: crontab -l"
