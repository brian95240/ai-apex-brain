#!/usr/bin/env python3
"""
Comprehensive Resource Management System for Advanced A.I. 2nd Brain
Manages dependencies, memory, CPU, storage, and cleanup operations
"""

import os
import sys
import gc
import psutil
import threading
import asyncio
import logging
import time
import subprocess
import shutil
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import contextmanager
import weakref

logger = logging.getLogger(__name__)

@dataclass
class ResourceUsage:
    """Resource usage metrics"""
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_usage_mb: float
    network_io_mb: float
    open_files: int
    threads: int
    timestamp: float = field(default_factory=time.time)

@dataclass
class DependencyInfo:
    """Dependency information"""
    name: str
    version: str
    required_version: Optional[str] = None
    installed: bool = False
    import_path: Optional[str] = None
    size_mb: float = 0.0
    dependencies: List[str] = field(default_factory=list)

@dataclass
class ResourceLimit:
    """Resource limits configuration"""
    max_memory_mb: float = 2048
    max_cpu_percent: float = 80.0
    max_disk_usage_mb: float = 5120
    max_open_files: int = 1000
    max_threads: int = 100
    cleanup_threshold: float = 0.8  # Trigger cleanup at 80% of limit

class DependencyManager:
    """Manages Python dependencies and imports"""
    
    def __init__(self):
        self.installed_packages: Dict[str, DependencyInfo] = {}
        self.import_cache: Dict[str, Any] = {}
        self.failed_imports: set = set()
        self._scan_installed_packages()
    
    def _scan_installed_packages(self):
        """Scan for installed packages"""
        try:
            import pkg_resources
            for dist in pkg_resources.working_set:
                self.installed_packages[dist.project_name.lower()] = DependencyInfo(
                    name=dist.project_name,
                    version=dist.version,
                    installed=True
                )
        except Exception as e:
            logger.warning(f"Failed to scan installed packages: {e}")
    
    def check_dependency(self, package_name: str, required_version: Optional[str] = None) -> bool:
        """Check if a dependency is available"""
        package_name = package_name.lower()
        
        if package_name in self.failed_imports:
            return False
        
        if package_name in self.installed_packages:
            dep_info = self.installed_packages[package_name]
            if required_version:
                # Simple version check (could be enhanced with proper version parsing)
                return dep_info.version >= required_version
            return True
        
        return False
    
    def safe_import(self, module_name: str, package_name: Optional[str] = None) -> Optional[Any]:
        """Safely import a module with caching"""
        if module_name in self.import_cache:
            return self.import_cache[module_name]
        
        if module_name in self.failed_imports:
            return None
        
        try:
            if package_name and not self.check_dependency(package_name):
                logger.warning(f"Package {package_name} not available")
                return None
            
            module = __import__(module_name)
            self.import_cache[module_name] = module
            return module
            
        except ImportError as e:
            logger.warning(f"Failed to import {module_name}: {e}")
            self.failed_imports.add(module_name)
            return None
    
    def install_dependency(self, package_name: str, version: Optional[str] = None) -> bool:
        """Install a dependency using pip"""
        try:
            package_spec = f"{package_name}=={version}" if version else package_name
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package_spec
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self._scan_installed_packages()  # Refresh package list
                logger.info(f"Successfully installed {package_spec}")
                return True
            else:
                logger.error(f"Failed to install {package_spec}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing {package_name}: {e}")
            return False
    
    def get_dependency_size(self, package_name: str) -> float:
        """Get approximate size of a package in MB"""
        try:
            import pkg_resources
            dist = pkg_resources.get_distribution(package_name)
            if dist.location:
                size_bytes = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(dist.location)
                    for filename in filenames
                )
                return size_bytes / (1024 * 1024)  # Convert to MB
        except Exception:
            pass
        return 0.0

