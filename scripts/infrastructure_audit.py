#!/usr/bin/env python3
"""
Infrastructure Audit Script for Advanced A.I. 2nd Brain
Checks for existing Hetzner Cloud and Neon Database resources to avoid redundancy
"""

import os
import sys
import json
import subprocess
import requests
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import psycopg2
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HetznerServer:
    """Hetzner server information"""
    id: int
    name: str
    status: str
    server_type: str
    public_ip: str
    private_ip: str
    datacenter: str
    created: str
    labels: Dict[str, str]

@dataclass
class KubernetesCluster:
    """Kubernetes cluster information"""
    id: int
    name: str
    status: str
    version: str
    node_count: int
    public_endpoint: str
    created: str

@dataclass
class NeonDatabase:
    """Neon database information"""
    id: str
    name: str
    status: str
    region: str
    connection_string: str
    created: str

@dataclass
class InfrastructureAudit:
    """Complete infrastructure audit results"""
    hetzner_servers: List[HetznerServer]
    kubernetes_clusters: List[KubernetesCluster]
    neon_databases: List[NeonDatabase]
    existing_services: List[Dict[str, Any]]
    recommendations: List[str]

class HetznerAuditor:
    """Audits Hetzner Cloud infrastructure"""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv('HETZNER_TOKEN')
        self.base_url = "https://api.hetzner.cloud/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        } if self.api_token else {}
    
    def check_api_access(self) -> bool:
        """Check if we have valid API access"""
        if not self.api_token:
            logger.warning("No Hetzner API token provided")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/servers", headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to access Hetzner API: {e}")
            return False
    
    def get_servers(self) -> List[HetznerServer]:
        """Get all Hetzner servers"""
        if not self.check_api_access():
            return []
        
        try:
            response = requests.get(f"{self.base_url}/servers", headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to get servers: {response.status_code}")
                return []
            
            data = response.json()
            servers = []
            
            for server_data in data.get('servers', []):
                server = HetznerServer(
                    id=server_data['id'],
                    name=server_data['name'],
                    status=server_data['status'],
                    server_type=server_data['server_type']['name'],
                    public_ip=server_data['public_net']['ipv4']['ip'] if server_data['public_net']['ipv4'] else '',
                    private_ip=server_data['private_net'][0]['ip'] if server_data['private_net'] else '',
                    datacenter=server_data['datacenter']['name'],
                    created=server_data['created'],
                    labels=server_data.get('labels', {})
                )
                servers.append(server)
            
            return servers
            
        except Exception as e:
            logger.error(f"Error getting Hetzner servers: {e}")
            return []
    
    def get_kubernetes_clusters(self) -> List[KubernetesCluster]:
        """Get all Kubernetes clusters"""
        if not self.check_api_access():
            return []
        
        try:
            # Note: This endpoint might not be available in all Hetzner accounts
            response = requests.get(f"{self.base_url}/kubernetes/clusters", headers=self.headers)
            if response.status_code != 200:
                logger.info("No Kubernetes clusters found or API not available")
                return []
            
            data = response.json()
            clusters = []
            
            for cluster_data in data.get('kubernetes_clusters', []):
                cluster = KubernetesCluster(
                    id=cluster_data['id'],
                    name=cluster_data['name'],
                    status=cluster_data['status'],
                    version=cluster_data['version'],
                    node_count=len(cluster_data.get('node_pools', [])),
                    public_endpoint=cluster_data.get('public_endpoint', ''),
                    created=cluster_data['created']
                )
                clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error getting Kubernetes clusters: {e}")
            return []

class NeonAuditor:
    """Audits Neon Database infrastructure"""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv('NEON_DATABASE_URL')
    
    def check_database_connection(self) -> bool:
        """Check if we can connect to Neon database"""
        if not self.connection_string:
            logger.warning("No Neon database connection string provided")
            return False
        
        try:
            conn = psycopg2.connect(self.connection_string)
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neon database: {e}")
            return False
    
    def get_database_info(self) -> Optional[NeonDatabase]:
        """Get Neon database information"""
        if not self.check_database_connection():
            return None
        
        try:
            parsed_url = urlparse(self.connection_string)
            
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Get database version and basic info
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()[0]
            
            cursor.execute("SELECT pg_database_size(current_database());")
            db_size = cursor.fetchone()[0]
            
            conn.close()
            
            return NeonDatabase(
                id=parsed_url.hostname or "unknown",
                name=db_name,
                status="active",
                region="unknown",  # Neon API would be needed for this
                connection_string=self.connection_string,
                created="unknown"  # Would need Neon API for this
            )
            
        except Exception as e:
            logger.error(f"Error getting Neon database info: {e}")
            return None
    
    def check_existing_tables(self) -> List[str]:
        """Check for existing tables that might indicate previous deployments"""
        if not self.check_database_connection():
            return []
        
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return tables
            
        except Exception as e:
            logger.error(f"Error checking existing tables: {e}")
            return []

class LocalServiceAuditor:
    """Audits local services and processes"""
    
    def get_running_services(self) -> List[Dict[str, Any]]:
        """Get running services related to AI brain"""
        services = []
        
        # Check for running Python processes
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ['apex', 'brain', 'vertex', 'orchestrator', 'algorithm']):
                    parts = line.split()
                    if len(parts) >= 11:
                        services.append({
                            'type': 'process',
                            'pid': parts[1],
                            'command': ' '.join(parts[10:]),
                            'cpu': parts[2],
                            'memory': parts[3]
                        })
        except Exception as e:
            logger.error(f"Error checking running processes: {e}")
        
        # Check for open ports
        try:
            result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if ':8000' in line or ':8001' in line or ':8002' in line or ':3000' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        services.append({
                            'type': 'port',
                            'address': parts[3],
                            'state': parts[5] if len(parts) > 5 else 'LISTEN',
                            'process': parts[6] if len(parts) > 6 else 'unknown'
                        })
        except Exception as e:
            logger.error(f"Error checking open ports: {e}")
        
        return services
    
    def check_docker_containers(self) -> List[Dict[str, Any]]:
        """Check for Docker containers"""
        containers = []
        
        try:
            result = subprocess.run(['docker', 'ps', '-a', '--format', 'json'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        container = json.loads(line)
                        if any(keyword in container.get('Names', '').lower() 
                              for keyword in ['apex', 'brain', 'vertex', 'orchestrator']):
                            containers.append(container)
        except Exception as e:
            logger.info(f"Docker not available or no containers found: {e}")
        
        return containers
    
    def check_kubernetes_pods(self) -> List[Dict[str, Any]]:
        """Check for Kubernetes pods"""
        pods = []
        
        try:
            result = subprocess.run(['kubectl', 'get', 'pods', '-A', '-o', 'json'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for pod in data.get('items', []):
                    pod_name = pod['metadata']['name']
                    if any(keyword in pod_name.lower() 
                          for keyword in ['apex', 'brain', 'vertex', 'orchestrator']):
                        pods.append({
                            'name': pod_name,
                            'namespace': pod['metadata']['namespace'],
                            'status': pod['status']['phase'],
                            'created': pod['metadata']['creationTimestamp']
                        })
        except Exception as e:
            logger.info(f"kubectl not available or no pods found: {e}")
        
        return pods

class InfrastructureAuditor:
    """Main infrastructure auditor"""
    
    def __init__(self):
        self.hetzner_auditor = HetznerAuditor()
        self.neon_auditor = NeonAuditor()
        self.local_auditor = LocalServiceAuditor()
    
    def perform_full_audit(self) -> InfrastructureAudit:
        """Perform complete infrastructure audit"""
        logger.info("Starting infrastructure audit...")
        
        # Audit Hetzner infrastructure
        logger.info("Checking Hetzner Cloud infrastructure...")
        hetzner_servers = self.hetzner_auditor.get_servers()
        kubernetes_clusters = self.hetzner_auditor.get_kubernetes_clusters()
        
        # Audit Neon database
        logger.info("Checking Neon Database...")
        neon_db = self.neon_auditor.get_database_info()
        neon_databases = [neon_db] if neon_db else []
        
        # Check existing tables
        existing_tables = self.neon_auditor.check_existing_tables()
        
        # Audit local services
        logger.info("Checking local services...")
        running_services = self.local_auditor.get_running_services()
        docker_containers = self.local_auditor.check_docker_containers()
        k8s_pods = self.local_auditor.check_kubernetes_pods()
        
        # Combine all service information
        existing_services = running_services + docker_containers + k8s_pods
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            hetzner_servers, kubernetes_clusters, neon_databases, 
            existing_services, existing_tables
        )
        
        return InfrastructureAudit(
            hetzner_servers=hetzner_servers,
            kubernetes_clusters=kubernetes_clusters,
            neon_databases=neon_databases,
            existing_services=existing_services,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, servers: List[HetznerServer], 
                                clusters: List[KubernetesCluster],
                                databases: List[NeonDatabase],
                                services: List[Dict[str, Any]],
                                existing_tables: List[str]) -> List[str]:
        """Generate deployment recommendations based on audit results"""
        recommendations = []
        
        # Check for existing servers
        if servers:
            recommendations.append(f"Found {len(servers)} existing Hetzner server(s). Consider reusing existing infrastructure.")
            for server in servers:
                if 'apex' in server.name.lower() or 'brain' in server.name.lower():
                    recommendations.append(f"Server '{server.name}' appears to be related to AI Brain deployment. Check if it can be reused.")
        else:
            recommendations.append("No existing Hetzner servers found. New server deployment required.")
        
        # Check for existing Kubernetes clusters
        if clusters:
            recommendations.append(f"Found {len(clusters)} existing Kubernetes cluster(s). Consider deploying to existing cluster.")
        else:
            recommendations.append("No existing Kubernetes clusters found. Consider creating new cluster or using Docker deployment.")
        
        # Check for existing databases
        if databases:
            recommendations.append("Neon database connection available. Check for existing schema before deployment.")
            if existing_tables:
                recommendations.append(f"Found {len(existing_tables)} existing tables: {', '.join(existing_tables[:5])}{'...' if len(existing_tables) > 5 else ''}")
        else:
            recommendations.append("No Neon database connection found. Database setup required.")
        
        # Check for existing services
        if services:
            recommendations.append(f"Found {len(services)} existing services that might conflict with new deployment.")
            port_conflicts = [s for s in services if s.get('type') == 'port']
            if port_conflicts:
                recommendations.append("Port conflicts detected. Consider using different ports or stopping existing services.")
        
        # Resource optimization recommendations
        if servers and len(servers) > 1:
            recommendations.append("Multiple servers available. Consider load balancing across servers.")
        
        if not servers and not clusters:
            recommendations.append("No existing infrastructure found. Fresh deployment recommended.")
        
        return recommendations

def save_audit_report(audit: InfrastructureAudit, filename: str = "infrastructure_audit_report.json"):
    """Save audit report to file"""
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hetzner_servers": [
            {
                "id": s.id,
                "name": s.name,
                "status": s.status,
                "server_type": s.server_type,
                "public_ip": s.public_ip,
                "datacenter": s.datacenter,
                "labels": s.labels
            } for s in audit.hetzner_servers
        ],
        "kubernetes_clusters": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "version": c.version,
                "node_count": c.node_count
            } for c in audit.kubernetes_clusters
        ],
        "neon_databases": [
            {
                "id": d.id,
                "name": d.name,
                "status": d.status,
                "region": d.region
            } for d in audit.neon_databases
        ],
        "existing_services": audit.existing_services,
        "recommendations": audit.recommendations
    }
    
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Audit report saved to {filename}")

