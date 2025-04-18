"""
This module provides utility functions and methods for navigating a maze 
and managing the movement of a rect (the position of the game object) within the maze.

Functions:
    rect_to_maze_coords:
        Converts a rectangle's position to maze tile coordinates.
    find_path_containing_coord:
        Finds the path containing the current maze coordinates.
    is_snap_within:
        Checks if the center of a rectangle is within a snapping threshold of a maze node's center.
    direction_from:
        Determines the direction from one maze node to another.
    are_nodes_connected:
        Checks if a sequence of maze nodes are connected.
    is_in_path_between:
        Determines if a rectangle's center is within the path between two maze nodes.
    _move_to_node:
        Moves a rect towards a specified maze node by a given distance.
    move_along_path:
        Moves a rect along a specified path of maze nodes by a given distance.
    path_through_new_location:
        Finds the portion of a path that contains a specified location in a sequence of maze nodes.
"""
from collections.abc import Sequence

import pygame as pg
import numpy as np

from src.constant import TILE_SIZE, SNAP_THRESHOLD
from .maze_node import MazeDirection, MazeNode
from .maze_coord import MazeCoord

def rect_to_maze_coords(
    rect: pg.Rect,
    tile_size: int = MazeCoord.tile_size,
    snap_threshold: int = SNAP_THRESHOLD
    ) -> tuple[MazeCoord, MazeCoord | None]:
    """
    Converts a rectangle's position to maze tile coordinates.

    This function takes a rectangle (represented by a `pg.Rect` object) and calculates 
    the corresponding maze tile coordinates based on the rectangle's top-left position 
    and the maze's tile size.
    
    It also determines if the rectangle is aligned with the 
    maze grid or if it overlaps multiple tiles.

    Args:
        rect (pg.Rect): A rectangle object whose position is to be converted into 
            maze tile coordinates.
        tile_size (int, optional): The size of each maze tile.
            Defaults to the class variable MazeCoord.tile_size.
        snap_threshold (int, optional): The maximum allowable offset for a rectangle 
            to be considered aligned with the maze grid. Defaults to SNAP_THRESHOLD.

    Returns:
        (tuple[MazeCoord, MazeCoord | None]): A tuple containing:
    - The primary `MazeCoord` object representing the nearest tile coordinates 
    - An optional secondary `MazeCoord` object if the rectangle overlaps 
      with an adjacent tile. If the rectangle is perfectly aligned with a 
      single tile, this value will be `None`.

    Warnings:
        - If the rectangle is not aligned with the maze grid both horizontally and 
          vertically, a warning is printed, and the function attempts to treat the 
          rectangle as snapped to either the horizontal or vertical grid alignment 
          based on the larger remainder.
    """
    nearest_tile_x = round((rect.topleft[0] - MazeCoord.maze_offset[0]) / tile_size)
    nearest_tile_y = round((rect.topleft[1] - MazeCoord.maze_offset[1]) / tile_size)
    x_remainder = rect.topleft[0] - (nearest_tile_x * tile_size + MazeCoord.maze_offset[0])
    y_remainder = rect.topleft[1] - (nearest_tile_y * tile_size + MazeCoord.maze_offset[1])
    if abs(x_remainder) <= snap_threshold and abs(y_remainder) <= snap_threshold:
        return MazeCoord(nearest_tile_x, nearest_tile_y), None

    if abs(x_remainder) <= snap_threshold:
        return MazeCoord(nearest_tile_x, nearest_tile_y), MazeCoord(
            nearest_tile_x, nearest_tile_y + 1 if y_remainder > 0 else nearest_tile_y - 1
            )

    if abs(y_remainder) <= snap_threshold:
        return MazeCoord(nearest_tile_x, nearest_tile_y), MazeCoord(
            nearest_tile_x + 1 if x_remainder > 0 else nearest_tile_x - 1, nearest_tile_y
            )

    print(f"Warning: rect {rect} is not aligned with the maze grid (horizontally AND vertically).")
    if abs(x_remainder) > abs(y_remainder):
        print(f"-------: treated {rect} as if it is snapped with the maze grid horizontally.")
        return MazeCoord(nearest_tile_x, nearest_tile_y), MazeCoord(
            nearest_tile_x + 1 if x_remainder > 0 else nearest_tile_x - 1, nearest_tile_y
            )
    print(f"-------: treated {rect} as if it is snapped with the maze grid vertically.")
    return MazeCoord(nearest_tile_x, nearest_tile_y), MazeCoord(
    nearest_tile_x, nearest_tile_y + 1 if y_remainder > 0 else nearest_tile_y - 1
    )

