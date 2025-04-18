"""
Pathfinding Monitor

This module provides a decorator to monitor the pathfinding process.
"""
import inspect
import tracemalloc
import time
import logging

from src.maze import MazeNode
from src.pathfinding import Pathfinder, PathfindingResult

# Configure the logger
logging.basicConfig(
    filename="pathfinding_monitor.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

def pathfinding_monitor(func: Pathfinder) -> Pathfinder:
    """
    Decorator to monitor the pathfinding process.
    """
    def wrapper(*args, **kwargs):
        # Start memory and time tracking
        tracemalloc.start()
        start_time = time.time()

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
        result: PathfindingResult = func(*args, **kwargs)

        # Stop memory and time tracking
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Save stats into last_stats directly on the wrapper function
        wrapper.last_stats = {
            "search_time": end_time - start_time,
            "memory_peak": peak,
            "expanded_nodes": len(result.expanded_nodes)
        }
        # Log the statistics
        logging.info("Pathfinding: %s", func.__name__)
        logging.info("Execution time: %.6f seconds", end_time - start_time)
        logging.info("Memory usage: Current=%.6f MB, Peak=%.6f MB", current / 10**6, peak / 10**6)
        logging.info("Expanded nodes: %d", len(result.expanded_nodes))


        # Print the path
        def print_path(nodes: list[MazeNode]):
            print("Path: ", end="")
            for node in nodes:
                print(f"{node} => ", end="")
            print("(end)")
        print_path(result.path)

        return result

    wrapper.last_stats = {}  # Initialize last_stats on the wrapper function
    return wrapper
