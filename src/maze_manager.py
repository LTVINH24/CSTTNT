"""
Maze Manager Module.

This module provides classes and functions to manage and process maze levels for a Pacman-like game. 
It includes functionality for loading maze levels, visualizing them, and converting them
into a graph representation for pathfinding and AI purposes.

Classes:
    - MazePart: Enum representing different parts of the maze (e.g., walls, spaces) with associated
      traversal costs.
    - MazeManager: Manages maze levels, including loading level data,
      creating visual representations, and providing access to the maze map.
    - MazeNode: Represents a node in the maze graph, typically at corners or intersections, with 
      connections to neighboring nodes.

Key Functions:
    - graphify_maze: Converts a 2D tilemap into a graph (list) of MazeNode objects,
      representing the maze structure.
    - coordinize_graph: Converts a list of MazeNode objects into
      a dictionary keyed by their coordinates.

Example:
    ```python
    maze_manager = MazeManager("level1.txt")
    maze_map = maze_manager.maze_map()
    maze_graph = graphify_maze(maze_map)
    maze_dict = coordinize_graph(maze_graph)
    ```
"""
import sys
import os
from enum import Enum
from typing import Self
from dataclasses import dataclass, field

import pygame as pg
# pylint: disable=no-name-in-module
from pygame.locals import QUIT
# pylint: enable=no-name-in-module
import numpy as np

from .constant import BASE_PATH, TILE_SIZE

LEVELS_PATH = os.path.join(BASE_PATH, "assets", "levels")
WALL_CHAR = "="
SPACE_CHAR = "."

WALL_COLOR = (64, 64, 64)  # Dark gray
SPACE_COLOR = (192, 192, 192)  # Gray

class MazePart(Enum):
    """Enum for maze parts. Its value represents the cost to move through the part."""
    # Arbitrary high cost for walls, enough for `np.uint16`.
    # This value should be the minimum value that represents an in-traversable cost.
    WALL = 10000
    SPACE = 1

    @classmethod
    def from_char(cls, char: str) -> Self:
        """Convert a character to a MazePart."""
        if char == WALL_CHAR:
            return cls.WALL
        if char == SPACE_CHAR:
            return cls.SPACE
        raise ValueError(f"Invalid character for maze part: {char}")

# Represent a cost of a tile that high enough to be considered as in-traversable
VERY_HIGH_COST = MazePart.WALL.value

class MazeManager:
    """Class to manage the maze levels."""
    def __init__(self, level_file_name: str):
        """Initialize the MazeManager with a level file name."""
        level_file_path = os.path.join(LEVELS_PATH, level_file_name)

        # Generate the level data from the file
        self.level_data = []
        with open(level_file_path, "r", encoding="utf-8") as level_file:
            for line in level_file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                current_row = [MazePart.from_char(char).value for char in line]
                self.level_data.append(current_row)
        self.level_data = np.array(self.level_data, dtype=np.uint16)

        # Generate the images for the maze parts
        wall_image = pg.Surface((TILE_SIZE, TILE_SIZE)).convert()
        wall_image.fill(WALL_COLOR)
        space_image = pg.Surface((TILE_SIZE, TILE_SIZE)).convert()
        space_image.fill(SPACE_COLOR)
        self.part_images = {
            MazePart.WALL: wall_image,
            MazePart.SPACE: space_image
        }

    def maze_map(self) -> np.ndarray[np.uint16]:
        """Get the maze map as a numpy array."""
        return self.level_data

    def make_maze(self) -> pg.Surface:
        """Create a maze surface from the level data."""
        maze_surface = pg.Surface(
            (self.level_data.shape[1] * TILE_SIZE, self.level_data.shape[0] * TILE_SIZE)
        ).convert()
        for y, row in enumerate(self.level_data):
            for x, part in enumerate(row):
                maze_surface.blit(self.part_images[MazePart(part)], (x * TILE_SIZE, y * TILE_SIZE))
        return maze_surface

