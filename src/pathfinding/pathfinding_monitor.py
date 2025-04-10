"""
Pathfinding Monitor

This module provides a decorator to monitor the pathfinding process.
"""
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
        print("Starting pathfinding...")
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
