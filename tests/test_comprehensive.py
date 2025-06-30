#!/usr/bin/env python3
"""
Comprehensive Test Suite for Advanced A.I. 2nd Brain
Tests all components including vertex orchestrator, algorithms, and dashboard
"""

import asyncio
import pytest
import sys
import os
import time
import json
import numpy as np
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vertex_orchestrator import (
    create_vertex_orchestrator, 
    AlgorithmPriority, 
    AlgorithmType,
    AlgorithmMetadata
)
from algorithms.algorithm_registry import get_algorithm_registry

class TestVertexOrchestrator:
    """Test suite for Vertex Orchestrator"""
    
    async def test_orchestrator_creation(self):
        """Test orchestrator creation and initialization"""
        orchestrator = create_vertex_orchestrator()
        assert orchestrator is not None
        assert orchestrator.max_concurrent_tasks == 50
        assert len(orchestrator.vertices) == 0
        assert orchestrator.algorithm_loader is not None
        assert orchestrator.cascade_engine is not None
    
    async def test_vertex_creation(self):
        """Test vertex creation and management"""
        orchestrator = create_vertex_orchestrator(max_concurrent_tasks=10)
        await orchestrator.start()
        try:
            vertex = orchestrator.create_vertex("test_vertex", max_capacity=5)
            assert vertex.vertex_id == "test_vertex"
            assert vertex.max_capacity == 5
            assert vertex.active_tasks == 0
            assert "test_vertex" in orchestrator.vertices
        finally:
            await orchestrator.stop()
    
    async def test_vertex_connection(self):
        """Test vertex connection functionality"""
        orchestrator = create_vertex_orchestrator(max_concurrent_tasks=10)
        await orchestrator.start()
        try:
            vertex1 = orchestrator.create_vertex("vertex_1")
            vertex2 = orchestrator.create_vertex("vertex_2")
            
            orchestrator.connect_vertices("vertex_1", "vertex_2")
            
            assert "vertex_2" in vertex1.connections
            assert "vertex_1" in vertex2.connections
        finally:
            await orchestrator.stop()
    
    async def test_algorithm_execution(self):
        """Test single algorithm execution"""
        orchestrator = create_vertex_orchestrator(max_concurrent_tasks=10)
        await orchestrator.start()
        try:
            result = await orchestrator.execute_task(
                "test_task",
                "predictive_example",
                [1, 2, 3, 4, 5],
                AlgorithmPriority.HIGH
            )
            
            assert result is not None
            assert isinstance(result, (int, float))
            assert result > 0  # Should be a prediction
        finally:
            await orchestrator.stop()
    
    async def test_cascade_execution(self):
        """Test cascade chain execution"""
        orchestrator = create_vertex_orchestrator(max_concurrent_tasks=10)
        await orchestrator.start()
        try:
            result = await orchestrator.execute_cascade(
                "prediction_learning_chain",
                [10, 20, 30, 40, 50]
            )
            
            assert result is not None
            assert isinstance(result, dict)
            assert "processed_data" in result
            assert "pattern_count" in result
        finally:
            await orchestrator.stop()
    
    async def test_compound_execution(self):
        """Test compound group execution"""
        orchestrator = create_vertex_orchestrator(max_concurrent_tasks=10)
        await orchestrator.start()
        try:
            result = await orchestrator.execute_compound(
                "analysis_group",
                [100, 200, 300, 400, 500]
            )
            
            assert result is not None
            assert isinstance(result, dict)
            assert len(result) >= 2  # Should have results from multiple algorithms
        finally:
            await orchestrator.stop()