@dataclass
class MazeNode:
    """Represent a corner or intersection in the maze."""
    pos: tuple[int, int]
    neighbors: dict[str, tuple[Self, int] | None] = field(default_factory=lambda: {
        "up": None,
        "down": None,
        "left": None,
        "right": None
    })

    @property
    def x(self) -> int:
        """Get the x position (column number)."""
        return self.pos[0]

    @property
    def y(self) -> int:
        """Get the y position (row number)."""
        return self.pos[1]

    def __repr__(self) -> str:
        """Get the string representation of the node."""
        return f"N({int(self.pos[0]):2}, {int(self.pos[1]):2})"

    def directed_repr(self) -> str:
        """Get the string representation of the node with directions."""
        def _format_neighbor(neighbor: tuple[Self, int] | None, icon: str) -> str:
            """Format the neighbor for printing."""
            if neighbor is None:
                return ""
            node, cost = neighbor
            direction_colors = {
                "↑": "\033[94m",  # Blue for up
                "↓": "\033[93m",  # Yellow for down
                "←": "\033[96m",  # Cyan for left
                "→": "\033[95m"   # Magenta for right
            }
            # Default to green if icon not found
            color_start = direction_colors.get(icon, "\033[92m")
            color_end = "\033[0m"  # Reset color
            return f",  {color_start}{icon}( {node}" +\
              f", cost={int(cost):2} ){color_end}"
        return f"MazeNode( pos({self.pos[0]:2}, {self.pos[1]:2})" +\
               _format_neighbor(self.neighbors["up"], "↑") +\
               _format_neighbor(self.neighbors["down"], "↓") +\
               _format_neighbor(self.neighbors["left"], "←") +\
               _format_neighbor(self.neighbors["right"], "→") + ")"

        # return f"MazeNode(( pos: ({self.pos[0]}, {self.pos[1]})" +\
        #   (f", up: {self.neighbors['up']}" if self.neighbors["up"] else "") +\
        #   (f", down: {self.neighbors['down']}" if self.neighbors["down"] else "") +\
        #   (f", left: {self.neighbors['left']}" if self.neighbors["left"] else "") +\
        #   (f", right: {self.neighbors['right']}" if self.neighbors["right"] else "") + " )"

def graphify_maze(
        tilemap: np.ndarray[np.uint16],
        high_cost_threshold: int = VERY_HIGH_COST // 2,
        tracing: bool = False
        ) -> list[MazeNode]:
    """Convert a 2D tilemap into a graph of nodes.
    Each node represents a corner or intersection in the maze.
    """
    if tilemap.ndim != 2:
        raise ValueError("The function only supports 2D array")
    # if tilemap.shape[0] == 0 or tilemap.shape[1] == 0:
    #     raise ValueError("The function only supports non-empty array")

    maze_nodes: list[MazeNode] = [] # List of all nodes in the maze
    horizontal_nodes = { y: [] for y in range(tilemap.shape[0]) } # { row_index: node_in_each_col }
    vertical_nodes = { x: [] for x in range(tilemap.shape[1]) } # { col_index: node_in_each_row }

    horizontal_weight = [VERY_HIGH_COST]  # Use a list to hold the weight as a reference
    # Weight of the path above the node
    vertical_weights = { j: VERY_HIGH_COST for j in range(tilemap.shape[1]) }

    # Note: In numpy's 2d array,
    # the first index is the row index (y) and the second index is the column index (x)
    for y in range(tilemap.shape[0]): # y is the row index
        for x in range(tilemap.shape[1]): # x is the column index
            # Iterate through the tilemap from left to right, then top to bottom
            _process_tile(
                tilemap,
                x, y,
                high_cost_threshold,
                horizontal_nodes,
                vertical_nodes,
                maze_nodes,
                horizontal_weight,
                vertical_weights
            )

    if tracing:
        def _nodes_info(nodes: list[tuple[int, MazeNode]]) -> None:
            """Print the nodes in a formatted way."""
            result = []
            for weight, node in nodes:
                result.append(f"({(
                    int(weight) if int(weight) < high_cost_threshold else "--"
                    ):2}, {node})")
            return ", ".join(result)
        print("----Horizontal Nodes-------")
        for x, nodes in horizontal_nodes.items():
            print(f"Row {x}: {_nodes_info(nodes)}")
        print("----Vertical Nodes-------")
        for y, nodes in vertical_nodes.items():
            print(f"Col {y}: {_nodes_info(nodes)}")

    # Connect the nodes
    _connect_nodes(horizontal_nodes, vertical_nodes, high_cost_threshold)

    if tracing:
        print("----Maze Nodes-------")
        for node in maze_nodes:
            print(node.directed_repr())
    return maze_nodes

