#!/bin/bash
# Generate comprehensive diagnostic report

REPORT_FILE="/tmp/apex-brain-diagnostic-$(date +%Y%m%d-%H%M%S).txt"

echo "🔍 Generating A.I. Apex Brain Diagnostic Report..."
echo "Report will be saved to: $REPORT_FILE"

{
    echo "========================================"
    echo "A.I. APEX BRAIN DIAGNOSTIC REPORT"
    echo "Generated: $(date)"
    echo "========================================"
    echo ""
    
    echo "=== SYSTEM INFORMATION ==="
    echo "Hostname: $(hostname)"
    echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    echo "Kernel: $(uname -r)"
    echo "Uptime: $(uptime -p)"
    echo ""
    
    echo "=== HARDWARE INFORMATION ==="
    echo "CPU: $(nproc) cores"
    echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
    echo "Disk Space:"
    df -h | grep -E "(/$|/var)"
    echo ""
    
    echo "=== KUBERNETES CLUSTER STATUS ==="
    echo "K3s Version:"
    k3s --version | head -1
    echo ""
    echo "Nodes:"
    kubectl get nodes -o wide
    echo ""
    echo "Namespaces:"
    kubectl get namespaces
    echo ""
    
    echo "=== APEX BRAIN PODS STATUS ==="
    kubectl get pods -n apex-brain -o wide
    echo ""
    
    echo "=== APEX BRAIN SERVICES ==="
    kubectl get services -n apex-brain
    echo ""
    
    echo "=== RESOURCE USAGE ==="
    echo "Node Resources:"
    kubectl top nodes 2>/dev/null || echo "Metrics server not available"
    echo ""
    echo "Pod Resources:"
    kubectl top pods -n apex-brain 2>/dev/null || echo "Pod metrics not available"
    echo ""
    
    echo "=== RECENT EVENTS ==="
    kubectl get events -n apex-brain --sort-by='.lastTimestamp' | tail -20
    echo ""
    
    echo "=== CONFIGURATION ==="
    echo "ConfigMaps:"
    kubectl get configmaps -n apex-brain
    echo ""
    echo "Secrets:"
    kubectl get secrets -n apex-brain
    echo ""
    
    echo "=== NETWORK INFORMATION ==="
    echo "Endpoints:"
    kubectl get endpoints -n apex-brain
    echo ""
    echo "Network Policies:"
    kubectl get networkpolicies -n apex-brain
    echo ""
    
    echo "=== RECENT LOGS (Last 100 lines) ==="
    echo "--- LLM Engine Logs ---"
    kubectl logs --tail=50 deployment/llm-engine -n apex-brain 2>/dev/null || echo "LLM engine logs not available"
    echo ""
    echo "--- Algorithm Engine Logs ---"
    kubectl logs --tail=50 deployment/algorithmic-engine -n apex-brain 2>/dev/null || echo "Algorithm engine logs not available"
    echo ""
    
    echo "=== EXTERNAL CONNECTIVITY ==="
    echo "Testing external connectivity..."
    curl -s --connect-timeout 5 http://localhost:30000/api/health > /dev/null && echo "✅ Local API accessible" || echo "❌ Local API not accessible"
    curl -s --connect-timeout 5 https://google.com > /dev/null && echo "✅ Internet connectivity working" || echo "❌ Internet connectivity issues"
    echo ""
    
    echo "=== SYSTEM PROCESSES ==="
    echo "Top processes by CPU:"
    ps aux --sort=-%cpu | head -10
    echo ""
    echo "Top processes by Memory:"
    ps aux --sort=-%mem | head -10
    echo ""
    
    echo "=== DISK USAGE ==="
    echo "Disk usage by directory:"
    du -sh /var/lib/rancher /var/log /tmp 2>/dev/null || echo "Some directories not accessible"
    echo ""
    
    echo "========================================"
    echo "END OF DIAGNOSTIC REPORT"
    echo "========================================"
    
} > "$REPORT_FILE"

echo "✅ Diagnostic report generated: $REPORT_FILE"
echo "📧 You can share this file when reporting issues"

# Display summary
echo ""
echo "📋 Quick Summary:"
kubectl get pods -n apex-brain --no-headers | awk '{
    if ($3 == "Running") running++; 
    else failed++; 
    total++
} 
END {
    print "Total Pods: " total
    print "Running: " (running ? running : 0)
    print "Failed: " (failed ? failed : 0)
}'

echo ""
echo "💾 Report size: $(du -h $REPORT_FILE | cut -f1)"
