#!/usr/bin/env python3
"""
Local Stress Test Runner - No Cloud Dependencies
Runs comprehensive algorithm stress testing without requiring cloud services
"""

import asyncio
import json
import time
import logging
import random
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import threading
from collections import defaultdict, deque
import hashlib
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class LocalTestConfig:
    """Configuration for local stress testing"""
    max_concurrent_tasks: int = 20
    test_duration_minutes: int = 15
    difficulty_progression_steps: int = 5
    recursive_depth_limit: int = 10
    memory_limit_gb: float = 4.0
    cpu_limit_percent: float = 80.0
    log_detailed_metrics: bool = True

@dataclass
class TestQuestion:
    """Individual test question structure"""
    id: str
    question: str
    difficulty_level: int  # 1-10
    expected_algorithms: List[str]
    recursive_depth: int
    complexity_score: float
    category: str  # "predictive", "ml", "causal", "recursive"
    expected_execution_time: float = 0.0
    metadata: Dict[str, Any] = None

@dataclass
class TestResult:
    """Test execution result"""
    question_id: str
    success: bool
    execution_time: float
    algorithms_used: List[str]
    recursive_depth_reached: int
    accuracy_score: float
    resource_usage: Dict[str, float]
    error_message: Optional[str] = None
    timestamp: datetime = None

class MockAlgorithmRegistry:
    """Mock algorithm registry for testing"""
    
    def __init__(self):
        self.algorithms = {
            # Predictive algorithms
            "linear_regression": {"type": "predictive", "complexity": 1.0},
            "time_series_forecasting": {"type": "predictive", "complexity": 2.0},
            "arima": {"type": "predictive", "complexity": 2.5},
            "neural_networks": {"type": "predictive", "complexity": 3.0},
            "ensemble_methods": {"type": "predictive", "complexity": 3.5},
            
            # ML algorithms
            "k_means": {"type": "ml", "complexity": 1.5},
            "svm": {"type": "ml", "complexity": 2.0},
            "decision_trees": {"type": "ml", "complexity": 1.8},
            "random_forest": {"type": "ml", "complexity": 2.5},
            "deep_learning": {"type": "ml", "complexity": 4.0},
            
            # Causal algorithms
            "causal_discovery": {"type": "causal", "complexity": 3.0},
            "intervention_analysis": {"type": "causal", "complexity": 3.5},
            "counterfactual_reasoning": {"type": "causal", "complexity": 4.0},
            
            # Recursive algorithms
            "recursive_pattern_mining": {"type": "recursive", "complexity": 2.5},
            "fractal_analysis": {"type": "recursive", "complexity": 3.5},
            "hierarchical_decomposition": {"type": "recursive", "complexity": 3.0},
            "genetic_algorithm": {"type": "recursive", "complexity": 4.0},
            
            # Optimization algorithms
            "dijkstra": {"type": "optimization", "complexity": 2.0},
            "a_star": {"type": "optimization", "complexity": 2.5},
            "dynamic_programming": {"type": "optimization", "complexity": 3.0},
            "monte_carlo": {"type": "optimization", "complexity": 3.5},
            
            # Additional algorithms
            "pattern_recognition": {"type": "ml", "complexity": 2.0},
            "sentiment_analysis": {"type": "ml", "complexity": 1.5},
            "text_classification": {"type": "ml", "complexity": 2.0},
            "nlp_processing": {"type": "ml", "complexity": 2.5},
            "financial_modeling": {"type": "predictive", "complexity": 3.0},
            "risk_analysis": {"type": "predictive", "complexity": 2.8},
            "optimization": {"type": "optimization", "complexity": 2.5},
            "clustering": {"type": "ml", "complexity": 2.0},
            "neural_architecture_search": {"type": "ml", "complexity": 4.5},
            "hyperparameter_optimization": {"type": "optimization", "complexity": 3.5},
            "multi_modal_learning": {"type": "ml", "complexity": 4.0},
            "performance_profiling": {"type": "optimization", "complexity": 1.5},
            "tsp_solver": {"type": "optimization", "complexity": 3.5},
            "adaptive_optimization": {"type": "optimization", "complexity": 4.0},
            "real_time_processing": {"type": "optimization", "complexity": 3.0},
            "reinforcement_learning": {"type": "ml", "complexity": 4.5},
            "collaborative_filtering": {"type": "ml", "complexity": 2.5},
            "emergent_behavior_prediction": {"type": "predictive", "complexity": 4.5},
            "self_optimization": {"type": "recursive", "complexity": 5.0},
            "multi_objective_optimization": {"type": "optimization", "complexity": 4.0},
            "swarm_intelligence": {"type": "recursive", "complexity": 3.5},
            "pareto_optimization": {"type": "optimization", "complexity": 3.5},
            "genetic_programming": {"type": "recursive", "complexity": 4.5},
            "self_modification": {"type": "recursive", "complexity": 5.0},
            "algorithm_evolution": {"type": "recursive", "complexity": 5.0}
        }
    
    def get_all_algorithms(self) -> List[str]:
        return list(self.algorithms.keys())
    
    def get_algorithm_info(self, name: str) -> Dict[str, Any]:
        return self.algorithms.get(name, {"type": "unknown", "complexity": 1.0})

