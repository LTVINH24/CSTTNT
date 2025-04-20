"""
This module implements the Breadth-First Search (BFS) algorithm for the blue ghost.
"""

from collections import deque
from src.maze import MazeNode
from .pathfinder import Pathfinder, PathfindingResult
from .pathfinding_monitor import pathfinding_monitor

@pathfinding_monitor
def breadth_first_search_path_finder(
    _maze_graph: list[MazeNode],
    start_location: tuple[MazeNode, MazeNode | None],
    target_location: tuple[MazeNode, MazeNode | None],
) -> PathfindingResult:
    """
    Finds a path in a maze graph from a start location to a target location
    using Breadth-First Search.

    BFS explores all neighbors at the present depth before moving on
    to nodes at the next depth level.
    It uses a queue to keep track of nodes to be explored,
    and visits the earliest discovered node first.

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
            Similar to **start_location**, but for the goal location.

            If this is a tuple of two nodes, **both nodes should be included at the end
            of the returning path at any order**.
    Returns:
        PathfindingResult:
            An object containing the path from the start to the target and any additional metadata.
    """

    start_path = []
    expanded_nodes = [start_location[0]]
    if start_location[1] is not None:
        expanded_nodes.append(start_location[1])
        starting_node = start_location[1]
        start_path = [start_location[0]]
    else:
        starting_node = start_location[0]

    target_node = target_location[0]
    target_second_node = None
    if target_location[1] is not None:
        target_second_node = target_location[1]

    queue = deque([(starting_node, start_path)])
    visited = set()


    while queue:
        current_node, path = queue.popleft()
        if current_node == target_node:
            final_path = path + [current_node]
            if target_second_node is not None and target_second_node not in final_path:
                final_path.append(target_second_node)
            return PathfindingResult(final_path, expanded_nodes)

        if current_node == target_second_node:
            final_path = path + [current_node]
            if target_node is not None and target_node not in final_path:
                final_path.append(target_node)
            return PathfindingResult(final_path, expanded_nodes)

        if current_node not in visited:
            visited.add(current_node)
            expanded_nodes.append(current_node)

            for neighbor, _ in current_node.neighbors.values():
                if neighbor not in visited:
                    queue.append((neighbor, path + [current_node]))

    return PathfindingResult([], expanded_nodes)

assert isinstance(breadth_first_search_path_finder, Pathfinder)
