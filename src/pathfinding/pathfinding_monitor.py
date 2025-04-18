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
from src.pathfinding import Pathfinder, PathfindingResult

LOGGER_PATH = os.path.join(BASE_PATH, "src", "logs")
os.makedirs(os.path.dirname(LOGGER_PATH), exist_ok=True)  # Ensure the directory exists
LOGGER_PATH = os.path.join(LOGGER_PATH, "pathfinding_monitor.log")

logger = logging.getLogger("shared_pathfinding_logger")
logger.setLevel(logging.INFO)

if not logger.hasHandlers():
    handler = logging.FileHandler(LOGGER_PATH)  # Save logs to the specified file
    formatter = logging.Formatter(
        '%(asctime)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
        )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def pathfinding_monitor(func: Pathfinder) -> Pathfinder:
    """
    Decorator to monitor the pathfinding process.

    TODO: Describe things being tracked here
    """
    def wrapper(*args, **kwargs):
        # Get the function signature and bind arguments to it
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()  # Apply default values for missing arguments

        # Print the function arguments for monitoring
        print(f"Pathfinding: {func.__name__}, ", end="")
        if "start_location" in bound_args.arguments:
            start_location: MazeNode = bound_args.arguments["start_location"]
            print(f"{start_location} to ", end="")
        else:
            print("??? to ", end="")
        if "target_location" in bound_args.arguments:
            target_location: MazeNode = bound_args.arguments["target_location"]
            print(f"{target_location}")
        elif "_target_location" in bound_args.arguments:
            target_location: MazeNode = bound_args.arguments["_target_location"]
            print(f"{target_location}")
        else:
            print("???")

        # Start memory and time tracking
        tracemalloc.start()
        start_time = time.time()

        result: PathfindingResult = func(*args, **kwargs)

        # Stop memory tracking and calculate peak memory usage
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end_time = time.time()
        wrapper.last_stats = {
            'search_time': end_time - start_time,
            'memory_peak': peak,
            'expanded_nodes': len(result.expanded_nodes)
        }

        # Log the results
        logger.info(
            "%s took %.6fs, expanded %d nodes, peak memory usage: %d bytes",
            func.__name__,
            wrapper.last_stats['search_time'],
            wrapper.last_stats['expanded_nodes'],
            wrapper.last_stats['memory_peak']
        )

        def print_path(nodes: list[MazeNode]):
            print("Path: ", end="")
            for node in nodes:
                print(f"{node} => ", end="")
            print("(end)")
        print_path(result.path)
        return result

    wrapper.last_stats = {} # Initialize last_stats attribute for the wrapper function
    return wrapper