class MockVertexOrchestrator:
    """Mock vertex orchestrator for testing"""
    
    def __init__(self):
        self.active_tasks = {}
        self.task_counter = 0
        self.algorithm_registry = MockAlgorithmRegistry()
    
    async def start(self):
        logger.info("Mock Vertex Orchestrator started")
    
    async def stop(self):
        logger.info("Mock Vertex Orchestrator stopped")
    
    async def submit_task(self, task_data: Dict, priority=None) -> str:
        self.task_counter += 1
        task_id = f"task_{self.task_counter}_{uuid.uuid4().hex[:8]}"
        
        # Simulate task processing
        self.active_tasks[task_id] = {
            "data": task_data,
            "status": "running",
            "start_time": time.time(),
            "algorithms_used": [],
            "recursive_depth": 0
        }
        
        # Start background processing
        asyncio.create_task(self._process_task(task_id, task_data))
        
        return task_id
    
    async def _process_task(self, task_id: str, task_data: Dict):
        """Simulate task processing"""
        try:
            task = self.active_tasks[task_id]
            
            # Simulate algorithm selection based on expected algorithms
            expected_algos = task_data.get("expected_algorithms", [])
            difficulty = task_data.get("difficulty_level", 1)
            max_depth = task_data.get("max_recursive_depth", 1)
            
            # Simulate processing time based on difficulty
            processing_time = difficulty * 0.5 + random.uniform(0.1, 1.0)
            
            # Simulate algorithm usage
            algorithms_used = []
            for algo in expected_algos:
                if random.random() > 0.2:  # 80% chance to use expected algorithm
                    algorithms_used.append(algo)
                    await asyncio.sleep(0.1)  # Simulate processing
            
            # Add some random algorithms
            all_algos = self.algorithm_registry.get_all_algorithms()
            for _ in range(random.randint(1, 3)):
                algo = random.choice(all_algos)
                if algo not in algorithms_used:
                    algorithms_used.append(algo)
            
            # Simulate recursive depth
            recursive_depth = min(max_depth, random.randint(1, max_depth + 2))
            
            # Simulate processing delay
            await asyncio.sleep(processing_time)
            
            # Update task status
            task["status"] = "completed"
            task["success"] = random.random() > 0.1  # 90% success rate
            task["algorithms_used"] = algorithms_used
            task["recursive_depth"] = recursive_depth
            task["result"] = {
                "processed": True,
                "algorithms_count": len(algorithms_used),
                "complexity_handled": difficulty
            }
            
        except Exception as e:
            task["status"] = "failed"
            task["success"] = False
            task["error"] = str(e)
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        task = self.active_tasks.get(task_id, {})
        
        return {
            "completed": task.get("status") in ["completed", "failed"],
            "success": task.get("success", False),
            "active_algorithms": task.get("algorithms_used", []),
            "recursive_depth": task.get("recursive_depth", 0),
            "coordination_events": [f"event_{i}" for i in range(random.randint(0, 5))],
            "result": task.get("result", {})
        }

