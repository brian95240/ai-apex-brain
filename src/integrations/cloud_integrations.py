#!/usr/bin/env python3
"""
Seamless Cloud Integrations for AI Apex Brain
Provides unified interface for Neon, Hetzner, WebThinker, and Spider.cloud
"""

import asyncio
import json
import os
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import aiohttp
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from datetime import datetime, timedelta
import hashlib
import base64

logger = logging.getLogger(__name__)

@dataclass
class CloudConfig:
    """Cloud service configuration"""
    neon_database_url: str
    hetzner_api_token: str
    webthinker_api_key: str
    spider_cloud_api_key: str
    redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 3600  # 1 hour default cache

@dataclass
class DeploymentStatus:
    """Deployment status tracking"""
    service_name: str
    status: str  # "pending", "deploying", "running", "failed", "stopped"
    url: Optional[str] = None
    health_check_url: Optional[str] = None
    last_updated: datetime = None
    resource_usage: Dict[str, float] = None
    logs: List[str] = None

class NeonDatabaseManager:
    """Neon PostgreSQL database management"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection_pool = None
    
    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            # Create tables for AI brain data
            await self._create_tables()
            logger.info("Neon database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neon database: {e}")
            raise
    
    async def _create_tables(self):
        """Create necessary tables for AI brain operations"""
        tables = {
            "algorithm_executions": """
                CREATE TABLE IF NOT EXISTS algorithm_executions (
                    id SERIAL PRIMARY KEY,
                    algorithm_name VARCHAR(255) NOT NULL,
                    input_data JSONB,
                    output_data JSONB,
                    execution_time FLOAT,
                    success BOOLEAN,
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resource_usage JSONB
                );
            """,
            "swarm_configurations": """
                CREATE TABLE IF NOT EXISTS swarm_configurations (
                    id SERIAL PRIMARY KEY,
                    config_name VARCHAR(255) UNIQUE NOT NULL,
                    reasoning_agents INTEGER,
                    technical_agents INTEGER,
                    creative_agents INTEGER,
                    analytical_agents INTEGER,
                    quality_threshold FLOAT,
                    budget_limit_hourly FLOAT,
                    budget_limit_daily FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """,
            "cost_tracking": """
                CREATE TABLE IF NOT EXISTS cost_tracking (
                    id SERIAL PRIMARY KEY,
                    service_type VARCHAR(100),
                    operation_type VARCHAR(100),
                    cost_amount DECIMAL(10,6),
                    currency VARCHAR(3) DEFAULT 'USD',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                );
            """,
            "model_registry": """
                CREATE TABLE IF NOT EXISTS model_registry (
                    id SERIAL PRIMARY KEY,
                    model_name VARCHAR(255) UNIQUE NOT NULL,
                    model_type VARCHAR(100),
                    version VARCHAR(50),
                    file_path TEXT,
                    metadata JSONB,
                    performance_metrics JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """,
            "voice_banks": """
                CREATE TABLE IF NOT EXISTS voice_banks (
                    id SERIAL PRIMARY KEY,
                    voice_name VARCHAR(255) UNIQUE NOT NULL,
                    voice_type VARCHAR(100),
                    language VARCHAR(10),
                    file_path TEXT,
                    metadata JSONB,
                    quality_score FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
        }
        
        conn = psycopg2.connect(self.database_url)
        try:
            with conn.cursor() as cursor:
                for table_name, create_sql in tables.items():
                    cursor.execute(create_sql)
                    logger.info(f"Created/verified table: {table_name}")
            conn.commit()
        finally:
            conn.close()
    
    async def log_algorithm_execution(self, algorithm_name: str, input_data: Dict, 
                                    output_data: Dict, execution_time: float, 
                                    success: bool, error_message: str = None,
                                    resource_usage: Dict = None):
        """Log algorithm execution to database"""
        conn = psycopg2.connect(self.database_url)
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO algorithm_executions 
                    (algorithm_name, input_data, output_data, execution_time, 
                     success, error_message, resource_usage)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (algorithm_name, json.dumps(input_data), json.dumps(output_data),
                      execution_time, success, error_message, 
                      json.dumps(resource_usage) if resource_usage else None))
            conn.commit()
        finally:
            conn.close()
    
    async def get_algorithm_performance(self, algorithm_name: str, 
                                      days: int = 7) -> Dict[str, Any]:
        """Get algorithm performance metrics"""
        conn = psycopg2.connect(self.database_url)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_executions,
                        AVG(execution_time) as avg_execution_time,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate,
                        MIN(timestamp) as first_execution,
                        MAX(timestamp) as last_execution
                    FROM algorithm_executions 
                    WHERE algorithm_name = %s 
                    AND timestamp >= NOW() - INTERVAL '%s days'
                """, (algorithm_name, days))
                
                result = cursor.fetchone()
                return dict(result) if result else {}
        finally:
            conn.close()

class HetznerCloudManager:
    """Hetzner Cloud infrastructure management"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.hetzner.cloud/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    async def create_server(self, name: str, server_type: str = "cx11", 
                          image: str = "ubuntu-22.04", location: str = "nbg1") -> Dict:
        """Create a new Hetzner Cloud server"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "name": name,
                "server_type": server_type,
                "image": image,
                "location": location,
                "start_after_create": True,
                "user_data": self._get_cloud_init_script()
            }
            
            async with session.post(
                f"{self.base_url}/servers",
                headers=self.headers,
                json=payload
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    logger.info(f"Created Hetzner server: {name}")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Failed to create server: {error}")
                    raise Exception(f"Server creation failed: {error}")
    
    async def list_servers(self) -> List[Dict]:
        """List all Hetzner Cloud servers"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/servers",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("servers", [])
                else:
                    logger.error(f"Failed to list servers: {await response.text()}")
                    return []
    
    async def delete_server(self, server_id: int) -> bool:
        """Delete a Hetzner Cloud server"""
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.base_url}/servers/{server_id}",
                headers=self.headers
            ) as response:
                if response.status == 204:
                    logger.info(f"Deleted Hetzner server: {server_id}")
                    return True
                else:
                    logger.error(f"Failed to delete server: {await response.text()}")
                    return False
    
    async def get_server_metrics(self, server_id: int) -> Dict:
        """Get server performance metrics"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/servers/{server_id}/metrics",
                headers=self.headers,
                params={"type": "cpu,disk,network", "start": "2023-01-01T00:00:00Z"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get metrics: {await response.text()}")
                    return {}
    
    def _get_cloud_init_script(self) -> str:
        """Get cloud-init script for server setup"""
        return """#cloud-config