def coordinize_graph(maze_nodes: list[MazeNode]) -> dict[tuple[int, int], MazeNode]:
    """
    Convert a list of MazeNodes into a dictionary with coordinates as keys,
    sorted by x then y.
    """
    maze_dict = {}
    for node in sorted(maze_nodes, key=lambda n: (n.x, n.y)):
        maze_dict[node.pos] = node
    return maze_dict

# pylint: disable=too-many-arguments, too-many-positional-arguments
def _process_tile(
# pylint: enable=too-many-arguments, too-many-positional-arguments
        tilemap: np.ndarray[np.uint16],
        x: int, y: int,
        high_cost_threshold: int,
        horizontal_nodes: dict[int, list[tuple[int, MazeNode]]],
        vertical_nodes: dict[int, list[tuple[int, MazeNode]]],
        maze_nodes: list[MazeNode],
        horizontal_weight: list[int],
        vertical_weights: list[int],
        ) -> None:
    """
    Process a single tile in the tilemap to determine its role in the maze structure.

    This function evaluates a tile in the maze and determines whether it should be 
    treated as a wall, a straight path, or a node in the maze graph. It updates the 
    weights and connections for horizontal and vertical paths and creates new maze 
    nodes when necessary.

    Args:
        tilemap (numpy.ndarray): A 2D array representing the maze, where each value 
            indicates the cost of traversing the tile.
        x (int): The x-coordinate (column number) of the tile being processed.
        y (int): The y-coordinate (row number) of the tile being processed.
        high_cost_threshold (int): The cost threshold above which a tile is considered 
            a wall and not traversable.
        horizontal_nodes (dict[int, list[tuple[int, MazeNode]]]): A dictionary mapping 
            row indices to lists of tuples, where each tuple contains the weight of a 
            horizontal edge and the connected MazeNode. The edge should be to the right 
            of the node, if it exists.
        vertical_nodes (dict[int, list[tuple[int, MazeNode]]]): A dictionary mapping 
            column indices to lists of tuples, where each tuple contains the weight of 
            a vertical edge and the connected MazeNode. The edge should be above the 
            node, if it exists.
        maze_nodes (list[MazeNode]): A list to store all MazeNode objects created during 
            processing so far.
        horizontal_weight (list[int]): A single-element list holding the cumulative weight 
            of the current horizontal path being processed.
        vertical_weights (list[int]): A list of cumulative weights for vertical paths, 
            indexed by column.

    Returns:
        None: The function modifies the provided data structures in place.
    """
    # The tilemap has a high cost enough to be considered as in-traversable
    # (e.g. a wall)
    if tilemap[y, x] >= high_cost_threshold:
        horizontal_weight[0] = VERY_HIGH_COST
        vertical_weights[x] = VERY_HIGH_COST
        return  # Skip walls

    # Those booleans are used to check if there are any directly adjacent tiles
    # that is considered traversable (i.e. not a wall)
    left = x > 0 and tilemap[y, x - 1] < high_cost_threshold
    right = x < tilemap.shape[1] - 1 and tilemap[y, x + 1] < high_cost_threshold
    up = y > 0 and tilemap[y - 1, x] < high_cost_threshold
    down = y < tilemap.shape[0] - 1 and tilemap[y + 1, x] < high_cost_threshold

    # Skip "isolated" nodes
    if all((not up, not down, not left, not right)):
        return

    # Skip "straight" nodes
    if all((left, right, not up, not down)): # Horizontal straight path
        horizontal_weight[0] += tilemap[y, x]
        return
    if all((up, down, not left, not right)): # Vertical straight path
        vertical_weights[x] += tilemap[y, x]
        return

    new_node = MazeNode((x, y))
    if left or right:
        horizontal_nodes[y].append((horizontal_weight[0], new_node))
        horizontal_weight[0] = tilemap[y, x]
    if up or down:
        vertical_nodes[x].append((vertical_weights[x], new_node))
        vertical_weights[x] = tilemap[y, x]
    maze_nodes.append(new_node)

