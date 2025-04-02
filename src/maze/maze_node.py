"""Maze Node Module."""
from enum import Enum
from dataclasses import dataclass, field
from typing import Self

from .maze_coord import MazeCoord

class MazeDirection(Enum):
    """Enum for maze directions."""
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

@dataclass
class MazeNode:
    """
    Represents a node in a maze, which can be a corner or an intersection. Each node has a position
    and a set of neighbors that represent the possible directions to move from this node.
    Attributes:
        pos (MazeCoord): The position of the node in the maze, represented as a coordinate (x, y).
                         Defaults to (0, 0) if not specified.
        neighbors (dict[MazeDirection, tuple[Self, int] | None]):
            A dictionary mapping each possible
            direction (UP, DOWN, LEFT, RIGHT) to a tuple containing the neighboring node
            and the cost to move to that neighbor. If there is no neighbor in a direction,
            the value is None.
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
    neighbors: dict[MazeDirection, tuple[Self, int] | None] = field(default_factory=lambda: {
        MazeDirection.UP: None,
        MazeDirection.DOWN: None,
        MazeDirection.LEFT: None,
        MazeDirection.RIGHT: None
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
               _format_neighbor(self.neighbors[MazeDirection.UP], "↑") +\
               _format_neighbor(self.neighbors[MazeDirection.DOWN], "↓") +\
               _format_neighbor(self.neighbors[MazeDirection.LEFT], "←") +\
               _format_neighbor(self.neighbors[MazeDirection.RIGHT], "→") + ")"
