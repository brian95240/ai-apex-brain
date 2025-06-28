#!/bin/bash
# A.I. Apex Brain Auto-Scaling Script

NAMESPACE="apex-brain"
METRICS_SERVER_AVAILABLE=false

# Check if metrics server is available
if kubectl top pods -n $NAMESPACE &>/dev/null; then
    METRICS_SERVER_AVAILABLE=true
fi

echo "🔧 Auto-Scaling Check - $(date)"
echo "=============================="

if [ "$METRICS_SERVER_AVAILABLE" = false ]; then
    echo "⚠️ Metrics server not available, using basic scaling logic"
fi

# Function to scale deployment
scale_deployment() {
    local deployment=$1
    local current_replicas=$2
    local target_replicas=$3
    
    if [ $current_replicas -ne $target_replicas ]; then
        echo "📈 Scaling $deployment from $current_replicas to $target_replicas replicas"
        kubectl scale deployment $deployment --replicas=$target_replicas -n $NAMESPACE
    fi
}

# Get current replicas
LLM_REPLICAS=$(kubectl get deployment llm-engine -n $NAMESPACE -o jsonpath='{.spec.replicas}')
ALG_REPLICAS=$(kubectl get deployment algorithmic-engine -n $NAMESPACE -o jsonpath='{.spec.replicas}')
UI_REPLICAS=$(kubectl get deployment apex-brain-ui -n $NAMESPACE -o jsonpath='{.spec.replicas}')

if [ "$METRICS_SERVER_AVAILABLE" = true ]; then
    # Advanced scaling based on metrics
    LLM_CPU=$(kubectl top pod -n $NAMESPACE | grep llm-engine | awk '{print $3}' | sed 's/m//' | head -1)
    ALG_CPU=$(kubectl top pod -n $NAMESPACE | grep algorithmic-engine | awk '{print $3}' | sed 's/m//' | head -1)
    
    LLM_CPU=${LLM_CPU:-0}
    ALG_CPU=${ALG_CPU:-0}
    
    # Scale LLM engine based on CPU usage
    if [ $LLM_CPU -gt 1500 ] && [ $LLM_REPLICAS -lt 3 ]; then
        scale_deployment "llm-engine" $LLM_REPLICAS $((LLM_REPLICAS + 1))
    elif [ $LLM_CPU -lt 500 ] && [ $LLM_REPLICAS -gt 1 ]; then
        scale_deployment "llm-engine" $LLM_REPLICAS $((LLM_REPLICAS - 1))
    fi
    
    # Scale algorithm engine based on CPU usage
    if [ $ALG_CPU -gt 800 ] && [ $ALG_REPLICAS -lt 2 ]; then
        scale_deployment "algorithmic-engine" $ALG_REPLICAS $((ALG_REPLICAS + 1))
    elif [ $ALG_CPU -lt 200 ] && [ $ALG_REPLICAS -gt 1 ]; then
        scale_deployment "algorithmic-engine" $ALG_REPLICAS $((ALG_REPLICAS - 1))
    fi
else
    # Basic scaling based on time and load patterns
    HOUR=$(date +%H)
    
    # Peak hours (9 AM - 6 PM): scale up
    if [ $HOUR -ge 9 ] && [ $HOUR -le 18 ]; then
        if [ $LLM_REPLICAS -lt 2 ]; then
            scale_deployment "llm-engine" $LLM_REPLICAS 2
        fi
        if [ $ALG_REPLICAS -lt 2 ]; then
            scale_deployment "algorithmic-engine" $ALG_REPLICAS 2
        fi
    # Off hours: scale down
    else
        if [ $LLM_REPLICAS -gt 1 ]; then
            scale_deployment "llm-engine" $LLM_REPLICAS 1
        fi
        if [ $ALG_REPLICAS -gt 1 ]; then
            scale_deployment "algorithmic-engine" $ALG_REPLICAS 1
        fi
    fi
fi

echo "✅ Auto-scaling check completed"
echo "Current state: LLM=$LLM_REPLICAS, Algorithm=$ALG_REPLICAS, UI=$UI_REPLICAS"
