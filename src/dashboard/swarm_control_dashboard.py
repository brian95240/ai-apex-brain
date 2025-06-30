#!/usr/bin/env python3
"""
Granular Swarm Control Dashboard Backend
Provides real-time cost prediction, resource monitoring, and swarm control
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from fastapi.responses import Response
import psutil
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class CostPrediction:
    """Cost prediction data structure"""
    total_cost: float
    breakdown: Dict[str, float]
    estimated_time: float
    confidence: float
    timestamp: float

@dataclass
class ResourceMetrics:
    """Resource usage metrics"""
    cpu_usage: float
    memory_usage: float
    network_io: Dict[str, float]
    disk_io: Dict[str, float]
    active_algorithms: int
    queue_length: int
    timestamp: float

@dataclass
class SwarmConfiguration:
    """Swarm configuration settings"""
    reasoning_agents: int = 3
    technical_agents: int = 2
    creative_agents: int = 1
    analytical_agents: int = 2
    max_concurrent_tasks: int = 50
    budget_limit_hourly: float = 5.0
    budget_limit_daily: float = 50.0
    quality_threshold: float = 0.85
    auto_scaling: bool = True
    emergency_stop_threshold: float = 0.95

@dataclass
class BudgetStatus:
    """Budget tracking information"""
    hourly_spent: float
    daily_spent: float
    hourly_limit: float
    daily_limit: float
    remaining_hourly: float
    remaining_daily: float
    burn_rate: float
    projected_daily: float
    alert_level: str  # "green", "yellow", "red"

class CostPredictor:
    """Real-time cost prediction engine"""
    
    def __init__(self):
        self.cost_rates = {
            "cpu_core_hour": 0.05,
            "memory_gb_hour": 0.01,
            "model_inference_token": 0.002,
            "network_gb": 0.10,
            "storage_gb_hour": 0.001
        }
        self.historical_costs = deque(maxlen=1000)
        self.cost_models = {}
    
    def predict_query_cost(self, query_complexity: int, agents_config: SwarmConfiguration, 
                          quality_threshold: float) -> CostPrediction:
        """Predict cost for a query execution"""
        
        # Calculate total agents
        total_agents = (agents_config.reasoning_agents + agents_config.technical_agents + 
                       agents_config.creative_agents + agents_config.analytical_agents)
        
        # Estimate tokens based on complexity
        estimated_tokens = query_complexity * 50  # Base tokens per complexity unit
        
        # Quality multiplier (higher quality = more processing)
        quality_multiplier = quality_threshold ** 1.5
        
        # Agent overhead multiplier
        agent_multiplier = 1 + (total_agents - 1) * 0.3
        
        # Calculate cost components
        inference_cost = (estimated_tokens * total_agents * 
                         self.cost_rates["model_inference_token"] * quality_multiplier)
        
        # Estimate processing time (seconds)
        processing_time = max(1, query_complexity * 0.5 * agent_multiplier * quality_multiplier)
        
        # CPU cost
        cpu_cost = (processing_time / 3600) * total_agents * 0.5 * self.cost_rates["cpu_core_hour"]
        
        # Memory cost (assume 2GB per agent)
        memory_cost = (processing_time / 3600) * total_agents * 2 * self.cost_rates["memory_gb_hour"]
        
        # Network cost (minimal for internal processing)
        network_cost = 0.001
        
        total_cost = inference_cost + cpu_cost + memory_cost + network_cost
        
        # Calculate confidence based on historical data
        confidence = min(0.95, 0.7 + len(self.historical_costs) / 1000 * 0.25)
        
        prediction = CostPrediction(
            total_cost=total_cost,
            breakdown={
                "inference": inference_cost,
                "compute": cpu_cost,
                "memory": memory_cost,
                "network": network_cost
            },
            estimated_time=processing_time,
            confidence=confidence,
            timestamp=time.time()
        )
        
        return prediction
    
    def record_actual_cost(self, predicted: CostPrediction, actual_cost: float, actual_time: float):
        """Record actual cost for model improvement"""
        self.historical_costs.append({
            "predicted": predicted.total_cost,
            "actual": actual_cost,
            "predicted_time": predicted.estimated_time,
            "actual_time": actual_time,
            "timestamp": time.time()
        })

class ResourceMonitor:
    """Real-time resource monitoring"""
    
    def __init__(self):
        self.metrics_history = deque(maxlen=1000)
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start resource monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Resource monitoring loop"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                time.sleep(1)  # Collect metrics every second
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                time.sleep(5)
    
    def _collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics"""
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
        
        # Disk I/O
        disk = psutil.disk_io_counters()
        disk_io = {
            "read_bytes": disk.read_bytes if disk else 0,
            "write_bytes": disk.write_bytes if disk else 0,
            "read_count": disk.read_count if disk else 0,
            "write_count": disk.write_count if disk else 0
        }
        
        return ResourceMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            network_io=network_io,
            disk_io=disk_io,
            active_algorithms=0,  # Will be updated by orchestrator
            queue_length=0,       # Will be updated by orchestrator
            timestamp=time.time()
        )
    
    def get_current_metrics(self) -> Optional[ResourceMetrics]:
        """Get the most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self, duration_seconds: int = 300) -> List[ResourceMetrics]:
        """Get metrics history for specified duration"""
        cutoff_time = time.time() - duration_seconds
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]

class BudgetTracker:
    """Budget tracking and management"""
    
    def __init__(self):
        self.hourly_costs = deque(maxlen=24)  # Last 24 hours
        self.daily_costs = deque(maxlen=30)   # Last 30 days
        self.current_hour_cost = 0.0
        self.current_day_cost = 0.0
        self.last_hour_reset = time.time()
        self.last_day_reset = time.time()
    
    def add_cost(self, cost: float):
        """Add a cost entry"""
        current_time = time.time()
        
        # Check if we need to reset hourly tracking
        if current_time - self.last_hour_reset >= 3600:  # 1 hour
            self.hourly_costs.append(self.current_hour_cost)
            self.current_hour_cost = 0.0
            self.last_hour_reset = current_time
        
        # Check if we need to reset daily tracking
        if current_time - self.last_day_reset >= 86400:  # 1 day
            self.daily_costs.append(self.current_day_cost)
            self.current_day_cost = 0.0
            self.last_day_reset = current_time
        
        self.current_hour_cost += cost
        self.current_day_cost += cost
    
    def get_budget_status(self, config: SwarmConfiguration) -> BudgetStatus:
        """Get current budget status"""
        # Calculate burn rate (cost per hour)
        if len(self.hourly_costs) > 0:
            burn_rate = sum(self.hourly_costs) / len(self.hourly_costs)
        else:
            burn_rate = self.current_hour_cost
        
        # Project daily cost
        projected_daily = burn_rate * 24
        
        # Calculate remaining budgets
        remaining_hourly = max(0, config.budget_limit_hourly - self.current_hour_cost)
        remaining_daily = max(0, config.budget_limit_daily - self.current_day_cost)
        
        # Determine alert level
        hourly_usage = self.current_hour_cost / config.budget_limit_hourly
        daily_usage = self.current_day_cost / config.budget_limit_daily
        max_usage = max(hourly_usage, daily_usage)
        
        if max_usage >= 0.9:
            alert_level = "red"
        elif max_usage >= 0.75:
            alert_level = "yellow"
        else:
            alert_level = "green"
        
        return BudgetStatus(
            hourly_spent=self.current_hour_cost,
            daily_spent=self.current_day_cost,
            hourly_limit=config.budget_limit_hourly,
            daily_limit=config.budget_limit_daily,
            remaining_hourly=remaining_hourly,
            remaining_daily=remaining_daily,
            burn_rate=burn_rate,
            projected_daily=projected_daily,
            alert_level=alert_level
        )

class SwarmControlDashboard:
    """Main dashboard controller"""
    
    def __init__(self):
        self.app = FastAPI(title="Granular Swarm Control Dashboard")
        self.cost_predictor = CostPredictor()
        self.resource_monitor = ResourceMonitor()
        self.budget_tracker = BudgetTracker()
        self.swarm_config = SwarmConfiguration()
        self.connected_clients = set()
        
        # Prometheus metrics
        self.dashboard_requests = Counter('dashboard_requests_total', 'Total dashboard requests')
        self.active_connections = Gauge('dashboard_active_connections', 'Active WebSocket connections')
        self.cost_predictions = Counter('cost_predictions_total', 'Total cost predictions made')
        
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/")
        async def dashboard():
            return HTMLResponse(self._get_dashboard_html())
        
        @self.app.get("/api/config")
        async def get_config():
            self.dashboard_requests.inc()
            return asdict(self.swarm_config)
        
        @self.app.post("/api/config")
        async def update_config(config: dict):
            self.dashboard_requests.inc()
            # Update configuration
            for key, value in config.items():
                if hasattr(self.swarm_config, key):
                    setattr(self.swarm_config, key, value)
            
            # Broadcast update to connected clients
            await self._broadcast_update("config_updated", asdict(self.swarm_config))
            return {"status": "success", "config": asdict(self.swarm_config)}
        
        @self.app.post("/api/predict-cost")
        async def predict_cost(request: dict):
            self.dashboard_requests.inc()
            self.cost_predictions.inc()
            
            query_complexity = request.get('complexity', 5)
            quality_threshold = request.get('quality_threshold', self.swarm_config.quality_threshold)
            
            prediction = self.cost_predictor.predict_query_cost(
                query_complexity, self.swarm_config, quality_threshold
            )
            
            return asdict(prediction)
        
        @self.app.get("/api/resources")
        async def get_resources():
            self.dashboard_requests.inc()
            metrics = self.resource_monitor.get_current_metrics()
            return asdict(metrics) if metrics else {}
        
        @self.app.get("/api/budget")
        async def get_budget():
            self.dashboard_requests.inc()
            budget_status = self.budget_tracker.get_budget_status(self.swarm_config)
            return asdict(budget_status)
        
        @self.app.post("/api/emergency-stop")
        async def emergency_stop():
            self.dashboard_requests.inc()
            # Implement emergency stop logic
            await self._broadcast_update("emergency_stop", {"timestamp": time.time()})
            return {"status": "emergency_stop_activated"}
        
        @self.app.get("/metrics")
        async def metrics():
            self.active_connections.set(len(self.connected_clients))
            return Response(generate_latest(), media_type="text/plain")
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.connected_clients.add(websocket)
            
            try:
                while True:
                    # Send real-time updates
                    await self._send_realtime_update(websocket)
                    await asyncio.sleep(1)  # Update every second
                    
            except WebSocketDisconnect:
                self.connected_clients.remove(websocket)
    
    async def _send_realtime_update(self, websocket: WebSocket):
        """Send real-time update to a WebSocket client"""
        try:
            # Collect current data
            metrics = self.resource_monitor.get_current_metrics()
            budget_status = self.budget_tracker.get_budget_status(self.swarm_config)
            
            update = {
                "type": "realtime_update",
                "timestamp": time.time(),
                "resources": asdict(metrics) if metrics else {},
                "budget": asdict(budget_status),
                "config": asdict(self.swarm_config)
            }
            
            await websocket.send_json(update)
            
        except Exception as e:
            logger.error(f"Error sending WebSocket update: {e}")
    
    async def _broadcast_update(self, update_type: str, data: Any):
        """Broadcast update to all connected clients"""
        if not self.connected_clients:
            return
        
        message = {
            "type": update_type,
            "timestamp": time.time(),
            "data": data
        }
        
        # Send to all connected clients
        disconnected_clients = set()
        for client in self.connected_clients:
            try:
                await client.send_json(message)
            except Exception:
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.connected_clients -= disconnected_clients
    
    def _get_dashboard_html(self) -> str:
        """Get the enhanced Ironman-style dashboard HTML"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Apex Brain - Granular Swarm Control</title>
            <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
            <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
            <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet">
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: 'Orbitron', 'Arial', sans-serif;
                    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2a2a2a 100%);
                    color: #00d4ff;
                    overflow-x: hidden;
                    min-height: 100vh;
                    position: relative;
                }

                /* Ironman-style background texture */
                body::before {
                    content: '';
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: 
                        radial-gradient(circle at 20% 20%, rgba(255,255,255,0.1) 1px, transparent 1px),
                        radial-gradient(circle at 80% 80%, rgba(255,255,255,0.05) 1px, transparent 1px),
                        linear-gradient(45deg, transparent 49%, rgba(0,212,255,0.03) 50%, transparent 51%);
                    background-size: 50px 50px, 30px 30px, 100px 100px;
                    pointer-events: none;
                    z-index: -1;
                }

                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                    position: relative;
                    z-index: 1;
                }

                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    position: relative;
                }

                .logo {
                    font-size: 36px;
                    font-weight: 900;
                    color: #00d4ff;
                    text-shadow: 0 0 30px #00d4ff;
                    margin-bottom: 10px;
                    position: relative;
                    letter-spacing: 3px;
                }

                .logo::before {
                    content: '🧠';
                    position: absolute;
                    left: -60px;
                    top: 50%;
                    transform: translateY(-50%);
                    font-size: 40px;
                    filter: drop-shadow(0 0 15px #00d4ff);
                }

                .status-indicator {
                    display: inline-block;
                    width: 15px;
                    height: 15px;
                    background: #00ff00;
                    border-radius: 50%;
                    margin-left: 15px;
                    box-shadow: 0 0 20px #00ff00;
                    animation: pulse 2s infinite;
                }

                @keyframes pulse {
                    0%, 100% { opacity: 1; transform: scale(1); }
                    50% { opacity: 0.7; transform: scale(1.1); }
                }

                .dashboard {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 25px;
                    margin-bottom: 30px;
                }

                .panel {
                    background: linear-gradient(145deg, #2a2a2a, #1a1a1a);
                    border: 2px solid #444;
                    border-radius: 15px;
                    padding: 25px;
                    position: relative;
                    box-shadow: 
                        inset 0 0 30px rgba(0,212,255,0.1),
                        0 8px 25px rgba(0,0,0,0.6),
                        0 0 50px rgba(0,212,255,0.05);
                    transition: all 0.3s ease;
                }

                .panel:hover {
                    transform: translateY(-5px);
                    box-shadow: 
                        inset 0 0 40px rgba(0,212,255,0.15),
                        0 12px 35px rgba(0,0,0,0.8),
                        0 0 60px rgba(0,212,255,0.1);
                }

                /* Realistic rivets */
                .panel::before,
                .panel::after {
                    content: '';
                    position: absolute;
                    width: 12px;
                    height: 12px;
                    background: radial-gradient(circle, #888 20%, #555 50%, #333 80%);
                    border-radius: 50%;
                    box-shadow: 
                        inset 0 2px 4px rgba(255,255,255,0.3),
                        inset 0 -2px 4px rgba(0,0,0,0.5),
                        0 0 10px rgba(0,212,255,0.2);
                }

                .panel::before {
                    top: 15px;
                    left: 15px;
                }

                .panel::after {
                    top: 15px;
                    right: 15px;
                }

                /* Additional rivets */
                .panel .rivet-bottom-left,
                .panel .rivet-bottom-right {
                    position: absolute;
                    width: 12px;
                    height: 12px;
                    background: radial-gradient(circle, #888 20%, #555 50%, #333 80%);
                    border-radius: 50%;
                    box-shadow: 
                        inset 0 2px 4px rgba(255,255,255,0.3),
                        inset 0 -2px 4px rgba(0,0,0,0.5),
                        0 0 10px rgba(0,212,255,0.2);
                }

                .panel .rivet-bottom-left {
                    bottom: 15px;
                    left: 15px;
                }

                .panel .rivet-bottom-right {
                    bottom: 15px;
                    right: 15px;
                }

                .panel-title {
                    font-size: 20px;
                    font-weight: 700;
                    color: #00d4ff;
                    margin-bottom: 20px;
                    text-align: center;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    text-shadow: 0 0 15px #00d4ff;
                    position: relative;
                    padding-bottom: 10px;
                }

                .panel-title::after {
                    content: '';
                    position: absolute;
                    bottom: 0;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 60%;
                    height: 2px;
                    background: linear-gradient(90deg, transparent, #00d4ff, transparent);
                    box-shadow: 0 0 10px #00d4ff;
                }

                .metric {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin: 15px 0;
                    padding: 12px;
                    background: linear-gradient(145deg, #1a1a1a, #0a0a0a);
                    border: 1px solid #333;
                    border-radius: 8px;
                    transition: all 0.3s ease;
                }

                .metric:hover {
                    border-color: #00d4ff;
                    box-shadow: 0 0 15px rgba(0,212,255,0.3);
                }

                .metric-label {
                    font-size: 14px;
                    color: #ccc;
                    font-weight: 400;
                }

                .metric-value {
                    font-weight: 700;
                    font-size: 16px;
                    color: #00ff00;
                    text-shadow: 0 0 10px #00ff00;
                }

                .alert-red {
                    color: #ff4444 !important;
                    text-shadow: 0 0 10px #ff4444 !important;
                }

                .alert-yellow {
                    color: #ffaa00 !important;
                    text-shadow: 0 0 10px #ffaa00 !important;
                }

                .control-group {
                    margin: 20px 0;
                    padding: 15px;
                    background: linear-gradient(145deg, #1a1a1a, #0a0a0a);
                    border: 1px solid #333;
                    border-radius: 10px;
                }

                .control-label {
                    display: block;
                    margin-bottom: 10px;
                    font-size: 14px;
                    color: #00d4ff;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }

                .slider {
                    width: 100%;
                    height: 8px;
                    border-radius: 4px;
                    background: linear-gradient(90deg, #333, #555);
                    outline: none;
                    margin: 10px 0;
                    cursor: pointer;
                    -webkit-appearance: none;
                    appearance: none;
                }

                .slider::-webkit-slider-thumb {
                    -webkit-appearance: none;
                    appearance: none;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background: linear-gradient(145deg, #00d4ff, #0099cc);
                    cursor: pointer;
                    box-shadow: 0 0 15px rgba(0,212,255,0.5);
                    border: 2px solid #333;
                }

                .slider::-moz-range-thumb {
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background: linear-gradient(145deg, #00d4ff, #0099cc);
                    cursor: pointer;
                    box-shadow: 0 0 15px rgba(0,212,255,0.5);
                    border: 2px solid #333;
                }

                .button {
                    background: linear-gradient(145deg, #00d4ff, #0099cc);
                    color: #000;
                    border: 2px solid #333;
                    padding: 12px 25px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 700;
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(0,212,255,0.3);
                    position: relative;
                    overflow: hidden;
                }

                .button::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                    transition: left 0.5s ease;
                }

                .button:hover::before {
                    left: 100%;
                }

                .button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,212,255,0.5);
                }

                .emergency-button {
                    background: linear-gradient(145deg, #ff4444, #cc0000) !important;
                    color: white !important;
                    box-shadow: 0 4px 15px rgba(255,68,68,0.3) !important;
                    width: 100%;
                    margin-top: 20px;
                    font-size: 16px;
                    padding: 15px;
                }

                .emergency-button:hover {
                    box-shadow: 0 6px 25px rgba(255,68,68,0.6) !important;
                    transform: translateY(-3px);
                }

                .additional-controls {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-top: 30px;
                }

                .control-button {
                    background: linear-gradient(145deg, #333, #222);
                    border: 2px solid #555;
                    border-radius: 10px;
                    color: #00d4ff;
                    padding: 15px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-align: center;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    position: relative;
                    overflow: hidden;
                }

                .control-button::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(0,212,255,0.2), transparent);
                    transition: left 0.5s ease;
                }

                .control-button:hover::before {
                    left: 100%;
                }

                .control-button:hover {
                    border-color: #00d4ff;
                    box-shadow: 0 0 20px rgba(0,212,255,0.3);
                    transform: translateY(-2px);
                }

                /* Mobile responsiveness */
                @media (max-width: 768px) {
                    .dashboard {
                        grid-template-columns: 1fr;
                    }
                    
                    .additional-controls {
                        grid-template-columns: repeat(2, 1fr);
                    }
                    
                    .logo {
                        font-size: 28px;
                    }
                    
                    .logo::before {
                        left: -45px;
                        font-size: 32px;
                    }
                }

                /* Loading animation */
                .loading {
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border: 2px solid #444;
                    border-top: 2px solid #00d4ff;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-right: 10px;
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">
                        AI APEX BRAIN
                        <span class="status-indicator" id="statusIndicator"></span>
                    </div>
                    <div style="color: #888; font-size: 16px; margin-top: 10px;">
                        Granular Swarm Control Dashboard
                    </div>
                </div>
                <div id="root"></div>
            </div>
            
            <script type="text/babel">
                const { useState, useEffect } = React;
                
                function Dashboard() {
                    const [config, setConfig] = useState({});
                    const [resources, setResources] = useState({});
                    const [budget, setBudget] = useState({});
                    const [connected, setConnected] = useState(false);
                    
                    useEffect(() => {
                        // WebSocket connection for real-time updates
                        const ws = new WebSocket(`ws://${window.location.host}/ws`);
                        
                        ws.onopen = () => {
                            setConnected(true);
                            document.getElementById('statusIndicator').style.background = '#00ff00';
                        };
                        ws.onclose = () => {
                            setConnected(false);
                            document.getElementById('statusIndicator').style.background = '#ff4444';
                        };
                        ws.onmessage = (event) => {
                            const data = JSON.parse(event.data);
                            if (data.type === 'realtime_update') {
                                setResources(data.resources);
                                setBudget(data.budget);
                                setConfig(data.config);
                            }
                        };
                        
                        return () => ws.close();
                    }, []);
                    
                    const updateConfig = async (newConfig) => {
                        try {
                            const response = await fetch('/api/config', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(newConfig)
                            });
                            const result = await response.json();
                            setConfig(result.config);
                        } catch (error) {
                            console.error('Error updating config:', error);
                        }
                    };
                    
                    const emergencyStop = async () => {
                        if (confirm('⚠️ EMERGENCY STOP\\n\\nThis will immediately halt all AI operations.\\nAre you sure you want to proceed?')) {
                            await fetch('/api/emergency-stop', { method: 'POST' });
                        }
                    };

                    const importModels = () => {
                        alert('🔄 Model import interface will open...');
                    };

                    const exportModels = () => {
                        alert('📤 Exporting current models...');
                    };

                    const importVoiceBanks = () => {
                        alert('🎵 Voice bank import interface will open...');
                    };

                    const exportVoiceBanks = () => {
                        alert('🔊 Exporting voice banks...');
                    };

                    const openPrometheus = () => {
                        window.open('http://localhost:9090', '_blank');
                    };

                    const openGrafana = () => {
                        window.open('http://localhost:3001', '_blank');
                    };

                    const systemDiagnostics = () => {
                        alert('🔧 Running comprehensive system diagnostics...');
                    };

                    const optimizePerformance = () => {
                        alert('⚡ Optimizing system performance...');
                    };
                    
                    return (
                        <div>
                            <div className="dashboard">
                                {/* Cost & Budget Panel */}
                                <div className="panel">
                                    <div className="rivet-bottom-left"></div>
                                    <div className="rivet-bottom-right"></div>
                                    <h3 className="panel-title">💰 Cost & Budget</h3>
                                    <div className="metric">
                                        <span className="metric-label">Hourly Spent:</span>
                                        <span className="metric-value">${budget.hourly_spent?.toFixed(4) || '0.0000'}</span>
                                    </div>
                                    <div className="metric">
                                        <span className="metric-label">Daily Spent:</span>
                                        <span className="metric-value">${budget.daily_spent?.toFixed(4) || '0.0000'}</span>
                                    </div>
                                    <div className="metric">
                                        <span className="metric-label">Burn Rate:</span>
                                        <span className="metric-value">${budget.burn_rate?.toFixed(4) || '0.0000'}/hr</span>
                                    </div>
                                    <div className="metric">
                                        <span className="metric-label">Alert Level:</span>
                                        <span className={`metric-value alert-${budget.alert_level || 'green'}`}>
                                            {budget.alert_level?.toUpperCase() || 'GREEN'}
                                        </span>
                                    </div>
                                </div>
                                
                                {/* Resource Monitoring Panel */}
                                <div className="panel">
                                    <div className="rivet-bottom-left"></div>
                                    <div className="rivet-bottom-right"></div>
                                    <h3 className="panel-title">📊 Resource Usage</h3>
                                    <div className="metric">
                                        <span className="metric-label">CPU Usage:</span>
                                        <span className="metric-value">{resources.cpu_usage?.toFixed(1) || '0.0'}%</span>
                                    </div>
                                    <div className="metric">
                                        <span className="metric-label">Memory Usage:</span>
                                        <span className="metric-value">{resources.memory_usage?.toFixed(1) || '0.0'}%</span>
                                    </div>
                                    <div className="metric">
                                        <span className="metric-label">Active Algorithms:</span>
                                        <span className="metric-value">{resources.active_algorithms || 0}</span>
                                    </div>
                                    <div className="metric">
                                        <span className="metric-label">Queue Length:</span>
                                        <span className="metric-value">{resources.queue_length || 0}</span>
                                    </div>
                                </div>
                                
                                {/* Swarm Configuration Panel */}
                                <div className="panel">
                                    <div className="rivet-bottom-left"></div>
                                    <div className="rivet-bottom-right"></div>
                                    <h3 className="panel-title">🤖 Swarm Configuration</h3>
                                    <div className="control-group">
                                        <label className="control-label">Reasoning Agents: {config.reasoning_agents || 3}</label>
                                        <input 
                                            type="range" 
                                            min="1" 
                                            max="10" 
                                            value={config.reasoning_agents || 3}
                                            className="slider"
                                            onChange={(e) => updateConfig({...config, reasoning_agents: parseInt(e.target.value)})}
                                        />
                                    </div>
                                    <div className="control-group">
                                        <label className="control-label">Technical Agents: {config.technical_agents || 2}</label>
                                        <input 
                                            type="range" 
                                            min="1" 
                                            max="10" 
                                            value={config.technical_agents || 2}
                                            className="slider"
                                            onChange={(e) => updateConfig({...config, technical_agents: parseInt(e.target.value)})}
                                        />
                                    </div>
                                    <div className="control-group">
                                        <label className="control-label">Quality Threshold: {(config.quality_threshold * 100 || 85).toFixed(0)}%</label>
                                        <input 
                                            type="range" 
                                            min="50" 
                                            max="100" 
                                            value={config.quality_threshold * 100 || 85}
                                            className="slider"
                                            onChange={(e) => updateConfig({...config, quality_threshold: parseInt(e.target.value) / 100})}
                                        />
                                    </div>
                                    <button className="button emergency-button" onClick={emergencyStop}>
                                        🚨 Emergency Stop
                                    </button>
                                </div>
                            </div>

                            {/* Additional Control Buttons */}
                            <div className="additional-controls">
                                <button className="control-button" onClick={importModels}>
                                    📥 Import AI Models
                                </button>
                                <button className="control-button" onClick={exportModels}>
                                    📤 Export AI Models
                                </button>
                                <button className="control-button" onClick={importVoiceBanks}>
                                    🎵 Import Voice Banks
                                </button>
                                <button className="control-button" onClick={exportVoiceBanks}>
                                    🔊 Export Voice Banks
                                </button>
                                <button className="control-button" onClick={openPrometheus}>
                                    📈 Prometheus Metrics
                                </button>
                                <button className="control-button" onClick={openGrafana}>
                                    📊 Grafana Dashboard
                                </button>
                                <button className="control-button" onClick={systemDiagnostics}>
                                    🔧 System Diagnostics
                                </button>
                                <button className="control-button" onClick={optimizePerformance}>
                                    ⚡ Optimize Performance
                                </button>
                            </div>
                        </div>
                    );
                }
                
                ReactDOM.render(<Dashboard />, document.getElementById('root'));
            </script>
        </body>
        </html>
        """
    
    def start(self, host: str = "0.0.0.0", port: int = 3000):
        """Start the dashboard server"""
        self.resource_monitor.start_monitoring()
        uvicorn.run(self.app, host=host, port=port)
    
    def stop(self):
        """Stop the dashboard server"""
        self.resource_monitor.stop_monitoring()

if __name__ == "__main__":
    dashboard = SwarmControlDashboard()
    dashboard.start()

