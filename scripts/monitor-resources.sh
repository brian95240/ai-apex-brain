#!/bin/bash
# A.I. Apex Brain Resource Monitor

LOGFILE="/var/log/apex-brain-monitor.log"
ALERT_EMAIL="admin@company.com"
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOGFILE"
}

send_alert() {
    local subject="$1"
    local message="$2"
    echo "$message" | mail -s "$subject" "$ALERT_EMAIL" 2>/dev/null || \
    echo "ALERT: $subject - $message" >> "$LOGFILE"
}

# Check CPU usage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
if (( $(echo "$CPU_USAGE > $CPU_THRESHOLD" | bc -l) )); then
    log_message "HIGH CPU USAGE: ${CPU_USAGE}%"
    send_alert "Apex Brain High CPU Alert" "CPU usage is at ${CPU_USAGE}%, threshold is ${CPU_THRESHOLD}%"
fi

# Check memory usage
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
if (( $(echo "$MEMORY_USAGE > $MEMORY_THRESHOLD" | bc -l) )); then
    log_message "HIGH MEMORY USAGE: ${MEMORY_USAGE}%"
    send_alert "Apex Brain High Memory Alert" "Memory usage is at ${MEMORY_USAGE}%, threshold is ${MEMORY_THRESHOLD}%"
fi

# Check disk usage
DISK_USAGE=$(df / | awk 'NR==2{printf "%.1f", $5}' | sed 's/%//')
if (( $(echo "$DISK_USAGE > $DISK_THRESHOLD" | bc -l) )); then
    log_message "HIGH DISK USAGE: ${DISK_USAGE}%"
    send_alert "Apex Brain High Disk Alert" "Disk usage is at ${DISK_USAGE}%, threshold is ${DISK_THRESHOLD}%"
fi

# Check pod status
FAILED_PODS=$(kubectl get pods -n apex-brain --no-headers | grep -v Running | wc -l)
if [ $FAILED_PODS -gt 0 ]; then
    log_message "FAILED PODS DETECTED: $FAILED_PODS pods not running"
    send_alert "Apex Brain Pod Failure Alert" "$FAILED_PODS pods are not in Running state"
fi

# Log normal status
if [ $FAILED_PODS -eq 0 ] && \
   (( $(echo "$CPU_USAGE <= $CPU_THRESHOLD" | bc -l) )) && \
   (( $(echo "$MEMORY_USAGE <= $MEMORY_THRESHOLD" | bc -l) )) && \
   (( $(echo "$DISK_USAGE <= $DISK_THRESHOLD" | bc -l) )); then
    log_message "SYSTEM HEALTHY - CPU: ${CPU_USAGE}%, Memory: ${MEMORY_USAGE}%, Disk: ${DISK_USAGE}%"
fi
