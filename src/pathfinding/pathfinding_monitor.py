"""
Pathfinding Monitor

This module provides a decorator to monitor the pathfinding process.
"""
import os
import logging
import inspect
import tracemalloc
import time

from src.constant import BASE_PATH
from src.maze import MazeNode
from .pathfinder import Pathfinder, PathfindingResult

# Đường dẫn đến thư mục logs
LOGS_DIR = os.path.join(BASE_PATH, "src", "logs")

# Tạo thư mục logs nếu chưa tồn tại
os.makedirs(LOGS_DIR, exist_ok=True)

# Đường dẫn đến file log
LOGGER_PATH = os.path.join(LOGS_DIR, "pathfinding_monitor.log")

def pathfinding_monitor(func: Pathfinder) -> Pathfinder:
    """
    Decorator to monitor the pathfinding process.
    """
    logger = logging.getLogger(func.__name__)
    logger.setLevel(logging.INFO)
    logger_path = os.path.join(LOGS_DIR, f"{func.__name__}.log")

    if not logger.hasHandlers():
        handler = logging.FileHandler(logger_path)
        formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    def wrapper(*args, **kwargs):
        # Get the function signature and bind arguments to it
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()  # Apply default values for missing arguments

        start_location = bound_args.arguments.get("start_location")
        target_location = bound_args.arguments.get("target_location")

        # Start memory and time tracking
        tracemalloc.start()
        start_time = time.time()

        result: PathfindingResult = func(*args, **kwargs)

        # Calculate path length (steps)
        path_length = len(result.path) - 1 if result.path else 0
        # Calculate total path weight (if possible)
        path_weight = 0
        if len(result.path) > 1:
            for i in range(len(result.path) - 1):
                current = result.path[i]
                next_node = result.path[i + 1]
                # Find the edge between current and next_node
                for neighbor, cost in current.neighbors.values():
                    if neighbor == next_node:
                        path_weight += cost
                        break

        # Stop memory tracking and calculate peak memory usage
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end_time = time.time()
        wrapper.last_stats = {
            'search_time': end_time - start_time,
            'memory_peak': peak,
            'expanded_nodes': len(result.expanded_nodes),
            'path_length': path_length,
            'path_weight': path_weight
        }

        def path_as_str(nodes: list[MazeNode]) -> str:
            if not nodes:
                return "(empty)"
            path_str = ""
            path_str = " => ".join(str(node) for node in nodes)
            path_str += "(end)"
            return path_str
        # Log the results
        log_message = (
            f"from {start_location} to {target_location}, "
            f"path: {path_as_str(result.path)}"
        )
        logger.info(log_message)
        print(f"{func.__name__} - {log_message}")

        return result

    wrapper.last_stats = {} # Initialize last_stats attribute for the wrapper function
    return wrapper
