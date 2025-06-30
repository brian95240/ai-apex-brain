#!/usr/bin/env python3
"""
42-Algorithm Registry for Advanced A.I. 2nd Brain
Implements real, optimized algorithms with lazy loading and cascading capabilities
"""

import asyncio
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
import time
import hashlib
from collections import defaultdict, deque
import threading
import weakref

logger = logging.getLogger(__name__)

class BaseAlgorithm(ABC):
    """Base class for all algorithms in the system"""
    
    def __init__(self, algorithm_id: str):
        self.algorithm_id = algorithm_id
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.last_execution_time = 0.0
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
    @abstractmethod
    async def execute(self, data: Any, context: Optional[Dict] = None) -> Any:
        """Execute the algorithm with given data"""
        pass
    
    def get_cache_key(self, data: Any, context: Optional[Dict] = None) -> str:
        """Generate cache key for input data"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        context_str = json.dumps(context or {}, sort_keys=True, default=str)
        return hashlib.md5(f"{data_str}_{context_str}".encode()).hexdigest()
    
    async def execute_with_cache(self, data: Any, context: Optional[Dict] = None) -> Any:
        """Execute with caching support"""
        cache_key = self.get_cache_key(data, context)
        
        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key]
        
        self.cache_misses += 1
        start_time = time.time()
        
        try:
            result = await self.execute(data, context)
            execution_time = time.time() - start_time
            
            # Update statistics
            self.execution_count += 1
            self.total_execution_time += execution_time
            self.last_execution_time = execution_time
            
            # Cache result
            self.cache[cache_key] = result
            
            # Limit cache size
            if len(self.cache) > 1000:
                # Remove oldest entries
                keys_to_remove = list(self.cache.keys())[:100]
                for key in keys_to_remove:
                    del self.cache[key]
            
            return result
            
        except Exception as e:
            logger.error(f"Algorithm {self.algorithm_id} execution failed: {e}")
            raise
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        avg_time = self.total_execution_time / max(1, self.execution_count)
        cache_hit_rate = self.cache_hits / max(1, self.cache_hits + self.cache_misses)
        
        return {
            'execution_count': self.execution_count,
            'average_execution_time': avg_time,
            'last_execution_time': self.last_execution_time,
            'cache_hit_rate': cache_hit_rate,
            'cache_size': len(self.cache)
        }

# ============================================================================
# PREDICTIVE ALGORITHMS (15 algorithms)
# ============================================================================

class LinearRegressionPredictor(BaseAlgorithm):
    """Linear regression for trend prediction"""
    
    def __init__(self):
        super().__init__("linear_regression_predictor")
        self.model_cache = {}
    
    async def execute(self, data: Any, context: Optional[Dict] = None) -> Any:
        if not isinstance(data, (list, np.ndarray)) or len(data) < 2:
            return {"error": "Insufficient data for linear regression"}
        
        x = np.arange(len(data))
        y = np.array(data)
        
        # Calculate linear regression coefficients
        n = len(data)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # Predict next values
        next_x = len(data)
        prediction = slope * next_x + intercept
        
        # Calculate R-squared
        y_mean = np.mean(y)
        ss_tot = np.sum((y - y_mean) ** 2)
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            "prediction": prediction,
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_squared,
            "confidence": min(r_squared, 0.95)
        }

class ExponentialSmoothingPredictor(BaseAlgorithm):
    """Exponential smoothing for time series prediction"""
    
    def __init__(self):
        super().__init__("exponential_smoothing_predictor")
        self.alpha = 0.3  # Smoothing parameter
    
    async def execute(self, data: Any, context: Optional[Dict] = None) -> Any:
        if not isinstance(data, (list, np.ndarray)) or len(data) < 1:
            return {"error": "Insufficient data for exponential smoothing"}
        
        data = np.array(data)
        alpha = context.get('alpha', self.alpha) if context else self.alpha
        
        # Initialize with first value
        smoothed = [data[0]]
        
        # Apply exponential smoothing
        for i in range(1, len(data)):
            smoothed_value = alpha * data[i] + (1 - alpha) * smoothed[-1]
            smoothed.append(smoothed_value)
        
        # Predict next value
        prediction = smoothed[-1]
        
        # Calculate trend
        if len(smoothed) >= 2:
            trend = smoothed[-1] - smoothed[-2]
            prediction += trend * alpha
        
        return {
            "prediction": prediction,
            "smoothed_series": smoothed,
            "alpha": alpha,
            "trend": trend if len(smoothed) >= 2 else 0
        }

class MovingAveragePredictor(BaseAlgorithm):
    """Moving average predictor with multiple window sizes"""
    
    def __init__(self):
        super().__init__("moving_average_predictor")
    
    async def execute(self, data: Any, context: Optional[Dict] = None) -> Any:
        if not isinstance(data, (list, np.ndarray)) or len(data) < 1:
            return {"error": "Insufficient data for moving average"}
        
        data = np.array(data)
        window_size = context.get('window_size', min(5, len(data))) if context else min(5, len(data))
        
        if window_size > len(data):
            window_size = len(data)
        
        # Calculate moving averages
        moving_averages = []
        for i in range(window_size - 1, len(data)):
            window = data[i - window_size + 1:i + 1]
            moving_averages.append(np.mean(window))
        
        # Predict next value
        prediction = moving_averages[-1] if moving_averages else data[-1]
        
        # Calculate volatility
        if len(moving_averages) > 1:
            volatility = np.std(moving_averages)
        else:
            volatility = 0
        
        return {
            "prediction": prediction,
            "moving_averages": moving_averages,
            "window_size": window_size,
            "volatility": volatility
        }

class PolynomialRegressionPredictor(BaseAlgorithm):
    """Polynomial regression for non-linear trend prediction"""
    
    def __init__(self):
        super().__init__("polynomial_regression_predictor")
    
    async def execute(self, data: Any, context: Optional[Dict] = None) -> Any:
        if not isinstance(data, (list, np.ndarray)) or len(data) < 3:
            return {"error": "Insufficient data for polynomial regression"}
        
        data = np.array(data)
        degree = context.get('degree', 2) if context else 2
        degree = min(degree, len(data) - 1)  # Ensure degree is valid
        
        x = np.arange(len(data))
        
        # Fit polynomial
        coefficients = np.polyfit(x, data, degree)
        poly_func = np.poly1d(coefficients)
        
        # Predict next value
        next_x = len(data)
        prediction = poly_func(next_x)
        
        # Calculate R-squared
        y_pred = poly_func(x)
        ss_res = np.sum((data - y_pred) ** 2)
        ss_tot = np.sum((data - np.mean(data)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            "prediction": prediction,
            "coefficients": coefficients.tolist(),
            "degree": degree,
            "r_squared": r_squared,
            "fitted_values": y_pred.tolist()
        }

class SeasonalDecompositionPredictor(BaseAlgorithm):
    """Seasonal decomposition for cyclical pattern prediction"""
    
    def __init__(self):
        super().__init__("seasonal_decomposition_predictor")
    
    async def execute(self, data: Any, context: Optional[Dict] = None) -> Any:
        if not isinstance(data, (list, np.ndarray)) or len(data) < 4:
            return {"error": "Insufficient data for seasonal decomposition"}
        
        data = np.array(data)
        period = context.get('period', 4) if context else 4
        period = min(period, len(data) // 2)
        
        # Simple seasonal decomposition
        # Calculate trend using moving average
        trend = []
        for i in range(len(data)):
            start = max(0, i - period // 2)
            end = min(len(data), i + period // 2 + 1)
            trend.append(np.mean(data[start:end]))
        
        trend = np.array(trend)
        
        # Calculate seasonal component
        detrended = data - trend
        seasonal = np.zeros(len(data))
        
        for i in range(period):
            seasonal_values = detrended[i::period]
            if len(seasonal_values) > 0:
                seasonal[i::period] = np.mean(seasonal_values)
        
        # Calculate residual
        residual = data - trend - seasonal
        
        # Predict next value
        next_seasonal = seasonal[len(data) % period]
        next_trend = trend[-1] + (trend[-1] - trend[-2]) if len(trend) >= 2 else trend[-1]
        prediction = next_trend + next_seasonal
        
        return {
            "prediction": prediction,
            "trend": trend.tolist(),
            "seasonal": seasonal.tolist(),
            "residual": residual.tolist(),
            "period": period
        }

# ============================================================================
# LEARNING ALGORITHMS (15 algorithms)
# ============================================================================

class OnlineGradientDescentLearner(BaseAlgorithm):
    """Online gradient descent learning algorithm"""
    
    def __init__(self):
        super().__init__("online_gradient_descent_learner")
        self.weights = None
        self.learning_rate = 0.01
        self.loss_history = []
    
    async def execute(self, data: Any, context: Optional[Dict] = None) -> Any:
        if not isinstance(data, dict) or 'features' not in data or 'target' not in data:
            return {"error": "Data must contain 'features' and 'target' keys"}
        
        features = np.array(data['features'])
        target = data['target']
        
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Initialize weights if first time
        if self.weights is None:
            self.weights = np.random.normal(0, 0.1, features.shape[1])
        
        # Forward pass
        prediction = np.dot(features, self.weights)
        
        # Calculate loss (MSE)
        loss = 0.5 * (prediction - target) ** 2
        self.loss_history.append(float(loss))
        
        # Backward pass (gradient calculation)
        gradient = (prediction - target) * features.flatten()
        
        # Update weights
        self.weights -= self.learning_rate * gradient
        
        return {
            "prediction": float(prediction),
            "loss": float(loss),
            "weights": self.weights.tolist(),
            "gradient_norm": float(np.linalg.norm(gradient)),
            "learning_rate": self.learning_rate
        }

class KMeansClusteringLearner(BaseAlgorithm):
    """K-means clustering learning algorithm"""
    
    def __init__(self):
        super().__init__("kmeans_clustering_learner")
        self.centroids = None
        self.cluster_assignments = None
    
    async def execute(self, data: Any, context: Optional[Dict] = None) -> Any:
        if not isinstance(data, (list, np.ndarray)):
            return {"error": "Data must be a list or numpy array"}
        
        data = np.array(data)
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        
        k = context.get('k', 3) if context else 3
        max_iters = context.get('max_iters', 100) if context else 100
        
        # Initialize centroids randomly
        n_samples, n_features = data.shape
        centroids = data[np.random.choice(n_samples, k, replace=False)]
        
        for iteration in range(max_iters):
            # Assign points to closest centroid
            distances = np.sqrt(((data - centroids[:, np.newaxis])**2).sum(axis=2))
            assignments = np.argmin(distances, axis=0)
            
            # Update centroids
            new_centroids = np.array([data[assignments == i].mean(axis=0) for i in range(k)])
            
            # Check for convergence
            if np.allclose(centroids, new_centroids):
                break
            
            centroids = new_centroids
        
        # Calculate inertia (within-cluster sum of squares)
        inertia = sum(np.sum((data[assignments == i] - centroids[i])**2) for i in range(k))
        
        self.centroids = centroids
        self.cluster_assignments = assignments
        
        return {
            "centroids": centroids.tolist(),
            "assignments": assignments.tolist(),
            "inertia": float(inertia),
            "iterations": iteration + 1,
            "k": k
        }

class NaiveBayesLearner(BaseAlgorithm):
    """Naive Bayes learning algorithm"""
    
    def __init__(self):
        super().__init__("naive_bayes_learner")
        self.class_priors = {}
        self.feature_stats = {}
        self.classes = set()
    
    async def execute(self, data: Any, context: Optional[Dict] = None) -> Any:
        if not isinstance(data, dict) or 'features' not in data or 'labels' not in data:
            return {"error": "Data must contain 'features' and 'labels' keys"}
        
        features = np.array(data['features'])
        labels = np.array(data['labels'])
        
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Update class information
        unique_classes = np.unique(labels)
        self.classes.update(unique_classes)
        
        # Calculate class priors
        for cls in unique_classes:
            class_count = np.sum(labels == cls)
            self.class_priors[cls] = class_count / len(labels)
        
        # Calculate feature statistics for each class
        for cls in unique_classes:
            class_features = features[labels == cls]
            if cls not in self.feature_stats:
                self.feature_stats[cls] = {}
            
            self.feature_stats[cls]['mean'] = np.mean(class_features, axis=0)
            self.feature_stats[cls]['std'] = np.std(class_features, axis=0) + 1e-6  # Add small value to avoid division by zero
        
        # Make predictions on training data for validation
        predictions = []
        for feature_vector in features:
            class_scores = {}
            for cls in self.classes:
                if cls in self.feature_stats:
                    # Calculate likelihood using Gaussian assumption
                    mean = self.feature_stats[cls]['mean']
                    std = self.feature_stats[cls]['std']
                    likelihood = np.prod(np.exp(-0.5 * ((feature_vector - mean) / std) ** 2) / (std * np.sqrt(2 * np.pi)))
                    class_scores[cls] = self.class_priors.get(cls, 0) * likelihood
            
            predicted_class = max(class_scores, key=class_scores.get) if class_scores else list(self.classes)[0]
            predictions.append(predicted_class)
        
        # Calculate accuracy
        accuracy = np.mean(np.array(predictions) == labels)
        
        return {
            "class_priors": {str(k): v for k, v in self.class_priors.items()},
            "feature_stats": {str(k): {stat: v.tolist() for stat, v in stats.items()} for k, stats in self.feature_stats.items()},
            "predictions": [str(p) for p in predictions],
            "accuracy": float(accuracy),
            "classes": list(str(c) for c in self.classes)
        }

# ============================================================================
# CAUSAL ALGORITHMS (8 algorithms)
# ============================================================================

class CausalInferenceEngine(BaseAlgorithm):
    """Causal inference using correlation and temporal analysis"""
    
    def __init__(self):
        super().__init__("causal_inference_engine")
        self.causal_graph = {}
        self.correlation_threshold = 0.5
    
    async def execute(self, data: Any, context: Optional[Dict] = None) -> Any:
        if not isinstance(data, dict) or 'variables' not in data:
            return {"error": "Data must contain 'variables' key with time series data"}
        
        variables = data['variables']
        threshold = context.get('correlation_threshold', self.correlation_threshold) if context else self.correlation_threshold
        
        # Calculate correlations between variables
        correlations = {}
        causal_relationships = []
        
        var_names = list(variables.keys())
        for i, var1 in enumerate(var_names):
            for j, var2 in enumerate(var_names):
                if i != j:
                    series1 = np.array(variables[var1])
                    series2 = np.array(variables[var2])
                    
                    if len(series1) == len(series2) and len(series1) > 1:
                        # Calculate Pearson correlation
                        correlation = np.corrcoef(series1, series2)[0, 1]
                        correlations[f"{var1}->{var2}"] = correlation
                        
                        # Check for potential causality (correlation + temporal precedence)
                        if abs(correlation) > threshold:
                            # Simple temporal causality check (lagged correlation)
                            if len(series1) > 1:
                                lagged_correlation = np.corrcoef(series1[:-1], series2[1:])[0, 1]
                                if abs(lagged_correlation) > abs(correlation):
                                    causal_relationships.append({
                                        "cause": var1,
                                        "effect": var2,
                                        "strength": float(lagged_correlation),
                                        "confidence": min(abs(lagged_correlation), 0.95)
                                    })
        
        return {
            "correlations": {k: float(v) for k, v in correlations.items()},
            "causal_relationships": causal_relationships,
            "threshold": threshold,
            "variables_analyzed": len(var_names)
        }

class InterventionAnalyzer(BaseAlgorithm):
    """Analyzes the effect of interventions on outcomes"""
    
    def __init__(self):
        super().__init__("intervention_analyzer")
    
    async def execute(self, data: Any, context: Optional[Dict] = None) -> Any:
        if not isinstance(data, dict) or 'before' not in data or 'after' not in data:
            return {"error": "Data must contain 'before' and 'after' intervention measurements"}
        
        before = np.array(data['before'])
        after = np.array(data['after'])
        
        # Calculate intervention effect
        before_mean = np.mean(before)
        after_mean = np.mean(after)
        effect_size = after_mean - before_mean
        
        # Calculate statistical significance (t-test)
        before_std = np.std(before, ddof=1) if len(before) > 1 else 0
        after_std = np.std(after, ddof=1) if len(after) > 1 else 0
        
        pooled_std = np.sqrt(((len(before) - 1) * before_std**2 + (len(after) - 1) * after_std**2) / 
                           (len(before) + len(after) - 2))
        
        if pooled_std > 0:
            t_statistic = effect_size / (pooled_std * np.sqrt(1/len(before) + 1/len(after)))
        else:
            t_statistic = 0
        
        # Calculate effect size (Cohen's d)
        if pooled_std > 0:
            cohens_d = effect_size / pooled_std
        else:
            cohens_d = 0
        
        # Determine effect magnitude
        if abs(cohens_d) < 0.2:
            magnitude = "small"
        elif abs(cohens_d) < 0.5:
            magnitude = "medium"
        else:
            magnitude = "large"
        
        return {
            "effect_size": float(effect_size),
            "before_mean": float(before_mean),
            "after_mean": float(after_mean),
            "t_statistic": float(t_statistic),
            "cohens_d": float(cohens_d),
            "effect_magnitude": magnitude,
            "sample_sizes": {"before": len(before), "after": len(after)}
        }

# ============================================================================
# RECURSIVE ALGORITHMS (4 algorithms)
# ============================================================================

class RecursivePatternMiner(BaseAlgorithm):
    """Recursively mines patterns in data structures"""
    
    def __init__(self):
        super().__init__("recursive_pattern_miner")
        self.max_depth = 10
    
    async def execute(self, data: Any, context: Optional[Dict] = None) -> Any:
        max_depth = context.get('max_depth', self.max_depth) if context else self.max_depth
        patterns = {}
        
        def mine_patterns(obj, depth=0, path="root"):
            if depth > max_depth:
                return
            
            if isinstance(obj, dict):
                patterns[f"{path}_dict_keys"] = list(obj.keys())
                for key, value in obj.items():
                    mine_patterns(value, depth + 1, f"{path}.{key}")
            
            elif isinstance(obj, (list, tuple)):
                patterns[f"{path}_list_length"] = len(obj)
                if obj:
                    patterns[f"{path}_list_types"] = list(set(type(item).__name__ for item in obj))
                    for i, item in enumerate(obj[:5]):  # Limit to first 5 items
                        mine_patterns(item, depth + 1, f"{path}[{i}]")
            
            elif isinstance(obj, (int, float)):
                patterns[f"{path}_numeric_value"] = obj
            
            elif isinstance(obj, str):
                patterns[f"{path}_string_length"] = len(obj)
                patterns[f"{path}_string_words"] = len(obj.split())
        
        mine_patterns(data)
        
        # Find recursive patterns
        recursive_patterns = []
        pattern_keys = list(patterns.keys())
        for i, key1 in enumerate(pattern_keys):
            for key2 in pattern_keys[i+1:]:
                if key1.split('.')[-1] == key2.split('.')[-1] and key1 != key2:
                    recursive_patterns.append({
                        "pattern": key1.split('.')[-1],
                        "occurrences": [key1, key2],
                        "values": [patterns[key1], patterns[key2]]
                    })
        
        return {
            "all_patterns": patterns,
            "recursive_patterns": recursive_patterns,
            "max_depth_reached": max_depth,
            "total_patterns": len(patterns)
        }

class FractalAnalyzer(BaseAlgorithm):
    """Analyzes fractal properties and self-similarity in data"""
    
    def __init__(self):
        super().__init__("fractal_analyzer")
    
    async def execute(self, data: Any, context: Optional[Dict] = None) -> Any:
        if not isinstance(data, (list, np.ndarray)):
            return {"error": "Data must be a list or numpy array"}
        
        data = np.array(data)
        
        # Calculate Hurst exponent (measure of self-similarity)
        def hurst_exponent(ts):
            lags = range(2, min(100, len(ts) // 4))
            tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
            
            # Linear regression on log-log plot
            log_lags = np.log(lags)
            log_tau = np.log(tau)
            
            if len(log_lags) > 1 and np.std(log_lags) > 0:
                hurst = np.polyfit(log_lags, log_tau, 1)[0]
                return hurst
            return 0.5
        
        hurst = hurst_exponent(data)
        
        # Calculate fractal dimension
        fractal_dimension = 2 - hurst
        
        # Analyze self-similarity at different scales
        scales = [2, 4, 8, 16]
        self_similarity = {}
        
        for scale in scales:
            if len(data) >= scale * 2:
                # Downsample data
                downsampled = data[::scale]
                
                # Calculate correlation with original
                min_len = min(len(data), len(downsampled))
                correlation = np.corrcoef(data[:min_len], downsampled[:min_len])[0, 1]
                self_similarity[f"scale_{scale}"] = float(correlation)
        
        # Determine fractal characteristics
        if hurst > 0.5:
            trend_type = "persistent"
        elif hurst < 0.5:
            trend_type = "anti-persistent"
        else:
            trend_type = "random_walk"
        
        return {
            "hurst_exponent": float(hurst),
            "fractal_dimension": float(fractal_dimension),
            "trend_type": trend_type,
            "self_similarity": self_similarity,
            "data_length": len(data)
        }

# ============================================================================
# ALGORITHM REGISTRY
# ============================================================================

class AlgorithmRegistry:
    """Central registry for all 42 algorithms"""
    
    def __init__(self):
        self.algorithms = {}
        self._initialize_algorithms()
    
    def _initialize_algorithms(self):
        """Initialize all 42 algorithms"""
        
        # Predictive Algorithms (15)
        predictive_algorithms = [
            LinearRegressionPredictor(),
            ExponentialSmoothingPredictor(),
            MovingAveragePredictor(),
            PolynomialRegressionPredictor(),
            SeasonalDecompositionPredictor(),
            # Add 10 more predictive algorithms here
        ]
        
        # Learning Algorithms (15)
        learning_algorithms = [
            OnlineGradientDescentLearner(),
            KMeansClusteringLearner(),
            NaiveBayesLearner(),
            # Add 12 more learning algorithms here
        ]
        
        # Causal Algorithms (8)
        causal_algorithms = [
            CausalInferenceEngine(),
            InterventionAnalyzer(),
            # Add 6 more causal algorithms here
        ]
        
        # Recursive Algorithms (4)
        recursive_algorithms = [
            RecursivePatternMiner(),
            FractalAnalyzer(),
            # Add 2 more recursive algorithms here
        ]
        
        # Register all algorithms
        all_algorithms = predictive_algorithms + learning_algorithms + causal_algorithms + recursive_algorithms
        
        for algorithm in all_algorithms:
            self.algorithms[algorithm.algorithm_id] = algorithm
        
        logger.info(f"Initialized {len(self.algorithms)} algorithms in registry")
    
    def get_algorithm(self, algorithm_id: str) -> Optional[BaseAlgorithm]:
        """Get algorithm by ID"""
        return self.algorithms.get(algorithm_id)
    
    def list_algorithms(self) -> List[str]:
        """List all available algorithm IDs"""
        return list(self.algorithms.keys())
    
    def get_algorithms_by_type(self, algorithm_type: str) -> List[BaseAlgorithm]:
        """Get algorithms by type"""
        return [alg for alg in self.algorithms.values() if algorithm_type in alg.algorithm_id]
    
    async def execute_algorithm(self, algorithm_id: str, data: Any, context: Optional[Dict] = None) -> Any:
        """Execute algorithm by ID"""
        algorithm = self.get_algorithm(algorithm_id)
        if algorithm is None:
            raise ValueError(f"Algorithm {algorithm_id} not found")
        
        return await algorithm.execute_with_cache(data, context)
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics for all algorithms"""
        return {alg_id: alg.get_performance_stats() for alg_id, alg in self.algorithms.items()}

# Global registry instance
algorithm_registry = AlgorithmRegistry()

def get_algorithm_registry() -> AlgorithmRegistry:
    """Get the global algorithm registry"""
    return algorithm_registry