packages:
  - docker.io
  - docker-compose
  - python3-pip
  - git
  - curl

runcmd:
  - systemctl enable docker
  - systemctl start docker
  - usermod -aG docker ubuntu
  - pip3 install fastapi uvicorn prometheus-client
  - git clone https://github.com/brian95240/ai-apex-brain.git /opt/ai-apex-brain
  - cd /opt/ai-apex-brain && python3 -m pip install -r requirements.txt
"""

class WebThinkerIntegration:
    """WebThinker API integration for enhanced reasoning"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.webthinker.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def enhance_reasoning(self, query: str, context: Dict = None) -> Dict:
        """Enhance reasoning using WebThinker AI"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "query": query,
                "context": context or {},
                "reasoning_depth": "deep",
                "include_sources": True,
                "max_tokens": 2000
            }
            
            async with session.post(
                f"{self.base_url}/reasoning/enhance",
                headers=self.headers,
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("WebThinker reasoning enhancement completed")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"WebThinker API error: {error}")
                    return {"error": error, "fallback": True}
    
    async def fact_check(self, claims: List[str]) -> Dict:
        """Fact-check claims using WebThinker"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "claims": claims,
                "include_sources": True,
                "confidence_threshold": 0.8
            }
            
            async with session.post(
                f"{self.base_url}/factcheck",
                headers=self.headers,
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Fact-check failed: {await response.text()}")
                    return {"error": "Fact-check service unavailable"}

class SpiderCloudIntegration:
    """Spider.cloud integration for web scraping and data collection"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.spider.cloud/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def scrape_url(self, url: str, options: Dict = None) -> Dict:
        """Scrape a URL using Spider.cloud"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "url": url,
                "options": options or {
                    "include_links": True,
                    "include_images": False,
                    "wait_for": "networkidle",
                    "timeout": 30000
                }
            }
            
            async with session.post(
                f"{self.base_url}/scrape",
                headers=self.headers,
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Successfully scraped: {url}")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Spider.cloud scraping failed: {error}")
                    return {"error": error, "url": url}
    
    async def batch_scrape(self, urls: List[str], options: Dict = None) -> List[Dict]:
        """Batch scrape multiple URLs"""
        tasks = [self.scrape_url(url, options) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "error": str(result),
                    "url": urls[i]
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def monitor_website(self, url: str, check_interval: int = 3600) -> str:
        """Set up website monitoring"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "url": url,
                "check_interval": check_interval,
                "alert_on_change": True,
                "alert_on_error": True
            }
            
            async with session.post(
                f"{self.base_url}/monitor",
                headers=self.headers,
                json=payload
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    monitor_id = result.get("monitor_id")
                    logger.info(f"Website monitoring setup for {url}: {monitor_id}")
                    return monitor_id
                else:
                    error = await response.text()
                    logger.error(f"Failed to setup monitoring: {error}")
                    return None

class CloudIntegrationOrchestrator:
    """Main orchestrator for all cloud integrations"""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.neon_db = NeonDatabaseManager(config.neon_database_url)
        self.hetzner = HetznerCloudManager(config.hetzner_api_token)
        self.webthinker = WebThinkerIntegration(config.webthinker_api_key)
        self.spider_cloud = SpiderCloudIntegration(config.spider_cloud_api_key)
        
        # Redis for caching and coordination
        self.redis_client = redis.from_url(config.redis_url)
        
        # Deployment tracking
        self.deployments: Dict[str, DeploymentStatus] = {}
    
    async def initialize(self):
        """Initialize all cloud integrations"""
        try:
            await self.neon_db.initialize()
            logger.info("All cloud integrations initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize cloud integrations: {e}")
            raise
    
    async def deploy_ai_brain_cluster(self, cluster_name: str, 
                                    node_count: int = 3) -> Dict[str, Any]:
        """Deploy AI brain cluster on Hetzner Cloud"""
        deployment_id = f"cluster-{cluster_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        try:
            # Update deployment status
            self.deployments[deployment_id] = DeploymentStatus(
                service_name=cluster_name,
                status="deploying",
                last_updated=datetime.now()
            )
            
            # Create servers
            servers = []
            for i in range(node_count):
                server_name = f"{cluster_name}-node-{i+1}"
                server = await self.hetzner.create_server(
                    name=server_name,
                    server_type="cx21",  # 2 vCPU, 4GB RAM
                    image="ubuntu-22.04"
                )
                servers.append(server)
                
                # Wait a bit between server creations
                await asyncio.sleep(5)
            
            # Update deployment status
            self.deployments[deployment_id].status = "running"
            self.deployments[deployment_id].url = f"http://{servers[0]['server']['public_net']['ipv4']['ip']}:3000"
            
            # Log deployment to database
            await self.neon_db.log_algorithm_execution(
                algorithm_name="cluster_deployment",
                input_data={"cluster_name": cluster_name, "node_count": node_count},
                output_data={"deployment_id": deployment_id, "servers": len(servers)},
                execution_time=0.0,  # Will be calculated
                success=True
            )
            
            logger.info(f"Successfully deployed cluster: {deployment_id}")
            return {
                "deployment_id": deployment_id,
                "servers": servers,
                "status": "running",
                "dashboard_url": self.deployments[deployment_id].url
            }
            
        except Exception as e:
            self.deployments[deployment_id].status = "failed"
            logger.error(f"Cluster deployment failed: {e}")
            raise
    
    async def enhanced_query_processing(self, query: str, 
                                      use_webthinker: bool = True,
                                      scrape_sources: bool = True) -> Dict[str, Any]:
        """Process query with enhanced cloud capabilities"""
        start_time = datetime.now()
        
        try:
            # Base processing
            result = {
                "query": query,
                "timestamp": start_time.isoformat(),
                "enhanced_reasoning": None,
                "scraped_data": None,
                "fact_check": None
            }
            
            # Enhance reasoning with WebThinker
            if use_webthinker:
                reasoning_result = await self.webthinker.enhance_reasoning(query)
                result["enhanced_reasoning"] = reasoning_result
            
            # Scrape relevant sources if needed
            if scrape_sources and "http" in query.lower():
                # Extract URLs from query
                import re
                urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', query)
                if urls:
                    scraped_data = await self.spider_cloud.batch_scrape(urls[:3])  # Limit to 3 URLs
                    result["scraped_data"] = scraped_data
            
            # Fact-check if claims are present
            if any(word in query.lower() for word in ["claim", "fact", "true", "false", "verify"]):
                fact_check_result = await self.webthinker.fact_check([query])
                result["fact_check"] = fact_check_result
            
            # Log to database
            execution_time = (datetime.now() - start_time).total_seconds()
            await self.neon_db.log_algorithm_execution(
                algorithm_name="enhanced_query_processing",
                input_data={"query": query, "use_webthinker": use_webthinker, "scrape_sources": scrape_sources},
                output_data=result,
                execution_time=execution_time,
                success=True
            )
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            await self.neon_db.log_algorithm_execution(
                algorithm_name="enhanced_query_processing",
                input_data={"query": query},
                output_data={},
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
            raise
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentStatus]:
        """Get deployment status"""
        return self.deployments.get(deployment_id)
    
    async def cleanup_deployment(self, deployment_id: str) -> bool:
        """Clean up a deployment"""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return False
        
        try:
            # Get servers for this deployment
            servers = await self.hetzner.list_servers()
            cluster_name = deployment.service_name
            
            # Delete servers
            for server in servers:
                if cluster_name in server["name"]:
                    await self.hetzner.delete_server(server["id"])
            
            # Update status
            deployment.status = "stopped"
            deployment.last_updated = datetime.now()
            
            logger.info(f"Cleaned up deployment: {deployment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup deployment {deployment_id}: {e}")
            return False
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health across all cloud services"""
        health = {
            "timestamp": datetime.now().isoformat(),
            "neon_database": "unknown",
            "hetzner_cloud": "unknown",
            "webthinker": "unknown",
            "spider_cloud": "unknown",
            "redis_cache": "unknown",
            "active_deployments": len([d for d in self.deployments.values() if d.status == "running"])
        }
        
        # Check Neon database
        try:
            conn = psycopg2.connect(self.config.neon_database_url)
            conn.close()
            health["neon_database"] = "healthy"
        except Exception:
            health["neon_database"] = "unhealthy"
        
        # Check Hetzner Cloud
        try:
            servers = await self.hetzner.list_servers()
            health["hetzner_cloud"] = "healthy"
            health["hetzner_servers"] = len(servers)
        except Exception:
            health["hetzner_cloud"] = "unhealthy"
        
        # Check Redis
        try:
            self.redis_client.ping()
            health["redis_cache"] = "healthy"
        except Exception:
            health["redis_cache"] = "unhealthy"
        
        # Test WebThinker and Spider.cloud with simple requests
        try:
            await self.webthinker.enhance_reasoning("test query")
            health["webthinker"] = "healthy"
        except Exception:
            health["webthinker"] = "unhealthy"
        
        try:
            await self.spider_cloud.scrape_url("https://httpbin.org/get")
            health["spider_cloud"] = "healthy"
        except Exception:
            health["spider_cloud"] = "unhealthy"
        
        return health

# Example usage and configuration
async def main():
    """Example usage of cloud integrations"""
    config = CloudConfig(
        neon_database_url=os.getenv("NEON_DATABASE_URL", "postgresql://user:pass@localhost/aiapexbrain"),
        hetzner_api_token=os.getenv("HETZNER_TOKEN", "your-hetzner-token"),
        webthinker_api_key=os.getenv("WEBTHINKER_API_KEY", "your-webthinker-key"),
        spider_cloud_api_key=os.getenv("SPIDER_CLOUD_API_KEY", "your-spider-key")
    )
    
    orchestrator = CloudIntegrationOrchestrator(config)
    await orchestrator.initialize()
    
    # Example: Deploy AI brain cluster
    # deployment = await orchestrator.deploy_ai_brain_cluster("production", node_count=3)
    # print(f"Deployment: {deployment}")
    
    # Example: Enhanced query processing
    # result = await orchestrator.enhanced_query_processing("What are the latest AI developments?")
    # print(f"Enhanced result: {result}")
    
    # Check system health
    health = await orchestrator.get_system_health()
    print(f"System health: {health}")

if __name__ == "__main__":
    asyncio.run(main())

