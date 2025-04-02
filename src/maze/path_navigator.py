"""rect_to_tile_coords.py"""
from collections.abc import Sequence

import pygame as pg
import numpy as np

from src.constant import TILE_SIZE, SNAP_THRESHOLD
from .maze_node import MazeDirection, MazeNode
from .maze_coord import MazeCoord

def rect_to_maze_coords(rect_center: tuple[int, int]) -> MazeCoord:
    """
    Converts the center coordinates of a rect to maze tile coordinates.
    Args:
        rect_center (tuple[int, int]): The center coordinates of the rect 
            to be converted, represented as a tuple of integers (x, y).
    Returns:
        MazeCoord: An object representing the corresponding tile coordinates 
            in the maze.
    """
    return MazeCoord(
        int(rect_center[0] // MazeCoord.tile_size),
        int(rect_center[1] // MazeCoord.tile_size)
        )

def is_snap_within(
        rect_center: tuple[int, int],
        node: MazeNode,
        snap_threshold: int = SNAP_THRESHOLD,
        ) -> bool:
    """
    Check if the "center" of a rect is close enough to the center of a node.

    For example, if the rect is a tile and the node is a tile, this function checks if the
    two tiles are close enough to be considered "snapping" together.
    
    Args:
        rect_center (tuple[int, int]): The center coordinates of the rect to check.
        node (MazeNode): The maze node whose center is being compared.
        snap_threshold (int, optional): The maximum distance within which the rectangle's 
            center is considered to be snapping to the node's center. Defaults to SNAP_THRESHOLD.
    Returns:
        bool: True if the rectangle's center is within the snapping threshold of the node's center, 
        False otherwise.
    """
    node_center = node.pos.center
    checking_rect = pg.Rect(
        node_center[0] - snap_threshold,
        node_center[1] - snap_threshold,
        snap_threshold * 2, snap_threshold * 2
        )
    return checking_rect.collidepoint(rect_center[0], rect_center[1])

def direction_from(start_node: MazeNode, end_node: MazeNode):
    """
    Determines the direction from the start node to the end node.

    Args:
        start_node (MazeNode): The starting node.
        end_node (MazeNode): The target node.

    Returns:
        (MazeDirection | None): The direction from the start node to the end node 
        (e.g., MazeDirection.UP, MazeDirection.DOWN, MazeDirection.LEFT, MazeDirection.RIGHT), 
        or None if the nodes are not connected.
    """
    for pointing_direction, pointing_node in start_node.neighbors.items():
        if pointing_node[0] == end_node:
            return pointing_direction
    return None

def are_nodes_connected(*nodes: MazeNode) -> bool:
    """
    Determines if the given nodes are connected in sequence.

    Args:
        *nodes (MazeNode): A variable number of MazeNode objects to check for connectivity.

    Returns:
        bool: True if all the nodes are connected in sequence, False otherwise.

    Notes:
        - If fewer than two nodes are provided, the function returns True by default.
        - For two nodes, it checks if there is a direct connection between them.
        - For more than two nodes, it verifies that each consecutive pair of nodes is connected.
    """
    if len(nodes) < 2:
        return True
    if len(nodes) == 2:
        return direction_from(nodes[0], nodes[1]) is not None
    for i in range(len(nodes) - 1):
        if not direction_from(nodes[i], nodes[i + 1]):
            return False
    return True

def is_in_path_between(
        rect_center: tuple[int, int],
        start_node: MazeNode,
        end_node: MazeNode,
        ) -> bool:
    """
    Determines if a rect's center is within the path between two nodes.

    If this function returns True, it means that the object may be moving from one node to another.
    Otherwise, it is not in the path between the two nodes or it has reached the destination node.

    Args:
        rect_center (tuple[int, int]): The center coordinates of the rect.
        start_node (MazeNode): The starting node of the path.
        end_node (MazeNode): The ending node of the path.

    Returns:
        bool: True if the rectangle's center is within the path between the two nodes, 
        False otherwise.
    """
    if is_snap_within(rect_center, start_node):
        return True
    if is_snap_within(rect_center, end_node):
        return False

    connecting_direction = direction_from(start_node, end_node)
    if connecting_direction is None:
        return False
    start_rect, end_rect = start_node.pos.rect, end_node.pos.rect

    simulated_tile = pg.Rect(
        rect_center[0] - TILE_SIZE // 2,
        rect_center[1] - TILE_SIZE // 2,
        TILE_SIZE, TILE_SIZE
        )
    checking_line: tuple[tuple[int, int], tuple[int, int]]
    match connecting_direction:
        case MazeDirection.UP:
            checking_line = (start_rect.midtop, end_rect.midbottom)
        case MazeDirection.DOWN:
            checking_line = (start_rect.midbottom, end_rect.midtop)
        case MazeDirection.LEFT:
            checking_line = (start_rect.midleft, end_rect.midright)
        case MazeDirection.RIGHT:
            checking_line = (start_rect.midright, end_rect.midleft)
        case _:
            raise ValueError(f"Invalid direction: {connecting_direction}")
    # Check if the simulated tile collides with the line between the two nodes
    clipped_line = simulated_tile.clipline(*checking_line)
    if len(clipped_line) == 0:
        return False
    return True

def _move_to_node(
        rect_center: tuple[int, int],
        end_node: MazeNode,
        distance: int
        ) -> tuple[tuple[int, int], int]:
    """
    "Move" a rect to a specified node by a given distance.

    Parameters:
        rect_center (tuple[int, int]):
          The current center position of the rectangle as (x, y) coordinates.
        end_node (MazeNode):
          The target node to move towards..
        distance (int):
          The distance to move the rectangle. Must be a non-negative integer.
    Returns:
        tuple: A tuple containing
            - The new center position of the rectangle as (x, y) coordinates.
            - The remaining distance after the move. If this is 0,
            the rect is either not reached the end_node or currently at it.
    Raises:
        ValueError: If the provided distance is negative.
    Notes:
        - The function assumes that the rectangle is already within the path
        between the two nodes.
        - If the distance to move is greater than or equal to the distance to the end_node,
        the rectangle will be moved to the end_node's position,
        and the remaining distance will be adjusted accordingly.
        - The movement is calculated proportionally based on the distance and direction
        between the current position and the end_node.
    """
    if distance == 0:
        return rect_center, 0
    if distance < 0:
        raise ValueError("Distance must be non-negative")
    moving_direction = np.array(end_node.pos.center) - np.array(rect_center)
    max_distance = int(np.linalg.norm(moving_direction))
    if distance >= max_distance:
        return end_node.pos.center, distance - max_distance
    moving_destination = np.array(rect_center) + moving_direction * (distance / max_distance)
    new_x, new_y = int(moving_destination[0]), int(moving_destination[1])
    return (new_x, new_y), 0

def move_along_path(
        rect_center: tuple[int, int],
        path: Sequence[tuple[MazeNode, MazeNode]],
        distance: int
        ) -> tuple[list[tuple[MazeNode, MazeNode]], tuple[int, int]]:
    r"""
    Moves a rectangle along a specified path by a given distance.

    Args:
        rect_center (tuple[int, int]):
          The current center position of the rectangle as (x, y) coordinates.
        path (Sequence[tuple[MazeNode, MazeNode]]):
          The path to follow, represented as a sequence of tuples of MazeNode objects.
        distance (int):
          The distance to move along the path. Must be a non-negative integer.

    Returns:
        tuple: A tuple containing
        - The remaining path after the move as a list of tuples of MazeNode objects.
        - The updated center position of the rectangle as (x, y) coordinates.

    Raises:
        ValueError: If the provided distance is negative.
        TypeError: If the path is not a sequence.

    Notes:
        - If the distance is 0 or the path is empty, the rectangle's position remains unchanged.
        - The function assumes that the rectangle is already within the path between the nodes.
        - The rectangle moves along the path until the distance is exhausted or the path ends.
    """
    if distance < 0:
        raise ValueError("Distance must be non-negative")
    if not isinstance(path, Sequence):
        raise TypeError("Path must be a mutable sequence (e.g., list)")
    if len(path) == 0 or distance == 0:
        return path, rect_center

    remaining_path = list(path)
    for start_node, end_node in path:
        if is_in_path_between(rect_center, start_node, end_node):
            new_position, distance = _move_to_node(rect_center, end_node, distance)
            rect_center = new_position
        else:
            remaining_path = remaining_path[1:]
        if distance <= 0:
            return remaining_path, rect_center

    return remaining_path, rect_center
