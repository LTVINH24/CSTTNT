"""
This module defines the `MazeNode` and `MazeDirection` classes, which are used to represent
nodes and directions in a maze. These classes provide functionality for navigating and
describing the structure of a maze.

Classes:
    MazeDirection (Enum):
        An enumeration representing the four possible directions in a maze:
        UP, DOWN, LEFT, and RIGHT.
        Provides utility methods for string and vector representations of directions.
    MazeNode (dataclass):
        Represents a node in a maze, which can be a corner, dead-end, or intersection.
        Each node has a position in the maze and a set of neighbors representing possible
        directions to move from this node.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Self

from .maze_coord import MazeCoord

class MazeDirection(Enum):
    """
    MazeDirection is an enumeration that represents the four possible directions
    in a maze: UP, DOWN, LEFT, and RIGHT.

    Each direction is associated with a string value and provides utility methods
    for string representation (and vector representation).

    Attributes:
        UP (str): Represents the upward direction in the maze.
        DOWN (str): Represents the downward direction in the maze.
        LEFT (str): Represents the leftward direction in the maze.
        RIGHT (str): Represents the rightward direction in the maze.
    Methods:
        __str__() -> str:
            Returns the string representation of the direction.
    """
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    def __str__(self) -> str:
        """Get the string representation of the direction."""
        return self.value

    def direction_vector(self) -> tuple[int, int]:
        """Get the vector representation of the direction."""
        match self:
            case MazeDirection.UP:
                return (0, -1)
            case MazeDirection.DOWN:
                return (0, 1)
            case MazeDirection.LEFT:
                return (-1, 0)
            case MazeDirection.RIGHT:
                return (1, 0)
            # Default case, should not happen
            case _:
                return (0, 0)

@dataclass()
class MazeNode:
    """
    Represents a node in a maze, which can be a corner, an dead-end, or an intersection.

    Each node has **a position in the maze** and a set of neighbors that represent
    the possible directions to move from this node.

    Attributes:
        pos (MazeCoord): The position of the node in the maze, represented as a coordinate (x, y).
                         Defaults to (0, 0) if not specified.
        neighbors (dict[MazeDirection, tuple[Self, int]]):
            A dictionary mapping the four possible directions (UP, DOWN, LEFT, RIGHT)
            to a tuple containing the neighboring node and the cost to move to that neighbor.

            If there is no neighbor in a direction, that direction is omitted from the dictionary.
    Properties:
        x (int): The x-coordinate (column number) of the node's position.
        y (int): The y-coordinate (row number) of the node's position.
    Methods:
        __repr__() -> str:
            Returns a concise string representation of the node
            in the format "N(x, y)" where x and y are the coordinates of the node.
        directed_repr() -> str:
            Returns a detailed string representation of the node, including its position and its
            neighbors in each direction. The neighbors are displayed with their direction
            (e.g., ↑, ↓, ←, →), their position, and the cost to move to them.
            The output uses ANSI escape codes to colorize the directions for better visualization:
                - Blue (↑) for UP
                - Yellow (↓) for DOWN
                - Cyan (←) for LEFT
                - Magenta (→) for RIGHT
                - Green for any unspecified direction
            If a neighbor is not present in a direction, that direction is omitted from the output.
    """
    pos: MazeCoord = field(default_factory=lambda: MazeCoord(0, 0))
    neighbors: dict[MazeDirection, tuple[Self, int]] = field(default_factory=dict)

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
        def _format_neighbor(direction: MazeDirection, icon: str) -> str:
            """Format the neighbor for printing."""
            if direction not in self.neighbors:
                return ""
            node, cost = self.neighbors[direction]
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
               _format_neighbor(MazeDirection.UP, "↑") +\
               _format_neighbor(MazeDirection.DOWN, "↓") +\
               _format_neighbor(MazeDirection.LEFT, "←") +\
               _format_neighbor(MazeDirection.RIGHT, "→") + ")"

    def __copy__(self) -> Self:
        """Create a copy of the MazeNode."""
        return MazeNode(MazeCoord.__copy__(self.pos), self.neighbors.copy())

    def __eq__(self, other:Self) -> bool:
        if isinstance(other,MazeNode):
            return self.pos ==other.pos
        return False

    def __hash__(self) -> int:
        return hash(self.pos)
