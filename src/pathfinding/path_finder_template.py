"""
This module provides a random walk pathfinder function for generating a random path 
through a maze graph. The function implements a random walk algorithm, starting from 
a given location and randomly selecting neighboring nodes to traverse until a 
predefined path length is reached.
Functions:
    random_walk_path_finder: Generates a random path through a maze graph using a 
    random walk algorithm.
Classes:
    PathfindingResult: Represents the result of a pathfinding operation, including 
Constants:
    PATH_LENGTH: The default length of the random path to be generated.
"""
import random

from src.maze import MazeNode
from .pathfinder import Pathfinder, PathfindingResult

PATH_LENGTH = 5
def random_walk_path_finder(
    _maze_graph: list[MazeNode],
    start_location: tuple[MazeNode, MazeNode | None], # max-length = 2
    _target_location: tuple[MazeNode, MazeNode | None], # max-length = 2
) -> PathfindingResult:
    """
    Random walk pathfinder function that returns a random pathfinding result.

    Args:
        maze_graph (list[MazeNode]): The graph representation of the maze.
        start_location (tuple[MazeNode, MazeNode | None]): The starting location for the path.
        target_location (tuple[MazeNode, MazeNode | None]): The target location for the path.

    Returns:
        PathfindingResult: A result containing the random path and an empty list for costs.
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
