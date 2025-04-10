"""
Maze Builder Module.

This module provides functions and utilities to process and build maze levels
for a Pacman-like game.
It includes functionality for loading maze levels, visualizing them, and converting them
into a graph representation for pathfinding and AI purposes.

Functions:
    load_maze:
        Loads a maze level from a file and processes its structure, weights,
        and points of interest.
    build_maze:
        Prepares a maze layout for rendering and initializes its graph representation.

Example:
    ```python
    maze_layout = load_maze("level1.txt")
    maze_layout = build_maze(maze_layout)
    ```
"""
import sys
import os

import pygame as pg
# pylint: disable=no-name-in-module
from pygame.locals import QUIT
# pylint: enable=no-name-in-module
import numpy as np

from src.constant import BASE_PATH, SCREEN_WIDTH, SCREEN_HEIGHT
from .maze_coord import MazeCoord
from .maze_node import MazeNode, MazeDirection
from .maze_parts import MazePart

from .maze_layout import MazeLayout

LEVELS_PATH = os.path.join(BASE_PATH, "assets", "levels")

# Represent a cost of a tile that high enough to be considered as in-traversable
VERY_HIGH_COST = MazePart.WALL.weight

def load_maze(
    level_file_name: str,
    *,
    level_file_path: str = LEVELS_PATH,
    interesting_parts: frozenset[MazePart] = frozenset((MazePart.SPAWN_POINT,))
    ) -> MazeLayout:
    """
    Load the maze from a level file.
    
    This function reads a maze level file, processes its content to extract
    the maze structure, weights, and points of interest, and returns a 
    MazeLayout object containing all the relevant information.
    Args:
        level_file_name (str): The name of the level file to read.
        level_file_path (str, optional): The path to the directory containing 
            the level file. Defaults to LEVELS_PATH.
        interesting_parts (frozenset[MazePart], optional): A set of MazePart 
            elements that are considered points of interest. Defaults to a 
            frozenset containing only MazePart.SPAWN_POINT.
    Returns:
        MazeLayout: An object containing the maze's parts, weights, graph 
        representation, coordinate mapping, and points of interest.
    Raises:
        FileNotFoundError: If the specified level file does not exist.
    Notes:
        - Lines in the level file starting with '#' or empty lines are ignored.
        - Each character in the level file corresponds to a MazePart, which 
          determines the type and weight of that part of the maze.
        - Points of interest are extracted based on the `interesting_parts` 
          parameter and stored in a dictionary.
    
    """
    # Generate the level data from the file
    _maze_weight: list[list[int]] = []
    _maze_parts: list[list[MazePart]] = []
    _interested_parts: dict[MazePart, list[MazeCoord]] = {
        part: [] for part in interesting_parts
    }
    with open(
        os.path.join(level_file_path, level_file_name),
        mode = "r",
        encoding = "utf-8"
        ) as level_file:
        for row_index, line in enumerate(level_file):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            current_weights_in_row: list[int] = []
            current_parts_in_row: list[MazePart] = []
            # Enumerate the line to get the column index and character
            for col_index, char in enumerate(line):
                maze_type = MazePart.from_char(char)
                current_parts_in_row.append(maze_type)
                current_weights_in_row.append(maze_type.weight)
                if maze_type in interesting_parts:
                    _interested_parts[maze_type].append(MazeCoord(col_index, row_index))
                else:
                    # Skip the unwanted parts
                    pass
            _maze_parts.append(current_parts_in_row)
            _maze_weight.append(current_weights_in_row)

    _maze_weight: np.ndarray[np.uint16] = np.array(_maze_weight, dtype=np.uint16)
    _maze_parts: np.ndarray[MazePart] = np.array(_maze_parts)

    return MazeLayout(
        maze_parts=_maze_parts,
        maze_weight=_maze_weight,
        points_of_interest=_interested_parts,
    )