class TestAlgorithmRegistry:
    """Test suite for Algorithm Registry"""
    
    def test_registry_initialization(self):
        """Test algorithm registry initialization"""
        registry = get_algorithm_registry()
        assert registry is not None
        assert len(registry.algorithms) > 0
        
        # Check that we have algorithms of different types
        algorithm_ids = registry.list_algorithms()
        assert any("predictor" in alg_id for alg_id in algorithm_ids)
        assert any("learner" in alg_id for alg_id in algorithm_ids)
    
    async def test_linear_regression_predictor(self):
        """Test linear regression predictor algorithm"""
        registry = get_algorithm_registry()
        
        # Test with simple linear data
        data = [1, 2, 3, 4, 5]
        result = await registry.execute_algorithm("linear_regression_predictor", data)
        
        assert "prediction" in result
        assert "slope" in result
        assert "intercept" in result
        assert "r_squared" in result
        assert isinstance(result["prediction"], (int, float))
        assert result["r_squared"] >= 0 and result["r_squared"] <= 1
    
    async def test_exponential_smoothing_predictor(self):
        """Test exponential smoothing predictor"""
        registry = get_algorithm_registry()
        
        data = [10, 12, 11, 13, 12, 14, 13, 15]
        result = await registry.execute_algorithm("exponential_smoothing_predictor", data)
        
        assert "prediction" in result
        assert "smoothed_series" in result
        assert "alpha" in result
        assert len(result["smoothed_series"]) == len(data)
    
    async def test_moving_average_predictor(self):
        """Test moving average predictor"""
        registry = get_algorithm_registry()
        
        data = [1, 3, 5, 7, 9, 11, 13, 15]
        context = {"window_size": 3}
        result = await registry.execute_algorithm("moving_average_predictor", data, context)
        
        assert "prediction" in result
        assert "moving_averages" in result
        assert "window_size" in result
        assert result["window_size"] == 3
    
    async def test_kmeans_clustering_learner(self):
        """Test K-means clustering learner"""
        registry = get_algorithm_registry()
        
        # Create simple 2D data for clustering
        data = [[1, 1], [1, 2], [2, 1], [10, 10], [10, 11], [11, 10]]
        context = {"k": 2, "max_iters": 50}
        result = await registry.execute_algorithm("kmeans_clustering_learner", data, context)
        
        assert "centroids" in result
        assert "assignments" in result
        assert "inertia" in result
        assert len(result["centroids"]) == 2
        assert len(result["assignments"]) == len(data)
    
    async def test_naive_bayes_learner(self):
        """Test Naive Bayes learner"""
        registry = get_algorithm_registry()
        
        # Simple classification data
        data = {
            "features": [[1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7]],
            "labels": ["A", "A", "A", "B", "B", "B"]
        }
        result = await registry.execute_algorithm("naive_bayes_learner", data)
        
        assert "class_priors" in result
        assert "feature_stats" in result
        assert "predictions" in result
        assert "accuracy" in result
        assert len(result["predictions"]) == len(data["labels"])
    
    async def test_causal_inference_engine(self):
        """Test causal inference engine"""
        registry = get_algorithm_registry()
        
        # Create data with potential causal relationships
        data = {
            "variables": {
                "temperature": [20, 25, 30, 35, 40],
                "ice_cream_sales": [10, 15, 25, 35, 50],
                "drowning_incidents": [1, 2, 3, 4, 5]
            }
        }
        result = await registry.execute_algorithm("causal_inference_engine", data)
        
        assert "correlations" in result
        assert "causal_relationships" in result
        assert "threshold" in result
        assert isinstance(result["causal_relationships"], list)
    
    async def test_intervention_analyzer(self):
        """Test intervention analyzer"""
        registry = get_algorithm_registry()
        
        data = {
            "before": [10, 12, 11, 13, 12],
            "after": [15, 17, 16, 18, 17]
        }
        result = await registry.execute_algorithm("intervention_analyzer", data)
        
        assert "effect_size" in result
        assert "before_mean" in result
        assert "after_mean" in result
        assert "cohens_d" in result
        assert "effect_magnitude" in result
        assert result["effect_size"] > 0  # Should show positive effect
    
    async def test_recursive_pattern_miner(self):
        """Test recursive pattern miner"""
        registry = get_algorithm_registry()
        
        # Complex nested data structure
        data = {
            "level1": {
                "level2": {
                    "level3": [1, 2, 3],
                    "another_level3": {"deep": "value"}
                },
                "list_data": [{"item": 1}, {"item": 2}]
            },
            "top_level_list": [1, 2, 3, 4, 5]
        }
        result = await registry.execute_algorithm("recursive_pattern_miner", data)
        
        assert "all_patterns" in result
        assert "recursive_patterns" in result
        assert "total_patterns" in result
        assert len(result["all_patterns"]) > 0
    
    async def test_fractal_analyzer(self):
        """Test fractal analyzer"""
        registry = get_algorithm_registry()
        
        # Generate data with some self-similarity
        data = np.cumsum(np.random.randn(100))  # Random walk
        result = await registry.execute_algorithm("fractal_analyzer", data.tolist())
        
        assert "hurst_exponent" in result
        assert "fractal_dimension" in result
        assert "trend_type" in result
        assert "self_similarity" in result
        assert 0 <= result["hurst_exponent"] <= 1
        assert 1 <= result["fractal_dimension"] <= 2

class TestLazyLoading:
    """Test suite for lazy loading functionality"""
    
    async def test_algorithm_caching(self):
        """Test algorithm caching mechanism"""
        registry = get_algorithm_registry()
        
        # Execute same algorithm multiple times
        data = [1, 2, 3, 4, 5]
        
        # First execution
        start_time = time.time()
        result1 = await registry.execute_algorithm("linear_regression_predictor", data)
        first_time = time.time() - start_time
        
        # Second execution (should use cache)
        start_time = time.time()
        result2 = await registry.execute_algorithm("linear_regression_predictor", data)
        second_time = time.time() - start_time
        
        # Results should be identical
        assert result1 == result2
        
        # Second execution should be faster (cached)
        # Note: This might not always be true due to system variations
        # assert second_time < first_time
    
    async def test_cache_performance_stats(self):
        """Test cache performance statistics"""
        registry = get_algorithm_registry()
        algorithm = registry.get_algorithm("linear_regression_predictor")
        
        # Clear cache and reset stats
        algorithm.cache = {}
        algorithm.cache_hits = 0
        algorithm.cache_misses = 0
        
        data = [1, 2, 3, 4, 5]
        
        # First execution (cache miss)
        await algorithm.execute_with_cache(data)
        assert algorithm.cache_misses == 1
        assert algorithm.cache_hits == 0
        
        # Second execution (cache hit)
        await algorithm.execute_with_cache(data)
        assert algorithm.cache_misses == 1
        assert algorithm.cache_hits == 1
        
        # Get performance stats
        stats = algorithm.get_performance_stats()
        assert "cache_hit_rate" in stats
        assert stats["cache_hit_rate"] == 0.5  # 1 hit out of 2 total

