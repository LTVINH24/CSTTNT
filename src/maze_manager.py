"""
MazeManager class to manage the maze levels."""
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
        """Get the x position."""
        return self.pos[0]

    @property
    def y(self) -> int:
        """Get the y position."""
        return self.pos[1]

    def __repr__(self) -> str:
        """Get the string representation of the node."""
        return f"({self.pos[0]}, {self.pos[1]})"

    def directed_repr(self) -> str:
        """Get the string representation of the node with directions."""
        return f"MazeNode({self.pos[0]}, {self.pos[1]})" +\
          (f", up: {self.neighbors['up']}" if self.neighbors["up"] else "") +\
          (f", down: {self.neighbors['down']}" if self.neighbors["down"] else "") +\
          (f", left: {self.neighbors['left']}" if self.neighbors["left"] else "") +\
          (f", right: {self.neighbors['right']}" if self.neighbors["right"] else "")

VERY_HIGH_COST = MazePart.WALL.value
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

    horizontal_weight: int = VERY_HIGH_COST # Weight of the path to the left of the node
    # Weight of the path above the node
    vertical_weights = { j: VERY_HIGH_COST for j in range(tilemap.shape[1]) }

    # Note: In numpy's 2d array,
    # the first index is the row index (y) and the second index is the column index (x)
    for y in range(tilemap.shape[0]): # y is the row index
        for x in range(tilemap.shape[1]): # x is the column index
            # Iterate through the tilemap from left to right, then top to bottom
            if tilemap[y, x] >= high_cost_threshold:
                horizontal_weight = VERY_HIGH_COST
                vertical_weights[x] = VERY_HIGH_COST
                # Skip walls
                continue

            left = x > 0 and tilemap[y, x - 1] < high_cost_threshold
            right = x < tilemap.shape[1] - 1 and tilemap[y, x + 1] < high_cost_threshold
            up = y > 0 and tilemap[y - 1, x] < high_cost_threshold
            down = y < tilemap.shape[0] - 1 and tilemap[y + 1, x] < high_cost_threshold

            # Check if the node is a corner or intersection
            if all((not up, not down, not left, not right)):
                # Skip "isolated" nodes
                continue

            is_straight_horizontally = all((left, right, not up, not down))
            is_straight_vertically = all((up, down, not left, not right))
            if is_straight_horizontally:
                horizontal_weight += tilemap[y, x]
                continue # Skip "straight" nodes
            if is_straight_vertically:
                vertical_weights[x] += tilemap[y, x]
                continue # Skip "straight" nodes

            new_node = MazeNode((x, y))
            if left or right:
                horizontal_nodes[y].append((horizontal_weight, new_node))
                horizontal_weight = tilemap[y, x]
            if up or down:
                vertical_nodes[x].append((vertical_weights[x], new_node))
                vertical_weights[x] = tilemap[y, x]
            maze_nodes.append(new_node)

    if tracing:
        print("----Horizontal Nodes-------")
        for x, nodes in horizontal_nodes.items():
            print(f"Row {x}: {[node[1].directed_repr() for node in nodes]}")
        print("----Vertical Nodes-------")
        for y, nodes in vertical_nodes.items():
            print(f"Col {y}: {[node[1].directed_repr() for node in nodes]}")    

    # Connect the nodes
    for x, nodes in horizontal_nodes.items():
        for i in range(len(nodes) - 1):
            _, left_node = nodes[i]
            horizontal_path_weight, right_node = nodes[i + 1]
            if horizontal_path_weight < high_cost_threshold:
                left_node.neighbors["right"] = (right_node, horizontal_path_weight)
                right_node.neighbors["left"] = (left_node, horizontal_path_weight)
    for y, nodes in vertical_nodes.items():
        for i in range(len(nodes) - 1):
            _, upper_node = nodes[i]
            vertical_path_weight, lower_node = nodes[i + 1]
            if vertical_path_weight < high_cost_threshold:
                upper_node.neighbors["down"] = (lower_node, vertical_path_weight)
                lower_node.neighbors["up"] = (upper_node, vertical_path_weight)

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

LEVEL = 2
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
            if (_x, _y) in _maze_dict:
                print(f"{_maze_dict[(_x, _y)]}", end="")
            else:
                print("(-, -)", end="")
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
