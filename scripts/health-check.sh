#!/bin/bash
# A.I. Apex Brain Health Check Script

echo "🏥 A.I. Apex Brain Health Check - $(date)"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check status
check_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

# Check if kubectl is available
if command -v kubectl &> /dev/null; then
    echo -e "${GREEN}✅ kubectl is available${NC}"
    
    # Check namespace
    if kubectl get namespace apex-brain &> /dev/null; then
        echo -e "${GREEN}✅ apex-brain namespace exists${NC}"
        
        echo ""
        echo "📊 Pod Status:"
        echo "=============="
        kubectl get pods -n apex-brain --no-headers | while read line; do
            pod_name=$(echo $line | awk '{print $1}')
            pod_status=$(echo $line | awk '{print $3}')
            
            if [ "$pod_status" = "Running" ]; then
                echo -e "${GREEN}✅ $pod_name: $pod_status${NC}"
            elif [ "$pod_status" = "Pending" ]; then
                echo -e "${YELLOW}⏳ $pod_name: $pod_status${NC}"
            else
                echo -e "${RED}❌ $pod_name: $pod_status${NC}"
            fi
        done
        
        echo ""
        echo "🌐 Service Status:"
        echo "=================="
        kubectl get services -n apex-brain --no-headers | while read line; do
            svc_name=$(echo $line | awk '{print $1}')
            svc_type=$(echo $line | awk '{print $2}')
            cluster_ip=$(echo $line | awk '{print $3}')
            echo -e "${GREEN}✅ $svc_name ($svc_type): $cluster_ip${NC}"
        done
        
        echo ""
        echo "📈 Resource Usage:"
        echo "=================="
        if kubectl top pods -n apex-brain &> /dev/null; then
            kubectl top pods -n apex-brain
        else
            echo -e "${YELLOW}⚠️ Metrics server not available${NC}"
        fi
        
        echo ""
        echo "🔍 Recent Events:"
        echo "================="
        kubectl get events -n apex-brain --sort-by='.lastTimestamp' | tail -5
        
        echo ""
        echo "🌐 External Access Test:"
        echo "======================="
        node_ip=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}' 2>/dev/null || kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
        
        if curl -s --connect-timeout 5 http://$node_ip:30000/api/health > /dev/null; then
            echo -e "${GREEN}✅ Web interface accessible at http://$node_ip:30000${NC}"
        else
            echo -e "${RED}❌ Web interface not accessible${NC}"
        fi
        
    else
        echo -e "${RED}❌ apex-brain namespace not found${NC}"
    fi
else
    echo -e "${RED}❌ kubectl not found - are you on the deployment server?${NC}"
fi

echo ""
echo "💾 System Resources:"
echo "==================="
echo "Memory Usage:"
free -h | grep -E "Mem:|Swap:"
echo ""
echo "Disk Usage:"
df -h | grep -E "(/$|/var)"

echo ""
echo "📋 Health Summary:"
echo "=================="
# Count running pods
running_pods=$(kubectl get pods -n apex-brain --no-headers 2>/dev/null | grep Running | wc -l)
total_pods=$(kubectl get pods -n apex-brain --no-headers 2>/dev/null | wc -l)

if [ $running_pods -eq $total_pods ] && [ $total_pods -gt 0 ]; then
    echo -e "${GREEN}🟢 System Status: HEALTHY${NC}"
    echo "All $total_pods pods are running successfully"
elif [ $running_pods -gt 0 ]; then
    echo -e "${YELLOW}🟡 System Status: DEGRADED${NC}"
    echo "$running_pods/$total_pods pods are running"
else
    echo -e "${RED}🔴 System Status: CRITICAL${NC}"
    echo "No pods are running properly"
fi

echo ""
echo "🛠️ Quick Commands:"
echo "=================="
echo "View logs: kubectl logs -f deployment/DEPLOYMENT_NAME -n apex-brain"
echo "Restart service: kubectl rollout restart deployment/DEPLOYMENT_NAME -n apex-brain"
echo "Scale service: kubectl scale deployment/DEPLOYMENT_NAME --replicas=N -n apex-brain"
echo "SSH to server: ssh root@$node_ip"
