"""
Maze Builder Module.

This module provides classes and functions to process and build maze levels for a Pacman-like game.
It includes functionality for loading maze levels, visualizing them, and converting them
into a graph representation for pathfinding and AI purposes.

Classes:
    MazeBuilder: Manages maze levels, including loading level data,
        creating visual representations, and providing access to the maze map.

Example:
    ```python
    maze_builder = MazeBuilder("level1.txt")
    maze_grid = maze_builder.maze_grid
    maze_graph = maze_builder.maze_graph
    maze_dict = maze_builder.maze_dict
    ```
"""
import sys
import os

import pygame as pg
# pylint: disable=no-name-in-module
from pygame.locals import QUIT
# pylint: enable=no-name-in-module
import numpy as np

from src.constant import BASE_PATH, TILE_SIZE
from .maze_coord import MazeCoord
from .maze_node import MazeNode, MazeDirection
from .maze_parts import MazePart

LEVELS_PATH = os.path.join(BASE_PATH, "assets", "levels")

WALL_COLOR = (64, 64, 64)  # Dark gray
SPACE_COLOR = (192, 192, 192)  # Gray

# Represent a cost of a tile that high enough to be considered as in-traversable
VERY_HIGH_COST = MazePart.WALL.value

class MazeBuilder:
    """
    Class to load and process the maze levels.

    This class handles loading maze levels from files, creating visual representations
    of the maze, and converting the maze into graph structures for pathfinding.

    Attributes:
        maze_grid (np.ndarray[np.uint16]): A 2D numpy array representing the maze grid.
        maze_graph (list[MazeNode]): A list of MazeNode objects representing the maze graph.
        maze_dict (dict[MazeCoord, MazeNode]): A dictionary mapping coordinates to MazeNode objects.

    Methods:
        maze_surface() -> pg.Surface:
            Creates a Pygame surface representing the maze for rendering.
    """
    def __init__(self, level_file_name: str):
        """
        Initialize the MazeBuilder with a level specified in a file.

        Args:
            level_file_name (str): The name of the level file to load.
        """
        level_file_path = os.path.join(LEVELS_PATH, level_file_name)

        # Generate the level data from the file
        _level_data = []
        with open(level_file_path, "r", encoding="utf-8") as level_file:
            for line in level_file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                current_row = [MazePart.from_char(char).value for char in line]
                _level_data.append(current_row)
        _level_data = np.array(_level_data, dtype=np.uint16)
        self._maze_grid = _level_data

        # Generate the images for the maze parts
        wall_image = pg.Surface((TILE_SIZE, TILE_SIZE)).convert()
        wall_image.fill(WALL_COLOR)
        space_image = pg.Surface((TILE_SIZE, TILE_SIZE)).convert()
        space_image.fill(SPACE_COLOR)
        self.part_images = {
            MazePart.WALL: wall_image,
            MazePart.SPACE: space_image
        }

        self._maze_graph: list[MazeNode] = graphify_maze(_level_data)
        self._maze_dict: dict[MazeCoord, MazeNode] = coordinize_graph(self._maze_graph)

    @property
    def maze_grid(self) -> np.ndarray[np.uint16]:
        """
        Get the maze map as a numpy array.

        Returns:
            np.ndarray[np.uint16]: A 2D numpy array where each cell represents
            the cost of traversing that part of the maze.
        """
        return self._maze_grid

    @property
    def maze_graph(self) -> list[MazeNode]:
        """
        Get the maze graph as a list of MazeNode.

        The maze graph is a representation of the maze as a graph structure,
        where each node corresponds to a significant point in the maze
        (e.g., intersections, corners, or dead ends). Each node is connected
        to its neighbors with edges that have weights representing the cost
        of traversing between them.

        Returns:
            list[MazeNode]: A list of MazeNode objects representing the graph
            structure of the maze.
        """
        return self._maze_graph

    @property
    def maze_dict(self) -> dict[MazeCoord, MazeNode]:
        """
        Get the maze graph as a dictionary of MazeNode.

        The maze dictionary maps coordinates (MazeCoord) to their corresponding
        MazeNode objects. This allows for quick lookup of nodes based on their
        positions in the maze.

        Returns:
            dict[MazeCoord, MazeNode]: A dictionary where keys are MazeCoord objects
            (or tuples representing coordinates) and values are MazeNode objects.
        """
        return self._maze_dict

    def maze_surface(self) -> pg.Surface:
        """
        Create a maze surface from the level data.
        
        Generate a Pygame surface representing the maze based on the level data.
        This method creates a Pygame surface object with dimensions proportional 
        to the maze grid and tile size. It iterates through the maze grid, 
        retrieves the corresponding image for each maze part, and blits (draws) 
        it onto the surface at the appropriate position.
        Returns:
            pg.Surface: A Pygame surface object containing the visual representation 
            of the maze, where each tile corresponds to a part of the maze grid.
        """
        maze_surface = pg.Surface(
            (self._maze_grid.shape[1] * TILE_SIZE, self._maze_grid.shape[0] * TILE_SIZE)
        ).convert()
        for y, row in enumerate(self._maze_grid):
            for x, part in enumerate(row):
                maze_surface.blit(self.part_images[MazePart(part)], (x * TILE_SIZE, y * TILE_SIZE))
        return maze_surface

def is_coord_in_path(
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

LEVEL = 1
if __name__ == "__main__":
    # pylint: disable=no-member
    pg.init()
    # pylint: enable=no-member
    pg.display.set_mode((800, 600))
    pg.display.set_caption("Maze Builder Test")

    maze_builder = MazeBuilder(f"level{LEVEL}.txt")
    print(maze_builder.maze_grid)
    maze_graph = graphify_maze(maze_builder.maze_grid, tracing=True)

    _maze_dict = coordinize_graph(maze_graph)
    print("---Maze Dictionary---")
    for _y in range(maze_builder.maze_grid.shape[0]):
        for _x in range(maze_builder.maze_grid.shape[1]):
            def _coord(_x: int, _y: int) -> str:
                """Print the coordinates with color coding based on node connections."""
                if (_x, _y) in _maze_dict:
                    # Yellow for nodes
                    return f"\033[93m({_x:2},{_y:2})\033[0m"
                if is_coord_in_path(maze_builder.maze_grid, _maze_dict, (_x, _y)):
                    # Green for paths
                    return f"\033[92m({_x:2},{_y:2})\033[0m"
                # Default for non-nodes
                return "(--,--)"
            print(_coord(_x, _y), end="")
        print()

    maze = maze_builder.maze_surface()
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
