"""
Maze parts module.

This module defines the parts of the maze in the text file and their properties.

Classes:
    MazePart: Enum representing different parts of the maze (e.g., walls, spaces) with associated
        traversal costs.
"""
from enum import Enum
from typing import Self

WALL_CHAR = "="
SPACE_CHAR = "."

class MazePart(Enum):
    """Enum for maze parts. Its value represents the cost to move through that part."""
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