def _connect_nodes(
        horizontal_nodes: dict[int, list[tuple[int, MazeNode]]],
        vertical_nodes: dict[int, list[tuple[int, MazeNode]]],
        high_cost_threshold: int = VERY_HIGH_COST // 2
        ):
    """
    Connects nodes in a maze both horizontally and vertically based on path weights.

    This function establishes bidirectional connections between nodes in a maze
    by linking them horizontally and vertically. Connections are only created
    if the path weight between two nodes is below a specified high-cost threshold.

    Args:
        horizontal_nodes (dict): A dictionary where keys are y-coordinates (row number) and values
            are lists of tuples. Each tuple contains the path weight (to the left of the node)
            and the node at that position along the horizontal axis.
        vertical_nodes (dict): A dictionary where keys are x-coordinates (column number) and values
            are lists of tuples. Each tuple contains the path weight (above the node) and the node
            at that position along the vertical axis.
        high_cost_threshold (int): The maximum allowable path weight for two nodes
            to be considered traversible.

    Notes:
        - Each node is expected to have a `neighbors` attribute, which is a dictionary
          mapping directions ("right", "left", "down", "up") to tuples containing
          the neighboring node and the path weight.
        - Connections are bidirectional, meaning if node A is connected to node B,
          then node B is also connected to node A.
    """
    for _, nodes in horizontal_nodes.items():
        for i in range(len(nodes) - 1):
            _, left_node = nodes[i]
            horizontal_path_weight, right_node = nodes[i + 1]
            if horizontal_path_weight < high_cost_threshold:
                left_node.neighbors["right"] = (right_node, horizontal_path_weight)
                right_node.neighbors["left"] = (left_node, horizontal_path_weight)
    for _, nodes in vertical_nodes.items():
        for i in range(len(nodes) - 1):
            _, upper_node = nodes[i]
            vertical_path_weight, lower_node = nodes[i + 1]
            if vertical_path_weight < high_cost_threshold:
                upper_node.neighbors["down"] = (lower_node, vertical_path_weight)
                lower_node.neighbors["up"] = (upper_node, vertical_path_weight)

def is_coord_in_path(
        maze_map: np.ndarray[np.uint16],
        maze_dict: dict[tuple[int, int], MazeNode],
        coord: tuple[int, int]
        ) -> bool:
    """
    Determines if a given coordinate is part of a path in the maze.

    A coordinate is considered part of a path if it is **not a node** and traversable
    (i.e., not a wall).
            
    Check if a coordinate falls within a path in the maze, including straight lines.

    Args:
        maze_map (np.ndarray[np.uint16]): A 2D numpy array representing the maze,
            where each cell contains a cost value.
        maze_dict (dict[tuple[int, int], MazeNode]): A dictionary mapping coordinates
            (x, y) to MazeNode objects, representing nodes in the maze.
        coord (tuple[int, int]): The coordinate to check, represented as a tuple (x, y).

    Returns:
        bool: True if the coordinate is part of a path, False otherwise.
    """
    if (maze_map[coord[1], coord[0]] < VERY_HIGH_COST and
        maze_dict.get(coord) is None):
        return True
    return False

LEVEL = 1
if __name__ == "__main__":
    # pylint: disable=no-member
    pg.init()
    # pylint: enable=no-member
    pg.display.set_mode((800, 600))
    pg.display.set_caption("Maze Manager Test")

    maze_manager = MazeManager(f"level{LEVEL}.txt")
    print(maze_manager.maze_map())
    maze_graph = graphify_maze(maze_manager.level_data, tracing=True)

    _maze_dict = coordinize_graph(maze_graph)
    print("---Maze Dictionary---")
    for _y in range(maze_manager.level_data.shape[0]):
        for _x in range(maze_manager.level_data.shape[1]):
            def _coord(_x: int, _y: int) -> str:
                """Print the coordinates with color coding based on node connections."""
                if (_x, _y) in _maze_dict:
                    # Yellow for nodes
                    return f"\033[93m({_x:2},{_y:2})\033[0m"
                if is_coord_in_path(maze_manager.level_data, _maze_dict, (_x, _y)):
                    # Green for paths
                    return f"\033[92m({_x:2},{_y:2})\033[0m"
                # Default for non-nodes
                return "(--,--)"
            print(_coord(_x, _y), end="")
        print()

    maze = maze_manager.make_maze()
    screen = pg.display.get_surface()

    # Center the maze on the screen
    screen.blit(maze, (
        screen.get_rect().midtop[0] - maze.get_rect().width / 2,
        screen.get_rect().midleft[1] - maze.get_rect().height / 2
        ))

    while True:
        for event in pg.event.get():
            if event.type == QUIT:
                sys.exit()

        pg.display.flip()
