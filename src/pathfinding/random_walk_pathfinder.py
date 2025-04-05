"""
Random Walk Pathfinding Algorithm

This module implements a random walk pathfinding algorithm for navigating through a maze graph.
The algorithm randomly selects neighboring nodes to traverse from a given starting node,
creating a path of a specified length.
"""
import random

from src.maze import MazeNode
from .pathfinder import Pathfinder, PathfindingResult
from .pathfinding_monitor import pathfinding_monitor

PATH_LENGTH = 7
@pathfinding_monitor
def random_walk_path_finder(
    _maze_graph: list[MazeNode],
    start_location: tuple[MazeNode, MazeNode | None], # max-length = 2
    _target_location: tuple[MazeNode, MazeNode | None], # max-length = 2
) -> PathfindingResult:
    """
    Simulates a random walk through a maze graph starting from a given 
    location and generates a path of a predefined length.
    
    It randomly selects neighboring nodes to traverse from the starting node
    specified by the starting location.

    Args:
        maze_graph (list[MazeNode]): The graph representation of the maze.
        start_location (tuple[MazeNode, MazeNode | None]): The starting location for the path.
        target_location (tuple[MazeNode, MazeNode | None]): The target location for the path.

    Returns:
        PathfindingResult: A result containing the random path and the expanded nodes.
    """
    starting_node = start_location[0] if len(start_location) <= 1 else start_location[1]
    path_length = PATH_LENGTH  # Default path length

    # Generate a random path
    path = list(start_location)
    expanded_nodes = [starting_node]
    _current_node = starting_node
    for _ in range(path_length):
        next_node: MazeNode = random.choice(
            list(
                filter(None, _current_node.neighbors.values())
            )
        )[0]  # Only take the node part, not along with the weight part

        # Update the path and expanded nodes
        path.append(next_node)
        expanded_nodes.append(next_node)
        _current_node = next_node

    # Return the pathfinding result
    return PathfindingResult(path, expanded_nodes)

assert isinstance(random_walk_path_finder, Pathfinder), \
  "random_walk_path_finder must be a callable of type Pathfinder"
