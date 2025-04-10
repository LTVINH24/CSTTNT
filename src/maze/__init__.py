"""
This module initializes and provides access to various components and utilities 
for working with mazes. It imports and exposes classes, functions, and constants 
from submodules to facilitate maze creation, manipulation, and navigation.

Key Components:

- `maze_coord`:
    - `MazeCoord`: Represents maze coordinates with properties like `rect` and `center` 
      for pixel-based positioning.

- `maze_node`:
    - `MazeDirection`: Enum for navigation directions.
    - `MazeNode`: Represents maze nodes and their neighbors.

- `maze_parts`:
    - `MazePart`: Represents parts of a maze (e.g., walls, spaces, spawn points) 
      with traversal costs and visual properties.

- `maze_layout`:
    - `MazeLayout`: Defines the maze structure, including its graph representation, 
      weights, and points of interest.

- `maze_builder`:
    - `load_maze`: Loads maze data from files.
    - `build_maze`: Constructs the maze graph and prepares it for rendering.

- `path_navigator`:
    Utilities for pathfinding and navigation:
    - `rect_to_maze_coords`: Converts a rectangle's position to maze tile coordinates.
    - `find_path_containing_coord`: Finds the path containing a specific maze coordinate.
    - `is_snap_within`: Checks if a rectangle's center is within a snapping threshold 
      of a maze node's center.
    - `direction_from`: Determines the direction from one maze node to another.
    - `is_in_path_between`: Checks if a rectangle's center is within the path 
      between two maze nodes.
    - `move_along_path`: Moves a rectangle along a path of maze nodes by a given distance.
    - `are_nodes_connected`: Verifies if a sequence of maze nodes are connected.
    - `path_through_new_location`: Finds the portion of a path containing a specific location.

- `maze_supervisor`: Tools for managing maze levels:
    - `MazeLevel`: Represents a maze level, including layout, spawn points, and entities.
    - `set_up_level`: Sets up a maze level by loading and building the layout.
    - `render_maze_level`: Updates and renders the maze level, including its ghosts and layout.
"""

from .maze_coord import MazeCoord
from .maze_node import MazeDirection, MazeNode
from .maze_parts import MazePart
from .maze_layout import MazeLayout
from .maze_builder import load_maze, build_maze
from .path_navigator import (
  rect_to_maze_coords,
  find_path_containing_coord,
  is_snap_within, direction_from, is_in_path_between,
  move_along_path,
  are_nodes_connected,
  path_through_new_location,
)
from .maze_supervisor import MazeLevel, set_up_level, render_maze_level

__all__ = [
    "MazeCoord",
    "MazeDirection",
    "MazeNode",
    "MazePart",
    "MazeLayout",
    "load_maze",
    "build_maze",
    "rect_to_maze_coords",
    "find_path_containing_coord",
    "is_snap_within",
    "direction_from",
    "is_in_path_between",
    "move_along_path",
    "are_nodes_connected",
    "path_through_new_location",
    "MazeLevel",
    "set_up_level",
    "render_maze_level",
]
