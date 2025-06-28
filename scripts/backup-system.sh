#!/bin/bash
# A.I. Apex Brain Backup Script

BACKUP_DIR="/root/apex-brain-backups"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="apex-brain-backup-$DATE"

echo "🗄️ Starting A.I. Apex Brain Backup - $DATE"
echo "============================================"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
echo "📊 Backing up PostgreSQL database..."
kubectl exec deployment/postgresql-age -n apex-brain -- \
    pg_dump -U apex apex_brain > "$BACKUP_DIR/$BACKUP_NAME-database.sql"

if [ $? -eq 0 ]; then
    echo "✅ Database backup completed"
else
    echo "❌ Database backup failed"
fi

# Configuration backup
echo "⚙️ Backing up Kubernetes configurations..."
kubectl get all -n apex-brain -o yaml > "$BACKUP_DIR/$BACKUP_NAME-k8s-config.yaml"
kubectl get configmaps -n apex-brain -o yaml > "$BACKUP_DIR/$BACKUP_NAME-configmaps.yaml"
kubectl get secrets -n apex-brain -o yaml > "$BACKUP_DIR/$BACKUP_NAME-secrets.yaml"

# System configuration backup
echo "🔧 Backing up system configurations..."
cp -r /etc/rancher/k3s/ "$BACKUP_DIR/$BACKUP_NAME-k3s-config/" 2>/dev/null || echo "K3s config not found"

# Create compressed archive
echo "📦 Creating compressed backup archive..."
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" $BACKUP_NAME-*
rm -rf $BACKUP_NAME-*

# Cleanup old backups (keep last 7 days)
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR" -name "apex-brain-backup-*.tar.gz" -mtime +7 -delete

BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -f1)
echo "✅ Backup completed: $BACKUP_NAME.tar.gz ($BACKUP_SIZE)"
echo "📁 Location: $BACKUP_DIR/$BACKUP_NAME.tar.gz"

# Optional: Upload to cloud storage
if [ ! -z "$AWS_S3_BUCKET" ]; then
    echo "☁️ Uploading to S3..."
    aws s3 cp "$BACKUP_DIR/$BACKUP_NAME.tar.gz" "s3://$AWS_S3_BUCKET/apex-brain-backups/"
fi