class MemoryManager:
    """Manages memory usage and cleanup"""
    
    def __init__(self, max_memory_mb: float = 2048):
        self.max_memory_mb = max_memory_mb
        self.memory_history = deque(maxlen=100)
        self.cleanup_callbacks: List[Callable] = []
        self.object_registry = weakref.WeakSet()
    
    def register_object(self, obj: Any):
        """Register an object for memory tracking"""
        self.object_registry.add(obj)
    
    def register_cleanup_callback(self, callback: Callable):
        """Register a cleanup callback"""
        self.cleanup_callbacks.append(callback)
    
    def get_memory_usage(self) -> ResourceUsage:
        """Get current memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        usage = ResourceUsage(
            cpu_percent=process.cpu_percent(),
            memory_mb=memory_info.rss / (1024 * 1024),
            memory_percent=process.memory_percent(),
            disk_usage_mb=0,  # Will be calculated separately
            network_io_mb=0,  # Will be calculated separately
            open_files=len(process.open_files()),
            threads=process.num_threads()
        )
        
        self.memory_history.append(usage)
        return usage
    
    def check_memory_pressure(self) -> bool:
        """Check if memory usage is high"""
        usage = self.get_memory_usage()
        return usage.memory_mb > self.max_memory_mb * 0.8
    
    def force_garbage_collection(self):
        """Force garbage collection"""
        collected = gc.collect()
        logger.info(f"Garbage collection freed {collected} objects")
        return collected
    
    def cleanup_memory(self):
        """Perform memory cleanup"""
        logger.info("Starting memory cleanup...")
        
        # Force garbage collection
        self.force_garbage_collection()
        
        # Run cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Cleanup callback failed: {e}")
        
        # Clear import cache if memory pressure is high
        if self.check_memory_pressure():
            logger.info("Clearing import cache due to memory pressure")
            sys.modules.clear()
        
        logger.info("Memory cleanup completed")
    
    @contextmanager
    def memory_limit_context(self, limit_mb: float):
        """Context manager for temporary memory limits"""
        original_limit = self.max_memory_mb
        self.max_memory_mb = limit_mb
        try:
            yield
        finally:
            self.max_memory_mb = original_limit

class CPUManager:
    """Manages CPU usage and throttling"""
    
    def __init__(self, max_cpu_percent: float = 80.0):
        self.max_cpu_percent = max_cpu_percent
        self.cpu_history = deque(maxlen=100)
        self.throttle_active = False
        self.throttle_lock = threading.Lock()
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_history.append(cpu_percent)
        return cpu_percent
    
    def check_cpu_pressure(self) -> bool:
        """Check if CPU usage is high"""
        return self.get_cpu_usage() > self.max_cpu_percent
    
    async def throttle_if_needed(self, delay: float = 0.1):
        """Throttle execution if CPU usage is high"""
        if self.check_cpu_pressure():
            with self.throttle_lock:
                if not self.throttle_active:
                    self.throttle_active = True
                    logger.info(f"CPU throttling activated (usage: {self.get_cpu_usage():.1f}%)")
            
            await asyncio.sleep(delay)
            
            with self.throttle_lock:
                self.throttle_active = False
    
    @contextmanager
    def cpu_limit_context(self, limit_percent: float):
        """Context manager for temporary CPU limits"""
        original_limit = self.max_cpu_percent
        self.max_cpu_percent = limit_percent
        try:
            yield
        finally:
            self.max_cpu_percent = original_limit

class StorageManager:
    """Manages disk storage and cleanup"""
    
    def __init__(self, base_path: str = "/tmp/ai_brain", max_size_mb: float = 5120):
        self.base_path = base_path
        self.max_size_mb = max_size_mb
        self.temp_files: List[str] = []
        self.ensure_directory()
    
    def ensure_directory(self):
        """Ensure base directory exists"""
        os.makedirs(self.base_path, exist_ok=True)
    
    def get_disk_usage(self) -> float:
        """Get current disk usage in MB"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.base_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    pass
        return total_size / (1024 * 1024)
    
    def check_disk_pressure(self) -> bool:
        """Check if disk usage is high"""
        return self.get_disk_usage() > self.max_size_mb * 0.8
    
    def create_temp_file(self, suffix: str = ".tmp") -> str:
        """Create a temporary file"""
        import tempfile
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.base_path)
        os.close(fd)
        self.temp_files.append(path)
        return path
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        cleaned = 0
        for filepath in self.temp_files[:]:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    cleaned += 1
                self.temp_files.remove(filepath)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {filepath}: {e}")
        
        logger.info(f"Cleaned up {cleaned} temporary files")
        return cleaned
    
    def cleanup_old_files(self, max_age_hours: float = 24):
        """Clean up old files"""
        current_time = time.time()
        cleaned = 0
        
        for dirpath, dirnames, filenames in os.walk(self.base_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > max_age_hours * 3600:
                        os.remove(filepath)
                        cleaned += 1
                except Exception as e:
                    logger.warning(f"Failed to remove old file {filepath}: {e}")
        
        logger.info(f"Cleaned up {cleaned} old files")
        return cleaned

class ResourceManager:
    """Main resource manager coordinating all resource management"""
    
    def __init__(self, limits: Optional[ResourceLimit] = None):
        self.limits = limits or ResourceLimit()
        self.dependency_manager = DependencyManager()
        self.memory_manager = MemoryManager(self.limits.max_memory_mb)
        self.cpu_manager = CPUManager(self.limits.max_cpu_percent)
        self.storage_manager = StorageManager(max_size_mb=self.limits.max_disk_usage_mb)
        
        self.monitoring_active = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.cleanup_callbacks: List[Callable] = []
        
        # Register default cleanup callbacks
        self.register_cleanup_callback(self.memory_manager.cleanup_memory)
        self.register_cleanup_callback(self.storage_manager.cleanup_temp_files)
    
    def register_cleanup_callback(self, callback: Callable):
        """Register a cleanup callback"""
        self.cleanup_callbacks.append(callback)
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get comprehensive resource status"""
        memory_usage = self.memory_manager.get_memory_usage()
        cpu_usage = self.cpu_manager.get_cpu_usage()
        disk_usage = self.storage_manager.get_disk_usage()
        
        return {
            "memory": {
                "usage_mb": memory_usage.memory_mb,
                "usage_percent": memory_usage.memory_percent,
                "limit_mb": self.limits.max_memory_mb,
                "pressure": self.memory_manager.check_memory_pressure()
            },
            "cpu": {
                "usage_percent": cpu_usage,
                "limit_percent": self.limits.max_cpu_percent,
                "pressure": self.cpu_manager.check_cpu_pressure()
            },
            "disk": {
                "usage_mb": disk_usage,
                "limit_mb": self.limits.max_disk_usage_mb,
                "pressure": self.storage_manager.check_disk_pressure()
            },
            "files": {
                "open_files": memory_usage.open_files,
                "limit": self.limits.max_open_files
            },
            "threads": {
                "count": memory_usage.threads,
                "limit": self.limits.max_threads
            }
        }
    
    def check_resource_pressure(self) -> bool:
        """Check if any resource is under pressure"""
        return (self.memory_manager.check_memory_pressure() or
                self.cpu_manager.check_cpu_pressure() or
                self.storage_manager.check_disk_pressure())
    
    async def cleanup_resources(self):
        """Perform comprehensive resource cleanup"""
        logger.info("Starting comprehensive resource cleanup...")
        
        # Run all cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Cleanup callback failed: {e}")
        
        # Additional cleanup if still under pressure
        if self.check_resource_pressure():
            logger.info("Performing aggressive cleanup...")
            self.storage_manager.cleanup_old_files(max_age_hours=1)
            self.memory_manager.force_garbage_collection()
        
        logger.info("Resource cleanup completed")
    
    async def start_monitoring(self, interval: float = 30.0):
        """Start resource monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_task = asyncio.create_task(self._monitor_loop(interval))
        logger.info("Resource monitoring started")
    
    async def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring_active = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Resource monitoring stopped")
    
    async def _monitor_loop(self, interval: float):
        """Resource monitoring loop"""
        while self.monitoring_active:
            try:
                status = self.get_resource_status()
                
                # Log resource status
                logger.debug(f"Resource status: {status}")
                
                # Trigger cleanup if needed
                if self.check_resource_pressure():
                    logger.warning("Resource pressure detected, triggering cleanup")
                    await self.cleanup_resources()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(interval)
    
    @contextmanager
    def resource_context(self, **limits):
        """Context manager for temporary resource limits"""
        original_limits = self.limits
        
        # Create new limits with overrides
        new_limits = ResourceLimit(
            max_memory_mb=limits.get('max_memory_mb', original_limits.max_memory_mb),
            max_cpu_percent=limits.get('max_cpu_percent', original_limits.max_cpu_percent),
            max_disk_usage_mb=limits.get('max_disk_usage_mb', original_limits.max_disk_usage_mb),
            max_open_files=limits.get('max_open_files', original_limits.max_open_files),
            max_threads=limits.get('max_threads', original_limits.max_threads),
            cleanup_threshold=limits.get('cleanup_threshold', original_limits.cleanup_threshold)
        )
        
        self.limits = new_limits
        try:
            yield
        finally:
            self.limits = original_limits
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_monitoring()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop_monitoring()
        await self.cleanup_resources()

# Global resource manager instance
_global_resource_manager: Optional[ResourceManager] = None

def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance"""
    global _global_resource_manager
    if _global_resource_manager is None:
        _global_resource_manager = ResourceManager()
    return _global_resource_manager

def set_resource_limits(**limits):
    """Set global resource limits"""
    manager = get_resource_manager()
    manager.limits = ResourceLimit(**limits)

async def cleanup_resources():
    """Cleanup global resources"""
    manager = get_resource_manager()
    await manager.cleanup_resources()

# Decorator for resource-aware functions
def resource_managed(max_memory_mb: Optional[float] = None, 
                    max_cpu_percent: Optional[float] = None):
    """Decorator for resource-managed functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            manager = get_resource_manager()
            
            # Check resources before execution
            if manager.check_resource_pressure():
                await manager.cleanup_resources()
            
            # Apply CPU throttling if needed
            await manager.cpu_manager.throttle_if_needed()
            
            # Execute function with resource limits
            limits = {}
            if max_memory_mb:
                limits['max_memory_mb'] = max_memory_mb
            if max_cpu_percent:
                limits['max_cpu_percent'] = max_cpu_percent
            
            if limits:
                with manager.resource_context(**limits):
                    return await func(*args, **kwargs)
            else:
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

if __name__ == "__main__":
    async def test_resource_manager():
        """Test the resource manager"""
        async with ResourceManager() as manager:
            print("Resource Manager Test")
            print("=" * 40)
            
            status = manager.get_resource_status()
            print(f"Memory: {status['memory']['usage_mb']:.1f}MB / {status['memory']['limit_mb']:.1f}MB")
            print(f"CPU: {status['cpu']['usage_percent']:.1f}% / {status['cpu']['limit_percent']:.1f}%")
            print(f"Disk: {status['disk']['usage_mb']:.1f}MB / {status['disk']['limit_mb']:.1f}MB")
            
            # Test dependency checking
            torch_available = manager.dependency_manager.check_dependency('torch')
            print(f"PyTorch available: {torch_available}")
            
            # Test memory management
            print("Testing memory management...")
            await manager.cleanup_resources()
            
            print("Resource manager test completed")
    
    asyncio.run(test_resource_manager())

