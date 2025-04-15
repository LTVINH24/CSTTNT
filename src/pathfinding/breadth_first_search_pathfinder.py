"""
This module implements the Breadth First Search (BFS) algorithm for the blue ghost.
"""

from collections import deque
from src.maze import MazeNode
from src.maze import MazeDirection
from .pathfinder import Pathfinder, PathfindingResult
from .pathfinding_monitor import pathfinding_monitor

@pathfinding_monitor
def breadth_first_search_path_finder(
    maze_graph: list[MazeNode],
    start_location: tuple[MazeNode, MazeNode | None],
    target_location: tuple[MazeNode, MazeNode | None],
) -> PathfindingResult:
    """
    Finds a path in a maze graph from a start location to a target location.

    TODO: Provide a detailed description of the algorithm used for pathfinding.
    
    Args:
        maze_graph (list[MazeNode]):
            The graph representation of the maze, where each node represents a position in the maze.
        start_location (tuple[MazeNode, MazeNode | None]):
            A tuple of one or two MazeNodes.

            If this is a tuple of one node, it means that the object is standing on a node.

            If this is a tuple of two nodes, it means that the object is currently moving
            from the first node to the second node. In this case, **both nodes should be included
            at the start of the returning path at any order**.
          
        target_location (tuple[MazeNode, MazeNode | None]):
            Similar to **_start_location**, but for the goal location.

            If this is a tuple of two nodes, **both nodes should be included at the end
            of the returning path at any order**.
    Returns:
        PathfindingResult:
            An object containing the path from the start to the target and any additional metadata.
    """

    print(target_location)
    start_path = []
    if len(start_location) > 1 and start_location[1] is not None:
        starting_node = start_location[1]
        starting_path = [start_location[0]]
    else:
        starting_node = start_location[0]
    
    target_node = target_location[0]
    target_second_node = target_location[1] if len(target_location) > 1 else None

    queue = [(starting_node, starting_path)]
    visited = set()
    expanded_nodes = []

    while queue:
        current_node, path = queue.popLeft()
        if current_node == target_node or current_node == target_second_node:
            final_path = path + [current_node]
            if target_second_node is not None and target_second_node not in final_path:
                final_path.append(target_second_node)
            return PathfindingResult(final_path, expanded_nodes)
        
        if current_node not in visited:
            visited.add(current_node)
            expanded_nodes.append(current_node)
            
            for neighbor, _ in current_node.neighbors.values():
                if neighbor not in visited:
                    queue.append((neighbor, path + [current_node]))

    return PathfindingResult([], expanded_nodes)

assert isinstance(breadth_first_search_path_finder, Pathfinder)