class LocalStressTestFramework:
    """Local stress testing framework without cloud dependencies"""
    
    def __init__(self, config: LocalTestConfig):
        self.config = config
        self.vertex_orchestrator = MockVertexOrchestrator()
        self.algorithm_registry = MockAlgorithmRegistry()
        
        # Test tracking
        self.test_results: List[TestResult] = []
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        self.algorithm_performance: Dict[str, Dict[str, float]] = {}
        self.recursive_loop_stats: Dict[int, int] = defaultdict(int)
        
        # Real-time monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
    
    def generate_test_questions(self) -> List[TestQuestion]:
        """Generate test questions for local testing"""
        questions = [
            TestQuestion(
                id="local_001",
                question="Predict the next 5 numbers in sequence: 2, 4, 6, 8, 10",
                difficulty_level=1,
                expected_algorithms=["linear_regression", "pattern_recognition"],
                recursive_depth=1,
                complexity_score=1.0,
                category="predictive"
            ),
            TestQuestion(
                id="local_002",
                question="Classify sentiment: 'This AI system is amazing!'",
                difficulty_level=1,
                expected_algorithms=["sentiment_analysis", "text_classification"],
                recursive_depth=1,
                complexity_score=1.2,
                category="ml"
            ),
            TestQuestion(
                id="local_003",
                question="Find optimal path in 5x5 grid",
                difficulty_level=2,
                expected_algorithms=["dijkstra", "a_star", "dynamic_programming"],
                recursive_depth=2,
                complexity_score=1.5,
                category="recursive"
            ),
            TestQuestion(
                id="local_004",
                question="Analyze causal relationships in weather-energy data",
                difficulty_level=3,
                expected_algorithms=["causal_discovery", "time_series_forecasting", "clustering"],
                recursive_depth=3,
                complexity_score=2.5,
                category="causal"
            ),
            TestQuestion(
                id="local_005",
                question="Optimize neural network architecture for multi-modal learning",
                difficulty_level=4,
                expected_algorithms=["neural_architecture_search", "hyperparameter_optimization", "multi_modal_learning"],
                recursive_depth=4,
                complexity_score=3.5,
                category="ml"
            ),
            TestQuestion(
                id="local_006",
                question="Solve TSP for 20 cities with dynamic constraints",
                difficulty_level=5,
                expected_algorithms=["genetic_algorithm", "tsp_solver", "adaptive_optimization"],
                recursive_depth=6,
                complexity_score=4.0,
                category="recursive"
            ),
            TestQuestion(
                id="local_007",
                question="Create self-improving recommendation system",
                difficulty_level=6,
                expected_algorithms=["reinforcement_learning", "collaborative_filtering", "self_optimization"],
                recursive_depth=7,
                complexity_score=4.5,
                category="ml"
            ),
            TestQuestion(
                id="local_008",
                question="Implement recursive fractal analysis with causal inference",
                difficulty_level=7,
                expected_algorithms=["fractal_analysis", "recursive_pattern_mining", "causal_discovery"],
                recursive_depth=8,
                complexity_score=5.0,
                category="recursive"
            ),
            TestQuestion(
                id="local_009",
                question="Multi-objective optimization for smart city design",
                difficulty_level=8,
                expected_algorithms=["multi_objective_optimization", "swarm_intelligence", "pareto_optimization"],
                recursive_depth=9,
                complexity_score=5.5,
                category="optimization"
            ),
            TestQuestion(
                id="local_010",
                question="Self-evolving AI system with genetic programming",
                difficulty_level=9,
                expected_algorithms=["genetic_programming", "self_modification", "algorithm_evolution"],
                recursive_depth=10,
                complexity_score=6.0,
                category="recursive"
            )
        ]
        
        # Add metadata
        for i, q in enumerate(questions):
            q.metadata = {
                "generated_at": datetime.now().isoformat(),
                "sequence_number": i + 1,
                "total_questions": len(questions)
            }
        
        return questions
    
    async def execute_stress_test(self, questions: List[TestQuestion]) -> Dict[str, Any]:
        """Execute the stress test"""
        logger.info(f"Starting local stress test with {len(questions)} questions")
        
        # Initialize systems
        await self.vertex_orchestrator.start()
        
        # Start monitoring
        self._start_monitoring()
        
        start_time = datetime.now()
        
        try:
            # Execute questions
            for i, question in enumerate(questions):
                logger.info(f"Executing question {i+1}/{len(questions)}: {question.id} (Difficulty: {question.difficulty_level})")
                
                # Check resource limits
                if not self._check_resource_limits():
                    logger.warning("Resource limits exceeded, pausing test")
                    await asyncio.sleep(2)
                    continue
                
                # Execute the question
                result = await self._execute_question(question)
                self.test_results.append(result)
                
                # Log progress
                self._log_progress(i + 1, len(questions), result)
                
                # Adaptive delay
                await self._adaptive_delay()
            
            # Generate report
            report = await self._generate_test_report(start_time)
            
            return report
            
        except Exception as e:
            logger.error(f"Stress test failed: {e}")
            raise
        finally:
            self._stop_monitoring()
            await self.vertex_orchestrator.stop()
    
    async def _execute_question(self, question: TestQuestion) -> TestResult:
        """Execute a single test question"""
        start_time = time.time()
        
        try:
            # Create task data
            task_data = {
                "question": question.question,
                "expected_algorithms": question.expected_algorithms,
                "max_recursive_depth": question.recursive_depth,
                "difficulty_level": question.difficulty_level
            }
            
            # Submit to orchestrator
            task_id = await self.vertex_orchestrator.submit_task(task_data)
            
            # Monitor execution
            result_data = await self._monitor_task_execution(task_id, question)
            
            execution_time = time.time() - start_time
            
            # Analyze results
            algorithms_used = result_data.get("algorithms_used", [])
            recursive_depth_reached = result_data.get("recursive_depth_reached", 0)
            accuracy_score = self._calculate_accuracy_score(question, result_data)
            
            # Get resource usage
            resource_usage = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            }
            
            # Track recursive loop statistics
            self.recursive_loop_stats[recursive_depth_reached] += 1
            
            # Create result
            result = TestResult(
                question_id=question.id,
                success=result_data.get("success", False),
                execution_time=execution_time,
                algorithms_used=algorithms_used,
                recursive_depth_reached=recursive_depth_reached,
                accuracy_score=accuracy_score,
                resource_usage=resource_usage,
                timestamp=datetime.now()
            )
            
            # Update performance metrics
            self._update_performance_metrics(question, result)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Question execution failed: {e}")
            
            return TestResult(
                question_id=question.id,
                success=False,
                execution_time=execution_time,
                algorithms_used=[],
                recursive_depth_reached=0,
                accuracy_score=0.0,
                resource_usage={"cpu_percent": psutil.cpu_percent(), "memory_percent": psutil.virtual_memory().percent},
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def _monitor_task_execution(self, task_id: str, question: TestQuestion) -> Dict[str, Any]:
        """Monitor task execution"""
        timeout = max(30, question.difficulty_level * 10)
        start_time = time.time()
        
        algorithms_used = []
        recursive_depth_reached = 0
        
        while time.time() - start_time < timeout:
            status = await self.vertex_orchestrator.get_task_status(task_id)
            
            if status.get("completed"):
                return {
                    "success": status.get("success", False),
                    "algorithms_used": status.get("active_algorithms", []),
                    "recursive_depth_reached": status.get("recursive_depth", 0),
                    "result_data": status.get("result", {})
                }
            
            # Update tracking
            current_algorithms = status.get("active_algorithms", [])
            for algo in current_algorithms:
                if algo not in algorithms_used:
                    algorithms_used.append(algo)
            
            recursive_depth_reached = max(recursive_depth_reached, status.get("recursive_depth", 0))
            
            await asyncio.sleep(0.5)
        
        # Timeout
        logger.warning(f"Task {task_id} timed out")
        return {
            "success": False,
            "algorithms_used": algorithms_used,
            "recursive_depth_reached": recursive_depth_reached,
            "error": "Timeout"
        }
    
    def _calculate_accuracy_score(self, question: TestQuestion, result_data: Dict) -> float:
        """Calculate accuracy score"""
        score = 0.0
        
        # Algorithm coverage (40%)
        expected_algos = set(question.expected_algorithms)
        used_algos = set(result_data.get("algorithms_used", []))
        if expected_algos:
            algo_coverage = len(expected_algos.intersection(used_algos)) / len(expected_algos)
            score += algo_coverage * 0.4
        
        # Recursive depth (30%)
        expected_depth = question.recursive_depth
        actual_depth = result_data.get("recursive_depth_reached", 0)
        if expected_depth > 0:
            depth_score = min(actual_depth / expected_depth, 1.0)
            score += depth_score * 0.3
        
        # Success (30%)
        if result_data.get("success", False):
            score += 0.3
        
        return min(score, 1.0)
    
    def _update_performance_metrics(self, question: TestQuestion, result: TestResult):
        """Update performance metrics"""
        self.performance_metrics["execution_times"].append(result.execution_time)
        self.performance_metrics["accuracy_scores"].append(result.accuracy_score)
        self.performance_metrics["success_rates"].append(1.0 if result.success else 0.0)
        
        # Algorithm-specific metrics
        for algo in result.algorithms_used:
            if algo not in self.algorithm_performance:
                self.algorithm_performance[algo] = {
                    "total_uses": 0,
                    "total_time": 0.0,
                    "success_count": 0,
                    "avg_accuracy": 0.0
                }
            
            perf = self.algorithm_performance[algo]
            perf["total_uses"] += 1
            perf["total_time"] += result.execution_time
            if result.success:
                perf["success_count"] += 1
            
            # Update average accuracy
            current_avg = perf["avg_accuracy"]
            new_avg = (current_avg * (perf["total_uses"] - 1) + result.accuracy_score) / perf["total_uses"]
            perf["avg_accuracy"] = new_avg
    
    async def _generate_test_report(self, start_time: datetime) -> Dict[str, Any]:
        """Generate test report"""
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        # Calculate statistics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.success)
        success_rate = successful_tests / total_tests if total_tests > 0 else 0.0
        
        avg_execution_time = np.mean([r.execution_time for r in self.test_results]) if self.test_results else 0.0
        avg_accuracy = np.mean([r.accuracy_score for r in self.test_results]) if self.test_results else 0.0
        
        # Algorithm performance
        algorithm_stats = {}
        for algo, perf in self.algorithm_performance.items():
            algorithm_stats[algo] = {
                "usage_count": perf["total_uses"],
                "avg_execution_time": perf["total_time"] / perf["total_uses"] if perf["total_uses"] > 0 else 0.0,
                "success_rate": perf["success_count"] / perf["total_uses"] if perf["total_uses"] > 0 else 0.0,
                "avg_accuracy": perf["avg_accuracy"]
            }
        
        # Recursive depth analysis
        max_depth_reached = max(self.recursive_loop_stats.keys()) if self.recursive_loop_stats else 0
        depth_distribution = dict(self.recursive_loop_stats)
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        report = {
            "test_summary": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration_seconds": total_duration,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "avg_execution_time": avg_execution_time,
                "avg_accuracy_score": avg_accuracy
            },
            "algorithm_performance": algorithm_stats,
            "recursive_analysis": {
                "max_depth_reached": max_depth_reached,
                "depth_distribution": depth_distribution,
                "recursive_efficiency": self._calculate_recursive_efficiency()
            },
            "performance_trends": self._analyze_performance_trends(),
            "optimization_recommendations": recommendations,
            "detailed_results": [asdict(r) for r in self.test_results]
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if self.performance_metrics["execution_times"]:
            avg_time = np.mean(self.performance_metrics["execution_times"])
            if avg_time > 10:
                recommendations.append("Consider optimizing algorithm execution times - average time is high")
        
        if max(self.recursive_loop_stats.keys()) < 5:
            recommendations.append("Recursive algorithms could explore deeper - consider increasing depth limits")
        
        total_algorithms = len(self.algorithm_registry.get_all_algorithms())
        used_algorithms = len(self.algorithm_performance)
        if used_algorithms < total_algorithms * 0.6:
            recommendations.append(f"Only {used_algorithms}/{total_algorithms} algorithms utilized - consider more diverse tests")
        
        success_rate = np.mean(self.performance_metrics["success_rates"]) if self.performance_metrics["success_rates"] else 0
        if success_rate < 0.8:
            recommendations.append("Success rate is below 80% - investigate algorithm reliability")
        
        return recommendations
    
    def _calculate_recursive_efficiency(self) -> float:
        """Calculate recursive efficiency"""
        if not self.recursive_loop_stats:
            return 0.0
        
        total_depth = sum(depth * count for depth, count in self.recursive_loop_stats.items())
        total_calls = sum(self.recursive_loop_stats.values())
        
        return total_depth / total_calls if total_calls > 0 else 0.0
    
    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends"""
        if len(self.test_results) < 3:
            return {"insufficient_data": True}
        
        execution_times = [r.execution_time for r in self.test_results]
        accuracy_scores = [r.accuracy_score for r in self.test_results]
        
        # Simple trend analysis
        mid_point = len(execution_times) // 2
        early_avg_time = np.mean(execution_times[:mid_point])
        late_avg_time = np.mean(execution_times[mid_point:])
        time_trend = "improving" if late_avg_time < early_avg_time else "degrading"
        
        early_avg_accuracy = np.mean(accuracy_scores[:mid_point])
        late_avg_accuracy = np.mean(accuracy_scores[mid_point:])
        accuracy_trend = "improving" if late_avg_accuracy > early_avg_accuracy else "degrading"
        
        return {
            "execution_time_trend": time_trend,
            "accuracy_trend": accuracy_trend,
            "early_avg_time": early_avg_time,
            "late_avg_time": late_avg_time,
            "early_avg_accuracy": early_avg_accuracy,
            "late_avg_accuracy": late_avg_accuracy
        }
    
    def _start_monitoring(self):
        """Start resource monitoring"""
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.start()
    
    def _stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
    
    def _monitoring_loop(self):
        """Resource monitoring loop"""
        while self.monitoring_active:
            try:
                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                
                if cpu_percent > self.config.cpu_limit_percent:
                    logger.warning(f"CPU usage high: {cpu_percent}%")
                
                if memory_percent > 80:
                    logger.warning(f"Memory usage high: {memory_percent}%")
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
    
    def _check_resource_limits(self) -> bool:
        """Check resource limits"""
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        return cpu_percent < self.config.cpu_limit_percent and memory_percent < 85
    
    async def _adaptive_delay(self):
        """Adaptive delay based on system load"""
        cpu_percent = psutil.cpu_percent()
        
        if cpu_percent > 70:
            await asyncio.sleep(1)
        elif cpu_percent > 50:
            await asyncio.sleep(0.5)
        else:
            await asyncio.sleep(0.1)
    
    def _log_progress(self, current: int, total: int, result: TestResult):
        """Log test progress"""
        progress = (current / total) * 100
        status = "✅" if result.success else "❌"
        
        logger.info(f"Progress: {progress:.1f}% ({current}/{total}) {status} "
                   f"Time: {result.execution_time:.2f}s "
                   f"Accuracy: {result.accuracy_score:.2f} "
                   f"Algorithms: {len(result.algorithms_used)} "
                   f"Depth: {result.recursive_depth_reached}")

async def run_local_stress_test():
    """Run the local stress test"""
    config = LocalTestConfig(
        max_concurrent_tasks=20,
        test_duration_minutes=15,
        difficulty_progression_steps=5,
        recursive_depth_limit=10
    )
    
    framework = LocalStressTestFramework(config)
    
    # Generate test questions
    questions = framework.generate_test_questions()
    
    logger.info(f"Generated {len(questions)} test questions")
    logger.info("Starting local stress test...")
    
    # Execute stress test
    report = await framework.execute_stress_test(questions)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"/home/ubuntu/ai-apex-brain/local_stress_test_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Local stress test completed. Report saved to: {report_file}")
    
    # Print summary
    print("\n" + "="*80)
    print("LOCAL STRESS TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {report['test_summary']['total_tests']}")
    print(f"Success Rate: {report['test_summary']['success_rate']:.2%}")
    print(f"Average Execution Time: {report['test_summary']['avg_execution_time']:.2f}s")
    print(f"Average Accuracy: {report['test_summary']['avg_accuracy_score']:.2%}")
    print(f"Max Recursive Depth: {report['recursive_analysis']['max_depth_reached']}")
    print(f"Algorithms Used: {len(report['algorithm_performance'])}")
    
    print("\nTop Performing Algorithms:")
    sorted_algos = sorted(
        report['algorithm_performance'].items(),
        key=lambda x: x[1]['success_rate'],
        reverse=True
    )[:5]
    
    for algo, stats in sorted_algos:
        print(f"  {algo}: {stats['success_rate']:.2%} success, {stats['avg_execution_time']:.2f}s avg")
    
    print(f"\nRecursive Depth Distribution:")
    for depth, count in sorted(report['recursive_analysis']['depth_distribution'].items()):
        print(f"  Depth {depth}: {count} tests")
    
    print(f"\nOptimization Recommendations:")
    for rec in report['optimization_recommendations']:
        print(f"  • {rec}")
    
    return report

if __name__ == "__main__":
    asyncio.run(run_local_stress_test())

