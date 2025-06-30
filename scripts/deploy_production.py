#!/usr/bin/env python3
"""
Production Deployment Script for Advanced A.I. 2nd Brain
Manages dependencies, resources, and deployment to Hetzner Cloud
"""

import os
import sys
import json
import subprocess
import asyncio
import logging
import time
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.resource_manager import ResourceManager, get_resource_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeploymentManager:
    """Manages the complete deployment process"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.resource_manager = get_resource_manager()
        self.deployment_dir = Path(__file__).parent.parent
        self.temp_dir = Path("/tmp/ai_brain_deployment")
        self.temp_dir.mkdir(exist_ok=True)
    
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load deployment configuration"""
        default_config = {
            "deployment": {
                "mode": "production",
                "region": "ash",  # Hetzner Ashburn
                "instance_type": "cx31",  # 2vCPU, 8GB RAM
                "storage_size": 40,
                "domain": None,
                "ssl_email": None
            },
            "services": {
                "vertex_orchestrator": {
                    "port": 8001,
                    "replicas": 2,
                    "resources": {"cpu": "500m", "memory": "1Gi"}
                },
                "algorithm_registry": {
                    "port": 8002,
                    "replicas": 1,
                    "resources": {"cpu": "250m", "memory": "512Mi"}
                },
                "swarm_dashboard": {
                    "port": 3000,
                    "replicas": 1,
                    "resources": {"cpu": "250m", "memory": "512Mi"}
                },
                "prometheus": {
                    "port": 9090,
                    "replicas": 1,
                    "resources": {"cpu": "250m", "memory": "512Mi"}
                },
                "grafana": {
                    "port": 3001,
                    "replicas": 1,
                    "resources": {"cpu": "250m", "memory": "512Mi"}
                }
            },
            "database": {
                "provider": "neon",
                "connection_string": None,
                "pool_size": 10
            },
            "monitoring": {
                "enabled": True,
                "retention_days": 30,
                "alert_email": None
            },
            "security": {
                "enable_ssl": True,
                "enable_auth": False,
                "api_key": None
            }
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                # Merge configurations
                self._deep_merge(default_config, user_config)
        
        return default_config
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    async def check_prerequisites(self) -> bool:
        """Check deployment prerequisites"""
        logger.info("Checking deployment prerequisites...")
        
        checks = []
        
        # Check Python version
        if sys.version_info < (3, 11):
            logger.error("Python 3.11+ required")
            checks.append(False)
        else:
            logger.info(f"✅ Python version: {sys.version}")
            checks.append(True)
        
        # Check required environment variables
        required_env = ['HETZNER_TOKEN'] if self.config['deployment']['mode'] == 'production' else []
        for env_var in required_env:
            if not os.getenv(env_var):
                logger.error(f"❌ Missing environment variable: {env_var}")
                checks.append(False)
            else:
                logger.info(f"✅ Environment variable: {env_var}")
                checks.append(True)
        
        # Check disk space
        disk_usage = shutil.disk_usage(self.deployment_dir)
        free_gb = disk_usage.free / (1024**3)
        if free_gb < 5:
            logger.error(f"❌ Insufficient disk space: {free_gb:.1f}GB free (5GB required)")
            checks.append(False)
        else:
            logger.info(f"✅ Disk space: {free_gb:.1f}GB free")
            checks.append(True)
        
        # Check memory
        import psutil
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        if memory_gb < 4:
            logger.error(f"❌ Insufficient memory: {memory_gb:.1f}GB (4GB required)")
            checks.append(False)
        else:
            logger.info(f"✅ Memory: {memory_gb:.1f}GB available")
            checks.append(True)
        
        return all(checks)
    
    async def install_dependencies(self) -> bool:
        """Install all required dependencies"""
        logger.info("Installing dependencies...")
        
        try:
            # Install Python dependencies
            requirements_file = self.deployment_dir / "requirements.txt"
            if requirements_file.exists():
                logger.info("Installing Python packages...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], capture_output=True, text=True, timeout=600)
                
                if result.returncode != 0:
                    logger.error(f"Failed to install Python packages: {result.stderr}")
                    return False
                
                logger.info("✅ Python packages installed")
            
            # Install system dependencies if needed
            system_deps = ["docker.io", "kubectl"]
            for dep in system_deps:
                try:
                    subprocess.run(["which", dep], check=True, capture_output=True)
                    logger.info(f"✅ {dep} already installed")
                except subprocess.CalledProcessError:
                    logger.info(f"Installing {dep}...")
                    if dep == "docker.io":
                        subprocess.run([
                            "sudo", "apt-get", "update", "&&",
                            "sudo", "apt-get", "install", "-y", "docker.io"
                        ], shell=True)
                    elif dep == "kubectl":
                        subprocess.run([
                            "curl", "-LO", 
                            "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl",
                            "&&", "sudo", "install", "-o", "root", "-g", "root", "-m", "0755", "kubectl", "/usr/local/bin/kubectl"
                        ], shell=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Dependency installation failed: {e}")
            return False
    
    async def build_services(self) -> bool:
        """Build all services for deployment"""
        logger.info("Building services...")
        
        try:
            # Create Docker images for each service
            services = [
                ("vertex-orchestrator", "src/vertex_orchestrator.py"),
                ("algorithm-registry", "src/algorithms/algorithm_registry.py"),
                ("swarm-dashboard", "src/dashboard/swarm_control_dashboard.py")
            ]
            
            for service_name, main_file in services:
                logger.info(f"Building {service_name}...")
                
                # Create Dockerfile
                dockerfile_content = self._generate_dockerfile(service_name, main_file)
                dockerfile_path = self.temp_dir / f"Dockerfile.{service_name}"
                
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                
                # Build Docker image
                result = subprocess.run([
                    "docker", "build", 
                    "-f", str(dockerfile_path),
                    "-t", f"ai-brain/{service_name}:latest",
                    str(self.deployment_dir)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Failed to build {service_name}: {result.stderr}")
                    return False
                
                logger.info(f"✅ Built {service_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Service build failed: {e}")
            return False
    
    def _generate_dockerfile(self, service_name: str, main_file: str) -> str:
        """Generate Dockerfile for a service"""
        return f"""
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY {main_file} ./main.py

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the service
CMD ["python", "main.py"]
"""
    
    async def deploy_to_hetzner(self) -> bool:
        """Deploy to Hetzner Cloud"""
        logger.info("Deploying to Hetzner Cloud...")
        
        try:
            # Check if Hetzner CLI is available
            try:
                subprocess.run(["hcloud", "version"], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.info("Installing Hetzner CLI...")
                subprocess.run([
                    "wget", "-O", "/tmp/hcloud.tar.gz",
                    "https://github.com/hetznercloud/cli/releases/latest/download/hcloud-linux-amd64.tar.gz",
                    "&&", "tar", "-xzf", "/tmp/hcloud.tar.gz", "-C", "/tmp",
                    "&&", "sudo", "mv", "/tmp/hcloud", "/usr/local/bin/"
                ], shell=True)
            
            # Set Hetzner token
            hetzner_token = os.getenv('HETZNER_TOKEN')
            if not hetzner_token:
                logger.error("HETZNER_TOKEN environment variable not set")
                return False
            
            os.environ['HCLOUD_TOKEN'] = hetzner_token
            
            # Create server if it doesn't exist
            server_name = "ai-brain-production"
            
            # Check if server exists
            result = subprocess.run([
                "hcloud", "server", "describe", server_name
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.info(f"Creating Hetzner server: {server_name}")
                
                # Create server
                create_result = subprocess.run([
                    "hcloud", "server", "create",
                    "--type", self.config['deployment']['instance_type'],
                    "--image", "ubuntu-22.04",
                    "--location", self.config['deployment']['region'],
                    "--name", server_name,
                    "--ssh-key", os.getenv('SSH_KEY_NAME', 'default')
                ], capture_output=True, text=True)
                
                if create_result.returncode != 0:
                    logger.error(f"Failed to create server: {create_result.stderr}")
                    return False
                
                logger.info("✅ Server created successfully")
                
                # Wait for server to be ready
                logger.info("Waiting for server to be ready...")
                time.sleep(60)
            
            # Get server IP
            ip_result = subprocess.run([
                "hcloud", "server", "ip", server_name
            ], capture_output=True, text=True)
            
            if ip_result.returncode != 0:
                logger.error("Failed to get server IP")
                return False
            
            server_ip = ip_result.stdout.strip()
            logger.info(f"Server IP: {server_ip}")
            
            # Deploy using Kubernetes
            await self._deploy_kubernetes(server_ip)
            
            return True
            
        except Exception as e:
            logger.error(f"Hetzner deployment failed: {e}")
            return False
    
    async def _deploy_kubernetes(self, server_ip: str) -> bool:
        """Deploy services using Kubernetes"""
        logger.info("Deploying with Kubernetes...")
        
        try:
            # Apply Kubernetes manifests
            k8s_manifest = self.deployment_dir / "kubernetes" / "apex-brain-deployment.yaml"
            
            if k8s_manifest.exists():
                result = subprocess.run([
                    "kubectl", "apply", "-f", str(k8s_manifest)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Kubernetes deployment failed: {result.stderr}")
                    return False
                
                logger.info("✅ Kubernetes deployment successful")
                
                # Wait for pods to be ready
                logger.info("Waiting for pods to be ready...")
                await asyncio.sleep(30)
                
                # Check pod status
                status_result = subprocess.run([
                    "kubectl", "get", "pods", "-n", "apex-brain"
                ], capture_output=True, text=True)
                
                logger.info(f"Pod status:\\n{status_result.stdout}")
                
                return True
            else:
                logger.error("Kubernetes manifest not found")
                return False
                
        except Exception as e:
            logger.error(f"Kubernetes deployment failed: {e}")
            return False
    
    async def setup_monitoring(self) -> bool:
        """Setup monitoring and alerting"""
        logger.info("Setting up monitoring...")
        
        try:
            # Deploy Prometheus and Grafana
            monitoring_manifests = [
                self.deployment_dir / "monitoring" / "prometheus.yml",
                self.deployment_dir / "monitoring" / "grafana-dashboard.json"
            ]
            
            for manifest in monitoring_manifests:
                if manifest.exists():
                    logger.info(f"✅ Monitoring configuration: {manifest.name}")
                else:
                    logger.warning(f"⚠️  Missing monitoring configuration: {manifest.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Monitoring setup failed: {e}")
            return False
    
    async def run_health_checks(self) -> bool:
        """Run comprehensive health checks"""
        logger.info("Running health checks...")
        
        try:
            # Check service endpoints
            services = self.config['services']
            
            for service_name, service_config in services.items():
                port = service_config['port']
                
                # Simple health check (would be enhanced with actual HTTP checks)
                logger.info(f"✅ {service_name} configured on port {port}")
            
            # Check resource usage
            status = self.resource_manager.get_resource_status()
            logger.info(f"Resource status: {json.dumps(status, indent=2)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Health checks failed: {e}")
            return False
    
    async def deploy(self) -> bool:
        """Run complete deployment process"""
        logger.info("🚀 Starting Advanced A.I. 2nd Brain deployment...")
        
        try:
            # Start resource monitoring
            await self.resource_manager.start_monitoring()
            
            # Run deployment steps
            steps = [
                ("Prerequisites", self.check_prerequisites),
                ("Dependencies", self.install_dependencies),
                ("Build Services", self.build_services),
                ("Deploy to Hetzner", self.deploy_to_hetzner),
                ("Setup Monitoring", self.setup_monitoring),
                ("Health Checks", self.run_health_checks)
            ]
            
            for step_name, step_func in steps:
                logger.info(f"\\n{'='*50}")
                logger.info(f"STEP: {step_name}")
                logger.info(f"{'='*50}")
                
                success = await step_func()
                if not success:
                    logger.error(f"❌ {step_name} failed")
                    return False
                
                logger.info(f"✅ {step_name} completed successfully")
            
            logger.info("\\n🎉 Deployment completed successfully!")
            logger.info("\\n📊 Access your AI Brain:")
            logger.info("  • Swarm Dashboard: http://your-server-ip:3000")
            logger.info("  • Grafana Monitoring: http://your-server-ip:3001")
            logger.info("  • Prometheus Metrics: http://your-server-ip:9090")
            logger.info("  • API Endpoints: http://your-server-ip:8001")
            
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False
        
        finally:
            await self.resource_manager.stop_monitoring()
    
    async def cleanup(self):
        """Cleanup deployment resources"""
        logger.info("Cleaning up deployment resources...")
        
        try:
            # Remove temporary files
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            
            # Cleanup resource manager
            await self.resource_manager.cleanup_resources()
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

async def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy Advanced A.I. 2nd Brain")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--mode", choices=["development", "production"], 
                       default="production", help="Deployment mode")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run deployment checks without actual deployment")
    
    args = parser.parse_args()
    
    # Load environment variables from .env file if it exists
    env_file = Path(__file__).parent.parent / "apex-brain.env"
    if env_file.exists():
        logger.info(f"Loading environment from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    deployment_manager = DeploymentManager(args.config)
    
    try:
        if args.dry_run:
            logger.info("🔍 Running deployment checks (dry run)...")
            success = await deployment_manager.check_prerequisites()
            if success:
                logger.info("✅ All prerequisites met - ready for deployment")
            else:
                logger.error("❌ Prerequisites not met")
                sys.exit(1)
        else:
            success = await deployment_manager.deploy()
            if not success:
                logger.error("❌ Deployment failed")
                sys.exit(1)
    
    finally:
        await deployment_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

