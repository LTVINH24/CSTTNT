"""
This module defines the `MazeCoord` class, which represents a coordinate in a maze
and provides utility methods for interacting with it.

Classes:
    MazeCoord: Represents a coordinate in the maze with tuple-like behavior and
        additional properties like `rect` and `center`.
"""

from dataclasses import dataclass
from typing import ClassVar
from collections.abc import Sequence

import pygame as pg

from src.constant import TILE_SIZE

@dataclass
class MazeCoord(Sequence[int]):
    """
    Represents a coordinate in the maze, acts like `tuple[int, int]`.

    Attributes:
        x (int): The x-coordinate.
        y (int): The y-coordinate.

    Class Variables:
        tile_size (int): The size of a tile in the maze.
        maze_offset (tuple[int, int]):
            The offset for the maze coordinates.
            To be exactly, the coordinates of the top-left corner of the maze in pixel.
            The offset is used to convert the maze coordinates to pixel coordinates.

    Properties:
        rect (pg.Rect): A pygame Rect object representing the tile area.
        center (tuple[int, int]): The center coordinates (x, y) (in pixel) of the rectangle.

    Methods:
        __iter__(): Unpack the MazeCoord as a tuple (x, y).
        __getitem__(index): Index the MazeCoord like a tuple.
        __len__(): Return the length of the tuple representation (always 2).
        __eq__(other): Compare MazeCoord with another tuple or MazeCoord.
        __repr__(): Return a string representation of the MazeCoord.
        __hash__(): Return the hash of the MazeCoord.
        __copy__(): Return a copy of the MazeCoord from the current instance.
    """

    x: int
    y: int
    tile_size: ClassVar[int] = TILE_SIZE
    maze_offset: ClassVar[tuple[int, int]] = (0, 0)  # Offset for the maze

    def __init__(self, x: int = 0, y: int = 0) -> None:
        """
        Initializes a MazeCoord instance.

        Args:
            x (int, optional): The x-coordinate (column number). Defaults to 0.
            y (int, optional): The y-coordinate (row number). Defaults to 0.
        """
        self.x = int(x)  # Ensure x is an integer (e.g., if it's np.uint16)
        self.y = int(y)
        self._rect = pg.Rect(
            self.x * MazeCoord.tile_size + MazeCoord.maze_offset[0],
            self.y * MazeCoord.tile_size + MazeCoord.maze_offset[1],
            MazeCoord.tile_size, MazeCoord.tile_size
        )

    @property
    def rect(self) -> pg.Rect:
        """
        Get the rect of the tile area denoted by the current coordinate.

        Returns:
            pg.Rect: A pygame Rect object representing the tile.
        """
        return pg.Rect(self._rect)

    @property
    def center(self) -> tuple[int, int]:
        """
        Get the center coordinates in pixel of the tile area denoted by the current coordinate.

        Returns:
            (tuple[int, int]): The center coordinates (x, y).
        """
        return self._rect.center

    def __iter__(self):
        """
        Allow unpacking the MazeCoord as a tuple (x, y).

        Returns:
            Iterator[int]: An iterator over the x and y coordinates.
        """
        return iter((self.x, self.y))

    def __getitem__(self, index):
        """
        Allow indexing like a tuple.

        Args:
            index (int): The index to access (0 for x, 1 for y).

        Returns:
            int: The x or y coordinate.
        """
        return (self.x, self.y)[index]

    def __len__(self):
        """
        Return the length of the tuple representation (always 2).

        Returns:
            int: The length of the tuple (always 2).
        """
        return 2

    def __eq__(self, other):
        """
        Compare MazeCoord with another tuple or MazeCoord.

        Args:
            other (MazeCoord or tuple): The object to compare with.

        Returns:
            bool: True if the coordinates are equal, False otherwise.
        """
        if isinstance(other, MazeCoord):
            return (self.x, self.y) == (other.x, other.y)
        if isinstance(other, tuple):
            return (self.x, self.y) == other
        return False

    def __repr__(self):
        """
        Return a string representation of the MazeCoord.

        Returns:
            str: A string representation of the MazeCoord.
        """
        return f"({self.x:2}, {self.y:2})"

    def __hash__(self):
        return hash((self[0], self[1]))

    def __copy__(self):
        return MazeCoord(self[0], self[1])
