"""
Maze parts module.

This module defines the parts of the maze in the text file and their properties.

Classes:
    MazePart: Enum representing different parts of the maze (e.g., walls, spaces) with associated
        traversal costs.
"""
from enum import Enum
from typing import Self

import pygame as pg

from src.constant import TILE_SIZE

WALL_CHAR = "="
SPACE_CHAR = "."
SPAWN_POINT_CHAR = "S"

MAZE_PART_WEIGHTS = {
    WALL_CHAR: 10000,
    SPACE_CHAR: 1,
    SPAWN_POINT_CHAR: 1
}
DEFAULT_WEIGHT = 1

WALL_COLOR = (64, 64, 64)  # Dark gray
SPACE_COLOR = (192, 192, 192)  # Gray

wall_surface = pg.Surface((TILE_SIZE, TILE_SIZE))
wall_surface.fill(WALL_COLOR)
space_surface = pg.Surface((TILE_SIZE, TILE_SIZE))
space_surface.fill(SPACE_COLOR)

class MazePart(Enum):
    """Enum for maze parts. Its value represents the cost to move through that part."""
    # Arbitrary high cost for walls, enough for `np.uint16`.
    # This value should be the minimum value that represents an in-traversable cost.
    WALL = WALL_CHAR
    SPACE = SPACE_CHAR
    SPAWN_POINT = SPAWN_POINT_CHAR

    @property
    def weight(self) -> int:
        """Return the weight of the maze part."""
        return MAZE_PART_WEIGHTS[self.value] if self.value in MAZE_PART_WEIGHTS else DEFAULT_WEIGHT

    @classmethod
    def get_surface_dict(cls) -> dict[Self, pg.Surface]:
        """Return a dictionary of surfaces for each maze part."""
        return {
            cls.WALL: wall_surface,
            cls.SPACE: space_surface,
            cls.SPAWN_POINT: space_surface,
        }

    @classmethod
    def from_char(cls, char: str) -> Self:
        """Convert a character to a MazePart."""
        if char == WALL_CHAR:
            return cls.WALL
        if char == SPACE_CHAR:
            return cls.SPACE
        if char == SPAWN_POINT_CHAR:
            return cls.SPAWN_POINT
        raise ValueError(f"Invalid character for maze part: {char}")
