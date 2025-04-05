"""
TODO: Provide a reasonable description for your module.
"""
# TODO: Remove `np` if not used
# pylint: disable=unused-import
import numpy as np
# pylint: enable=unused-import

from src.maze import MazeNode
from .pathfinder import Pathfinder, PathfindingResult
from .pathfinding_monitor import pathfinding_monitor

# TODO: Remove the `-` prefix from the function name and add a proper name.
@pathfinding_monitor
def your_path_finder(
    _maze_graph: list[MazeNode],
    _start_location: tuple[MazeNode, MazeNode | None],
    _target_location: tuple[MazeNode, MazeNode | None],
) -> PathfindingResult:
    """
    Finds a path in a maze graph from a start location to a target location.

    TODO: Provide a detailed description of the algorithm used for pathfinding.
    
    Args:
        _maze_graph (list[MazeNode]):
            The graph representation of the maze, where each node represents a position in the maze.
        _start_location (tuple[MazeNode, MazeNode | None]):
            A tuple of one or two MazeNodes.

            If this is a tuple of one node, it means that the object is standing on a node.

            If this is a tuple of two nodes, it means that the object is currently moving
            from the first node to the second node. In this case, **both nodes should be included
            at the start of the returning path at any order**.
          
        _target_location (tuple[MazeNode, MazeNode | None]):
            Similar to **_start_location**, but for the goal location.

            If this is a tuple of two nodes, **both nodes should be included at the end
            of the returning path at any order**.
    Returns:
        PathfindingResult:
            An object containing the path from the start to the target and any additional metadata.
    """
    return PathfindingResult([], [])

assert isinstance(your_path_finder, Pathfinder)
