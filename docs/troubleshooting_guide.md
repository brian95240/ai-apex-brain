[troubleshooting_guide.md](https://github.com/user-attachments/files/20959331/troubleshooting_guide.md)[Uploading troub# A.I. Apex Brain - Troubleshooting Guide
## Comprehensive Solutions for Common Issues

---

## 🚨 Quick Diagnosis

### System Health Check

**Run this first when experiencing issues:**

```bash
# SSH to your server
ssh root@YOUR_SERVER_IP

# Quick health assessment
echo "🏥 A.I. Apex Brain Health Check"
echo "=============================="

# Check Kubernetes cluster
kubectl get nodes
kubectl get pods -n apex-brain
kubectl get services -n apex-brain

# Check resource usage
kubectl top pods -n apex-brain 2>/dev/null || echo "Metrics unavailable"

# Check system resources
free -h
df -h
```

### Status Indicators

| Status | Meaning | Action Required |
|--------|---------|----------------|
| 🟢 **All Green** | System operational | Continue normal usage |
| 🟡 **Some Yellow** | Minor issues | Monitor and investigate |
| 🔴 **Any Red** | Critical issues | Immediate action needed |

---

## 🔧 Installation Issues

### Issue: Server Creation Failed

**Symptoms:**
- Hetzner server creation returns error
- "Invalid SSH key" or "Payment method required"

**Diagnosis:**
```bash
# Check Hetzner CLI configuration
hcloud context list
hcloud server list

# Verify SSH key
hcloud ssh-key list
```

**Solutions:**

1. **Invalid API Token:**
   ```bash
   # Regenerate token in Hetzner Console
   export HCLOUD_TOKEN="new_token_here"
   hcloud server list  # Test token
   ```

2. **SSH Key Issues:**
   ```bash
   # Upload SSH key to Hetzner
   hcloud ssh-key create --name "apex-brain-key" --public-key-from-file ~/.ssh/id_ed25519.pub
   ```

3. **Payment Method:**
   - Add valid payment method in Hetzner Console
   - Verify account has sufficient funds

### Issue: Deployment Script Fails

**Symptoms:**
- Script exits with error codes
- Services don't start properly
- Timeouts during deployment

**Diagnosis:**
```bash
# Check deployment logs
./deploy-apex-brain.sh 2>&1 | tee deployment.log

# Check specific component
kubectl describe pod POD_NAME -n apex-brain
kubectl logs POD_NAME -n apex-brain
```

**Solutions:**

1. **Environment Variables Missing:**
   ```bash
   # Verify all required variables
   source apex-brain.env
   echo $HETZNER_TOKEN
   echo $POSTGRES_PASSWORD
   echo $HUGGINGFACE_TOKEN
   ```

2. **Network Issues:**
   ```bash
   # Test connectivity
   curl -I https://get.k3s.io
   curl -I https://github.com
   
   # Check DNS
   nslookup github.com
   ```

3. **Resource Constraints:**
   ```bash
   # Check if server has enough resources
   kubectl describe nodes
   kubectl get events -n apex-brain --sort-by='.lastTimestamp'
   ```

---

## 🐛 Runtime Issues

### Issue: Pods Stuck in Pending State

**Symptoms:**
```bash
kubectl get pods -n apex-brain
# Shows: STATUS = Pending for extended time
```

**Diagnosis:**
```bash
# Check pod details
kubectl describe pod POD_NAME -n apex-brain

# Check events
kubectl get events -n apex-brain --field-selector reason=FailedScheduling
```

**Solutions:**

1. **Insufficient Resources:**
   ```bash
   # Check node resources
   kubectl describe nodes
   kubectl top nodes
   
   # Scale down resource-intensive pods
   kubectl scale deployment llm-engine --replicas=0 -n apex-brain
   kubectl scale deployment llm-engine --replicas=1 -n apex-brain
   ```

2. **Image Pull Issues:**
   ```bash
   # Check image availability
   kubectl describe pod POD_NAME -n apex-brain | grep -i image
   
   # Manual image pull test
   docker pull postgres:15
   docker pull redis:7-alpine
   ```

### Issue: LLM Engine Not Responding

**Symptoms:**
- Chat API returns timeouts
- Model loading failures
- High memory usage

**Diagnosis:**
```bash
# Check LLM engine logs
kubectl logs deployment/llm-engine -n apex-brain --tail=50

# Check resource usage
kubectl top pod -n apex-brain | grep llm-engine

# Test endpoint directly
curl http://localhost:30000/api/v1/system/health
```

**Solutions:**

1. **Model Download Issues:**
   ```bash
   # Check Hugging Face token
   kubectl exec deployment/llm-engine -n apex-brain -- \
     env | grep HUGGING_FACE_HUB_TOKEN
   
   # Restart with lighter model
   kubectl set env deployment/llm-engine -n apex-brain \
     MODEL_NAME="gpt2"
   ```

2. **Memory Issues:**
   ```bash
   # Increase memory limits
   kubectl patch deployment llm-engine -n apex-brain -p '
   {
     "spec": {
       "template": {
         "spec": {
           "containers": [{
             "name": "vllm-server",
             "resources": {
               "limits": {"memory": "6Gi"}
             }
           }]
         }
       }
     }
   }'
   ```

3. **Complete Reset:**
   ```bash
   # Delete and recreate LLM engine
   kubectl delete deployment llm-engine -n apex-brain
   # Re-run deployment script sections for LLM engine
   ```

### Issue: Algorithm Engine Timeout

**Symptoms:**
- Algorithm requests fail with timeouts
- "Algorithm not loaded" errors
- Slow response times

**Diagnosis:**
```bash
# Check algorithm engine status
curl http://localhost:30000/api/v1/algorithms/status

# Check logs
kubectl logs deployment/algorithmic-engine -n apex-brain --tail=100

# Check resource usage
kubectl top pod -n apex-brain | grep algorithmic
```

**Solutions:**

1. **Algorithm Loading Issues:**
   ```bash
   # Restart algorithm engine
   kubectl rollout restart deployment/algorithmic-engine -n apex-brain
   
   # Check if dependencies are installed
   kubectl exec deployment/algorithmic-engine -n apex-brain -- \
     pip list | grep -E "(numpy|pandas|scikit-learn)"
   ```

2. **Performance Optimization:**
   ```bash
   # Scale up algorithm engine
   kubectl scale deployment algorithmic-engine --replicas=2 -n apex-brain
   
   # Check cascade depth configuration
   kubectl get configmap -n apex-brain
   ```

### Issue: Voice Engine Problems

**Symptoms:**
- Voice synthesis fails
- Speech recognition not working
- Audio files not generated

**Diagnosis:**
```bash
# Test voice endpoints
curl -X POST http://localhost:30000/api/v1/voice/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Test", "voice_config": {"voice_profile": "professional"}}'

# Check if audio files exist
kubectl exec deployment/apex-brain-ui -n apex-brain -- \
  ls -la /app/public/audio/
```

**Solutions:**

1. **Missing Audio Dependencies:**
   ```bash
   # Update UI container with audio tools
   kubectl exec deployment/apex-brain-ui -n apex-brain -- \
     apt-get update && apt-get install -y ffmpeg sox
   ```

2. **Voice Model Issues:**
   ```bash
   # Check available voice models
   curl http://localhost:30000/api/v1/voice/profiles
   
   # Reset to default voice
   kubectl set env deployment/apex-brain-ui -n apex-brain \
     DEFAULT_VOICE="professional"
   ```

---

## 🔍 Performance Issues

### Issue: Slow Response Times

**Symptoms:**
- API responses take >5 seconds
- Chat interface feels sluggish
- High CPU usage

**Diagnosis:**
```bash
# Monitor real-time performance
kubectl top pods -n apex-brain --sort-by=cpu
kubectl top pods -n apex-brain --sort-by=memory

# Check request metrics
curl http://localhost:30000/api/v1/system/metrics?timeframe=1h
```

**Solutions:**

1. **Scale Up Services:**
   ```bash
   # Horizontal scaling
   kubectl scale deployment llm-engine --replicas=2 -n apex-brain
   kubectl scale deployment algorithmic-engine --replicas=2 -n apex-brain
   kubectl scale deployment apex-brain-ui --replicas=2 -n apex-brain
   ```

2. **Optimize Algorithm Loading:**
   ```bash
   # Enable more aggressive lazy loading
   kubectl set env deployment/algorithmic-engine -n apex-brain \
     LAZY_LOADING="aggressive" \
     MEMORY_THRESHOLD="0.6"
   ```

3. **Database Optimization:**
   ```bash
   # Tune PostgreSQL
   kubectl exec deployment/postgresql-age -n apex-brain -- \
     psql -U apex -d apex_brain -c "
     ALTER SYSTEM SET shared_buffers = '512MB';
     ALTER SYSTEM SET effective_cache_size = '2GB';
     SELECT pg_reload_conf();"
   ```

### Issue: High Memory Usage

**Symptoms:**
- System running out of memory
- Pods being killed (OOMKilled)
- Swap usage high

**Diagnosis:**
```bash
# Check memory usage
free -h
kubectl top nodes
kubectl top pods -n apex-brain --sort-by=memory

# Check for memory leaks
kubectl logs deployment/llm-engine -n apex-brain | grep -i memory
```

**Solutions:**

1. **Reduce Model Memory:**
   ```bash
   # Enable quantization
   kubectl set env deployment/llm-engine -n apex-brain \
     QUANTIZATION="8bit" \
     GPU_MEMORY_UTILIZATION="0.7"
   ```

2. **Adjust Resource Limits:**
   ```bash
   # Reduce memory limits if needed
   kubectl patch deployment algorithmic-engine -n apex-brain -p '
   {
     "spec": {
       "template": {
         "spec": {
           "containers": [{
             "name": "algorithm-core",
             "resources": {
               "limits": {"memory": "1Gi"},
               "requests": {"memory": "512Mi"}
             }
           }]
         }
       }
     }
   }'
   ```

3. **Server Upgrade:**
   ```bash
   # Upgrade Hetzner server type
   hcloud server poweroff apex-brain-v4
   hcloud server change-type apex-brain-v4 cx41
   hcloud server poweron apex-brain-v4
   ```

---

## 🌐 Network Issues

### Issue: Cannot Access Web Interface

**Symptoms:**
- Browser shows "connection refused"
- Timeout when accessing server IP
- DNS resolution issues

**Diagnosis:**
```bash
# Test from server
curl http://localhost:30000/api/health

# Check service status
kubectl get services -n apex-brain

# Check firewall
ufw status
iptables -L
```

**Solutions:**

1. **Firewall Configuration:**
   ```bash
   # Open required ports
   ufw allow 30000/tcp
   ufw allow 22/tcp
   ufw allow 6443/tcp
   ufw reload
   ```

2. **Service Type Issues:**
   ```bash
   # Change service to NodePort if LoadBalancer fails
   kubectl patch service apex-brain-ui -n apex-brain -p '
   {
     "spec": {
       "type": "NodePort",
       "ports": [{
         "port": 80,
         "targetPort": 3000,
         "nodePort": 30000
       }]
     }
   }'
   ```

3. **DNS Issues:**
   ```bash
   # Use IP address directly instead of domain
   # Check DNS configuration if using custom domain
   nslookup YOUR_DOMAIN
   ```

### Issue: Internal Service Communication

**Symptoms:**
- Services can't communicate with each other
- Database connection errors
- Algorithm engine can't reach LLM

**Diagnosis:**
```bash
# Test internal DNS
kubectl exec deployment/apex-brain-ui -n apex-brain -- \
  nslookup postgresql-age.apex-brain.svc.cluster.local

# Check service endpoints
kubectl get endpoints -n apex-brain
```

**Solutions:**

1. **DNS Resolution:**
   ```bash
   # Restart CoreDNS
   kubectl rollout restart deployment/coredns -n kube-system
   
   # Use service IPs directly if DNS fails
   kubectl get services -n apex-brain -o wide
   ```

2. **Network Policies:**
   ```bash
   # Check for restrictive network policies
   kubectl get networkpolicies -n apex-brain
   
   # Delete restrictive policies if needed
   kubectl delete networkpolicy POLICY_NAME -n apex-brain
   ```

---

## 🔐 Authentication Issues

### Issue: API Token Problems

**Symptoms:**
- "Unauthorized" errors
- Token expired messages
- Cannot generate new tokens

**Diagnosis:**
```bash
# Test token validity
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:30000/api/v1/system/health

# Check token in database
kubectl exec deployment/postgresql-age -n apex-brain -- \
  psql -U apex -d apex_brain -c "SELECT * FROM api_tokens WHERE active = true;"
```

**Solutions:**

1. **Regenerate Token:**
   ```bash
   # Generate new token via API
   curl -X POST http://localhost:30000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "your_password"}'
   ```

2. **Reset Authentication:**
   ```bash
   # Reset admin password
   kubectl exec deployment/postgresql-age -n apex-brain -- \
     psql -U apex -d apex_brain -c "
     UPDATE users SET password = crypt('newpassword', gen_salt('bf')) 
     WHERE username = 'admin';"
   ```

---

## 🔄 Recovery Procedures

### Complete System Reset

**When to use:** Major corruption, multiple component failures

```bash
# 1. Backup important data
kubectl exec deployment/postgresql-age -n apex-brain -- \
  pg_dump -U apex apex_brain > backup-$(date +%Y%m%d).sql

# 2. Save configuration
kubectl get configmaps -n apex-brain -o yaml > configmaps-backup.yaml

# 3. Delete namespace (removes all components)
kubectl delete namespace apex-brain

# 4. Re-run deployment script
./deploy-apex-brain.sh

# 5. Restore data if needed
kubectl exec deployment/postgresql-age -n apex-brain -- \
  psql -U apex apex_brain < backup-$(date +%Y%m%d).sql
```

### Rollback Deployment

**When to use:** Recent deployment caused issues

```bash
# Check rollout history
kubectl rollout history deployment/llm-engine -n apex-brain

# Rollback to previous version
kubectl rollout undo deployment/llm-engine -n apex-brain

# Rollback all deployments
for deploy in postgresql-age redis-cache llm-engine algorithmic-engine apex-brain-ui; do
    kubectl rollout undo deployment/$deploy -n apex-brain
done
```

### Database Recovery

**When to use:** Database corruption or data loss

```bash
# 1. Stop applications
kubectl scale deployment llm-engine --replicas=0 -n apex-brain
kubectl scale deployment algorithmic-engine --replicas=0 -n apex-brain

# 2. Create fresh database
kubectl exec deployment/postgresql-age -n apex-brain -- \
  createdb -U apex apex_brain_new

# 3. Restore from backup
kubectl exec deployment/postgresql-age -n apex-brain -- \
  psql -U apex apex_brain_new < backup-file.sql

# 4. Switch to new database
kubectl set env deployment/postgresql-age -n apex-brain \
  POSTGRES_DB="apex_brain_new"

# 5. Restart applications
kubectl scale deployment llm-engine --replicas=1 -n apex-brain
kubectl scale deployment algorithmic-engine --replicas=1 -n apex-brain
```

---

## 📊 Monitoring and Alerts

### Setting Up Alerts

**CPU Usage Alert:**
```bash
# Create monitoring script
cat > /root/monitor-cpu.sh << 'EOF'
#!/bin/bash
CPU_USAGE=$(kubectl top nodes --no-headers | awk '{print $3}' | sed 's/%//')
if [ "$CPU_USAGE" -gt 80 ]; then
    echo "High CPU usage: ${CPU_USAGE}%" | mail -s "Apex Brain Alert" admin@company.com
fi
EOF

chmod +x /root/monitor-cpu.sh

# Add to crontab
echo "*/5 * * * * /root/monitor-cpu.sh" | crontab -
```

**Memory Usage Alert:**
```bash
# Memory monitoring
cat > /root/monitor-memory.sh << 'EOF'
#!/bin/bash
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ "$MEMORY_USAGE" -gt 85 ]; then
    echo "High memory usage: ${MEMORY_USAGE}%" | mail -s "Apex Brain Memory Alert" admin@company.com
fi
EOF

chmod +x /root/monitor-memory.sh
echo "*/10 * * * * /root/monitor-memory.sh" | crontab -
```

### Log Analysis

**Find Common Errors:**
```bash
# Aggregate error logs
kubectl logs --since=24h -l app=llm-engine -n apex-brain | grep -i error
kubectl logs --since=24h -l app=algorithmic-engine -n apex-brain | grep -i error

# Count error types
kubectl logs --since=24h -l app=llm-engine -n apex-brain | \
  grep -i error | sort | uniq -c | sort -nr
```

**Performance Analysis:**
```bash
# Response time analysis
kubectl logs --since=1h -l app=apex-brain-ui -n apex-brain | \
  grep "response_time" | awk '{print $NF}' | \
  awk '{sum+=$1; count++} END {print "Average:", sum/count "ms"}'
```

---

## 🆘 Emergency Procedures

### System Unresponsive

1. **Check server status:**
   ```bash
   hcloud server describe apex-brain-v4
   ```

2. **Reboot if necessary:**
   ```bash
   hcloud server reboot apex-brain-v4
   ```

3. **Wait for services to restart and verify:**
   ```bash
   # Wait 2-3 minutes then check
   ssh root@YOUR_SERVER_IP
   kubectl get pods -n apex-brain
   ```

### Data Corruption

1. **Immediate backup:**
   ```bash
   kubectl exec deployment/postgresql-age -n apex-brain -- \
     pg_dump -U apex apex_brain > emergency-backup-$(date +%Y%m%d-%H%M).sql
   ```

2. **Assess damage:**
   ```bash
   kubectl exec deployment/postgresql-age -n apex-brain -- \
     psql -U apex -d apex_brain -c "SELECT count(*) FROM information_schema.tables;"
   ```

3. **Restore from latest backup:**
   ```bash
   # Find latest backup
   ls -la backup-*.sql | tail -1
   
   # Restore
   kubectl exec deployment/postgresql-age -n apex-brain -- \
     psql -U apex apex_brain < latest-backup.sql
   ```

### Security Breach

1. **Immediate actions:**
   ```bash
   # Change all passwords
   kubectl set env deployment/postgresql-age -n apex-brain \
     POSTGRES_PASSWORD="new_secure_password"
   
   # Regenerate API tokens
   kubectl exec deployment/postgresql-age -n apex-brain -- \
     psql -U apex -d apex_brain -c "UPDATE api_tokens SET active = false;"
   ```

2. **Review access logs:**
   ```bash
   kubectl logs --since=24h -l app=apex-brain-ui -n apex-brain | \
     grep -E "(POST|PUT|DELETE)" | grep -v 200
   ```

3. **Update security:**
   ```bash
   # Update firewall rules
   ufw --force reset
   ufw default deny incoming
   ufw allow 22/tcp
   ufw allow 30000/tcp
   ufw enable
   ```

---

## 📞 Getting Help

### Before Contacting Support

1. **Gather system information:**
   ```bash
   # Create diagnostic report
   echo "=== System Info ===" > diagnostic-report.txt
   date >> diagnostic-report.txt
   echo "" >> diagnostic-report.txt
   
   echo "=== Kubernetes Status ===" >> diagnostic-report.txt
   kubectl get nodes >> diagnostic-report.txt
   kubectl get pods -n apex-brain >> diagnostic-report.txt
   kubectl get services -n apex-brain >> diagnostic-report.txt
   echo "" >> diagnostic-report.txt
   
   echo "=== Resource Usage ===" >> diagnostic-report.txt
   kubectl top nodes >> diagnostic-report.txt 2>/dev/null || echo "Metrics unavailable" >> diagnostic-report.txt
   kubectl top pods -n apex-brain >> diagnostic-report.txt 2>/dev/null || echo "Pod metrics unavailable" >> diagnostic-report.txt
   echo "" >> diagnostic-report.txt
   
   echo "=== Recent Events ===" >> diagnostic-report.txt
   kubectl get events -n apex-brain --sort-by='.lastTimestamp' | tail -10 >> diagnostic-report.txt
   ```

2. **Include relevant logs:**
   ```bash
   # Get error logs
   kubectl logs --since=1h -l app=llm-engine -n apex-brain > llm-logs.txt
   kubectl logs --since=1h -l app=algorithmic-engine -n apex-brain > algorithm-logs.txt
   ```

### Support Channels

1. **GitHub Issues:** Create detailed issue with:
   - Diagnostic report
   - Error logs
   - Steps to reproduce
   - Expected vs actual behavior

2. **GitHub Discussions:** For:
   - Usage questions
   - Feature requests
   - General troubleshooting
   - Community help

3. **Emergency Support:** For critical production issues:
   - Include "URGENT" in issue title
   - Provide immediate impact description
   - Include all diagnostic information

### Community Help

**Search existing issues:**
- Check GitHub Issues for similar problems
- Look through closed issues for solutions
- Search documentation for troubleshooting steps

**Provide helpful information:**
- Always include diagnostic report
- Be specific about error messages
- Describe what you were trying to achieve
- Include steps you've already tried

---

## ✅ Preventive Maintenance

### Daily Checks
```bash
#!/bin/bash
# daily-health-check.sh
echo "Daily A.I. Apex Brain Health Check - $(date)"
echo "============================================"

# System status
echo "System Status:"
kubectl get pods -n apex-brain --no-headers | awk '{print $1 ": " $3}'

# Resource usage
echo -e "\nResource Usage:"
kubectl top pods -n apex-brain --no-headers 2>/dev/null | awk '{print $1 ": CPU " $2 " Memory " $3}'

# Error count
echo -e "\nError Summary (last 24h):"
kubectl logs --since=24h -l app!='' -n apex-brain | grep -i error | wc -l | awk '{print "Total errors: " $1}'

# Disk usage
echo -e "\nDisk Usage:"
df -h | grep -E "(/$|/var)"
```

### Weekly Maintenance
```bash
#!/bin/bash
# weekly-maintenance.sh

# Clean up old logs
kubectl logs --since=168h -l app!='' -n apex-brain > /dev/null

# Update system packages
apt update && apt list --upgradable

# Check for Kubernetes updates
kubectl version --short

# Backup database
kubectl exec deployment/postgresql-age -n apex-brain -- \
  pg_dump -U apex apex_brain > weekly-backup-$(date +%Y%m%d).sql

# Restart services to clear memory leaks
kubectl rollout restart deployment -n apex-brain
```

---

*🛠️ Remember: Most issues can be resolved with a simple restart or scaling adjustment. When in doubt, check the logs first, then restart the affected component.*

**Still need help?** Create a detailed GitHub issue with your diagnostic report and we'll help you get back on track!leshooting_guide.md…]()