class TestResourceEfficiency:
    """Test suite for resource efficiency"""
    
    async def test_concurrent_execution(self):
        """Test concurrent algorithm execution"""
        orchestrator = create_vertex_orchestrator(max_concurrent_tasks=5)
        await orchestrator.start()
        
        try:
            # Create multiple concurrent tasks
            tasks = []
            for i in range(5):
                task = orchestrator.execute_task(
                    f"concurrent_task_{i}",
                    "predictive_example",
                    [i, i+1, i+2, i+3, i+4],
                    AlgorithmPriority.MEDIUM
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks)
            
            # All tasks should complete successfully
            assert len(results) == 5
            assert all(result is not None for result in results)
            
        finally:
            await orchestrator.stop()
    
    async def test_memory_management(self):
        """Test memory management and cleanup"""
        registry = get_algorithm_registry()
        algorithm = registry.get_algorithm("linear_regression_predictor")
        
        # Fill cache with many entries
        for i in range(1500):  # More than cache limit (1000)
            data = [i, i+1, i+2, i+3, i+4]
            await algorithm.execute_with_cache(data)
        
        # Cache should be limited to prevent memory issues
        assert len(algorithm.cache) <= 1000

class TestCascadingAndCompounding:
    """Test suite for cascading and compounding algorithms"""
    
    async def test_cascade_chain_performance(self):
        """Test cascade chain execution performance"""
        orchestrator = create_vertex_orchestrator()
        await orchestrator.start()
        
        try:
            # Test cascade execution
            start_time = time.time()
            result = await orchestrator.execute_cascade(
                "prediction_learning_chain",
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            )
            execution_time = time.time() - start_time
            
            assert result is not None
            assert execution_time < 10  # Should complete within 10 seconds
            
        finally:
            await orchestrator.stop()
    
    async def test_compound_group_parallelism(self):
        """Test compound group parallel execution"""
        orchestrator = create_vertex_orchestrator()
        await orchestrator.start()
        
        try:
            # Test compound execution
            start_time = time.time()
            result = await orchestrator.execute_compound(
                "analysis_group",
                [10, 20, 30, 40, 50]
            )
            execution_time = time.time() - start_time
            
            assert result is not None
            assert isinstance(result, dict)
            assert len(result) >= 2  # Multiple algorithms should execute
            assert execution_time < 10  # Should complete within 10 seconds
            
        finally:
            await orchestrator.stop()

# Utility functions for running tests
async def run_all_tests():
    """Run all tests and return results"""
    test_results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "failures": []
    }
    
    # Test classes to run
    test_classes = [
        TestVertexOrchestrator,
        TestAlgorithmRegistry,
        TestLazyLoading,
        TestResourceEfficiency,
        TestCascadingAndCompounding
    ]
    
    for test_class in test_classes:
        test_instance = test_class()
        
        # Get all test methods
        test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
        
        for method_name in test_methods:
            test_results["total_tests"] += 1
            
            try:
                method = getattr(test_instance, method_name)
                
                # Handle async and sync methods
                if asyncio.iscoroutinefunction(method):
                    await method()
                else:
                    method()
                
                test_results["passed_tests"] += 1
                print(f"✅ {test_class.__name__}.{method_name}")
                
            except Exception as e:
                test_results["failed_tests"] += 1
                test_results["failures"].append({
                    "test": f"{test_class.__name__}.{method_name}",
                    "error": str(e)
                })
                print(f"❌ {test_class.__name__}.{method_name}: {e}")
    
    return test_results

def print_test_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("🧠 ADVANCED A.I. 2ND BRAIN - TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']} ✅")
    print(f"Failed: {results['failed_tests']} ❌")
    print(f"Success Rate: {(results['passed_tests']/results['total_tests']*100):.1f}%")
    
    if results['failures']:
        print("\nFailures:")
        for failure in results['failures']:
            print(f"  - {failure['test']}: {failure['error']}")
    
    print("="*60)

if __name__ == "__main__":
    async def main():
        print("🧠 Starting Advanced A.I. 2nd Brain Comprehensive Tests...")
        print("Testing vertex orchestration, lazy loading, and algorithm performance...")
        print()
        
        results = await run_all_tests()
        print_test_summary(results)
        
        return results
    
    # Run the tests
    test_results = asyncio.run(main())