def build_maze(
        maze_layout: MazeLayout,
        *,
        screen_sizes: tuple[int, int] = (SCREEN_WIDTH, SCREEN_HEIGHT),
        maze_offset: tuple[int, int] = None,
        ):
    """
    Build the maze graph and prepare it for rendering.

    Should be call **after** (and with) `load_maze()` to create a complete MazeLayout object.

    ```python
    maze_layout = build_maze(load_maze("level1.txt"))
    ```

    This function initializes the maze layout, sets the maze offset,
    and prepares the maze for rendering on the screen.
    Args:
        maze_layout (MazeLayout): The maze layout object to be built.
        screen_sizes (tuple[int, int], optional): The size of the screen.
            Defaults to (SCREEN_WIDTH, SCREEN_HEIGHT).
        maze_offset (tuple[int, int], optional): The offset for the maze layout.
            If not provided, it will be calculated based on the screen size
            and the maze size.
    Returns:
        MazeLayout: The built maze layout object.
    """
    if not maze_offset:
        maze_surface_sizes = maze_layout.surface_sizes()
        maze_offset = (
            screen_sizes[0] // 2 - maze_surface_sizes[0] // 2,
            screen_sizes[1] // 2 - maze_surface_sizes[1] // 2
        )
    MazeCoord.maze_offset = maze_offset

    maze_layout.maze_graph = graphify_maze(maze_layout.maze_weight)
    maze_layout.maze_dict = coordinize_graph(maze_layout.maze_graph)
    return maze_layout

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

def coordinize_graph(maze_nodes: list[MazeNode]) -> dict[MazeCoord, MazeNode]:
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

    new_node = MazeNode(MazeCoord(x, y))
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
          mapping directions (MazeDirection.RIGHT, MazeDirection.LEFT,
          MazeDirection.DOWN, MazeDirection.UP) to tuples containing
          the neighboring node and the path weight.
        - Connections are bidirectional, meaning if node A is connected to node B,
          then node B is also connected to node A.
    """
    for _, nodes in horizontal_nodes.items():
        for i in range(len(nodes) - 1):
            _, left_node = nodes[i]
            horizontal_path_weight, right_node = nodes[i + 1]
            if horizontal_path_weight < high_cost_threshold:
                left_node.neighbors[MazeDirection.RIGHT] = (right_node, horizontal_path_weight)
                right_node.neighbors[MazeDirection.LEFT] = (left_node, horizontal_path_weight)
    for _, nodes in vertical_nodes.items():
        for i in range(len(nodes) - 1):
            _, upper_node = nodes[i]
            vertical_path_weight, lower_node = nodes[i + 1]
            if vertical_path_weight < high_cost_threshold:
                upper_node.neighbors[MazeDirection.DOWN] = (lower_node, vertical_path_weight)
                lower_node.neighbors[MazeDirection.UP] = (upper_node, vertical_path_weight)

def _is_coord_in_path(
        maze_map: np.ndarray[np.uint16],
        maze_dict: dict[MazeCoord, MazeNode],
        coord: MazeCoord | tuple[int, int]
        ) -> bool:
    """
    Determines if a given coordinate is part of a path in the maze.

    A coordinate is considered part of a path if it is **not a node** and traversable
    (i.e., not a wall).

    Check if a coordinate falls within a path in the maze, including straight lines.

    Args:
        maze_map (np.ndarray[np.uint16]): A 2D numpy array representing the maze,
            where each cell contains a cost value.
        maze_dict (dict[MazeCoord, MazeNode]): A dictionary mapping coordinates
            (x, y) to MazeNode objects, representing nodes in the maze.
        coord (MazeCoord | tuple[int, int]): The coordinate to check, represented as a tuple (x, y).

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

    main_screen_sizes = (SCREEN_WIDTH, SCREEN_HEIGHT)
    pg.display.set_mode(main_screen_sizes)
    pg.display.set_caption("Maze Builder Test")

    # main_maze_layout = build_maze(load_maze(f"level{LEVEL}.txt"))
    main_maze_layout = load_maze(f"level{LEVEL}.txt")
    print(main_maze_layout.maze_weight)
    maze_graph = graphify_maze(main_maze_layout.maze_weight, tracing=True)

    _maze_dict = coordinize_graph(maze_graph)
    print("---Maze Dictionary---")
    for _y in range(main_maze_layout.maze_weight.shape[0]):
        for _x in range(main_maze_layout.maze_weight.shape[1]):
            def _coord(_x: int, _y: int) -> str:
                """Print the coordinates with color coding based on node connections."""
                if (_x, _y) in _maze_dict:
                    # Yellow for nodes
                    return f"\033[93m({_x:2},{_y:2})\033[0m"
                if _is_coord_in_path(main_maze_layout.maze_weight, _maze_dict, (_x, _y)):
                    # Green for paths
                    return f"\033[92m({_x:2},{_y:2})\033[0m"
                # Default for non-nodes
                return "(--,--)"
            print(_coord(_x, _y), end="")
        print()

    # Draw the maze layout to the screen
    screen = pg.display.get_surface()
    main_maze_layout.draw_surface(
        screen=screen
    )

    while True:
        for event in pg.event.get():
            if event.type == QUIT:
                sys.exit()

        pg.display.flip()