def print_audit_summary(audit: InfrastructureAudit):
    """Print audit summary to console"""
    print("\n" + "="*80)
    print("🔍 INFRASTRUCTURE AUDIT REPORT")
    print("="*80)
    
    print(f"\n📊 SUMMARY:")
    print(f"  • Hetzner Servers: {len(audit.hetzner_servers)}")
    print(f"  • Kubernetes Clusters: {len(audit.kubernetes_clusters)}")
    print(f"  • Neon Databases: {len(audit.neon_databases)}")
    print(f"  • Existing Services: {len(audit.existing_services)}")
    
    if audit.hetzner_servers:
        print(f"\n🖥️  HETZNER SERVERS:")
        for server in audit.hetzner_servers:
            print(f"  • {server.name} ({server.server_type}) - {server.status} - {server.public_ip}")
    
    if audit.kubernetes_clusters:
        print(f"\n☸️  KUBERNETES CLUSTERS:")
        for cluster in audit.kubernetes_clusters:
            print(f"  • {cluster.name} (v{cluster.version}) - {cluster.status} - {cluster.node_count} nodes")
    
    if audit.neon_databases:
        print(f"\n🗄️  NEON DATABASES:")
        for db in audit.neon_databases:
            print(f"  • {db.name} - {db.status}")
    
    if audit.existing_services:
        print(f"\n🔧 EXISTING SERVICES:")
        for service in audit.existing_services[:5]:  # Show first 5
            if service.get('type') == 'process':
                print(f"  • Process: {service.get('command', '')[:50]}...")
            elif service.get('type') == 'port':
                print(f"  • Port: {service.get('address', '')} - {service.get('process', '')}")
            else:
                print(f"  • {service.get('type', 'Unknown')}: {service.get('name', '')}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(audit.recommendations, 1):
        print(f"  {i}. {rec}")
    
    print("="*80)

if __name__ == "__main__":
    # Load environment variables if available
    env_file = os.path.join(os.path.dirname(__file__), '..', 'apex-brain.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Perform audit
    auditor = InfrastructureAuditor()
    audit_results = auditor.perform_full_audit()
    
    # Print summary
    print_audit_summary(audit_results)
    
    # Save detailed report
    save_audit_report(audit_results)
    
    print(f"\n📄 Detailed report saved to: infrastructure_audit_report.json")
    print("Use this information to avoid redundant deployments and optimize resource usage.")