# pylint: disable=too-many-branches
def find_path_containing_coord(
    current_coord: tuple[MazeCoord, MazeCoord | None],
    maze_dict: dict[MazeCoord, MazeNode],
    maze_shape: tuple[int, int],
) -> tuple[MazeNode, MazeNode | None] | None:
# pylint: enable=too-many-branches
    """
    Get the path containing the current maze coordinates.

    Args:
        current_coord (tuple[MazeCoord, MazeCoord | None]): The current maze coordinates.
        maze_dict (dict[MazeCoord, MazeNode]): A dictionary mapping maze coordinates to maze nodes.
        maze_shape (tuple[int, int]): The shape of the maze as (width, height).

    Returns:
        out (tuple[MazeNode, MazeNode | None] | None):
            A tuple containing the start and end nodes of the path, or None if no path is found. 
    """
    if current_coord[1] is not None and current_coord[0] == current_coord[1]:
        current_coord = (current_coord[0], None)
    if current_coord[1] is None and current_coord[0] in maze_dict:
        return maze_dict[current_coord[0]], None

    start_node: MazeNode | None = None
    end_node: MazeNode | None = None
    if current_coord[1] is None or current_coord[0].y == current_coord[1].y:
        current_left: MazeCoord = min(
            current_coord, key=lambda coord: coord.x if coord else float('inf')
        )
        current_right: MazeCoord = max(
            current_coord, key=lambda coord: coord.x if coord else float('-inf')
        )
        while current_left.x >= 0:
            if current_left in maze_dict:
                start_node = maze_dict[current_left]
                break
            current_left = MazeCoord(current_left.x - 1, current_left.y)
        while current_right.x <= maze_shape[0] - 1:
            if current_right in maze_dict:
                end_node = maze_dict[current_right]
                break
            current_right = MazeCoord(current_right.x + 1, current_right.y)
    if start_node is not None and end_node is not None:
        return start_node, end_node
    if current_coord[1] is None or current_coord[0].x == current_coord[1].x:
        current_top: MazeCoord = min(
            current_coord, key=lambda coord: coord.y if coord else float('inf')
            )
        current_bottom: MazeCoord = max(
            current_coord, key=lambda coord: coord.y if coord else float('-inf')
            )
        while current_top.y >= 0:
            if current_top in maze_dict:
                start_node = maze_dict[current_top]
                break
            current_top = MazeCoord(current_top.x, current_top.y - 1)
        while current_bottom.y <= maze_shape[1] - 1:
            if current_bottom in maze_dict:
                end_node = maze_dict[current_bottom]
                break
            current_bottom = MazeCoord(current_bottom.x, current_bottom.y + 1)
    if start_node is not None and end_node is not None:
        return start_node, end_node
    return None

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
        distance: int,
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
        path: Sequence[MazeNode],
        distance: int,
        ) -> tuple[list[MazeNode], tuple[int, int]]:
    """
    Moves a rectangle along a specified path by a given distance.

    *(If the rect center happens to snap with a node after moving enough distance,
    the node(s) before it would be removed from the path)*

    Args:
        rect_center (tuple[int, int]):
          The current center position of the rectangle as (x, y) coordinates.
        path (Sequence[MazeNode]):
          The path to follow, represented as a sequence of MazeNode objects.
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
    if len(path) <= 1 or distance == 0:
        return path, rect_center

    remaining_path = list(path)
    while distance > 0 and len(remaining_path) > 1:
        start_node, end_node = remaining_path[0], remaining_path[1]
        if is_in_path_between(rect_center, start_node, end_node):
            new_position, distance = _move_to_node(rect_center, end_node, distance)
            rect_center = new_position
            if distance == 0 and is_snap_within(rect_center, end_node):
                # The rect has reached the end node
                remaining_path = remaining_path[1:]
        else:
            # Also happens if the rect is snapping to the second node
            remaining_path = remaining_path[1:]

    return remaining_path, rect_center

def path_through_new_location(
    checking_path: Sequence[MazeNode],
    location: tuple[MazeNode, MazeNode | None],
) -> Sequence[MazeNode] | None:
    """
    Finds the portion of a path that contains a specified location in a sequence of maze nodes.

    This function checks if a given location (a single node or an edge between two nodes) 
    exists within the provided path.

    Args:
        checking_path (Sequence[MazeNode]):
            The path to search, represented as a sequence of MazeNode objects.
        location (tuple[MazeNode, MazeNode | None]): The location to find in the path.
            - If the second element of the tuple is `None`, it represents a single node.
            - If the tuple contains two nodes, it represents an edge between the two nodes.

    Returns:
        out (Sequence[MazeNode] | None):
            A sequence of MazeNode objects representing the portion of the path
            containing the location. If the location is not found, returns `None`.
    """
    if len(checking_path) < 2:
        return None

    if location[1] is None:
        # Single node case
        for index, node in enumerate(checking_path):
            if node == location[0]:
                return checking_path[:index + 1]
    else:
        # Edge case
        for index in range(len(checking_path) - 1):
            if (
                checking_path[index] == location[0]
                and checking_path[index + 1] == location[1]
            ) or (
                checking_path[index] == location[1]
                and checking_path[index + 1] == location[0]
            ):
                return checking_path[:index + 1]

    return None
