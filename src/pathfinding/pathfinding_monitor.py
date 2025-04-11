"""
Pathfinding Monitor

This module provides a decorator to monitor the pathfinding process.
"""
import inspect
# TODO: Remove this import if not needed, otherwise, remove the pylint disable/enable comments.
# pylint: disable=unused-import
import tracemalloc # suggestion for tracing memory usage
# pylint: enable=unused-import

from src.maze import MazeNode
from src.pathfinding import Pathfinder, PathfindingResult

def pathfinding_monitor(func: Pathfinder) -> Pathfinder:
    """
    Decorator to monitor the pathfinding process.

    TODO: Describe things being tracked here
    """
    def wrapper(*args, **kwargs):
        # TODO: Set up actual monitoring logic here
        # TODO: Consider logging in a separate file for easier data collection

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
        # TODO: Add actual monitoring logic here
        def print_path(nodes: list[MazeNode]):
            print("Path: ", end="")
            for node in nodes:
                print(f"{node} => ", end="")
            print("(end)")
        print_path(result.path)
        return result

    return wrapper
