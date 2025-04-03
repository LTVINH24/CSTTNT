"""
This module defines the Maze class, which represents a maze structure."""
from dataclasses import dataclass, field

import numpy as np
import pygame as pg

from src.constant import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
from .maze_coord import MazeCoord
from .maze_node import MazeNode
from .maze_parts import MazePart

@dataclass
class MazeLayout:
    """
    Class representing a maze.

    This class encapsulates the structure of a maze, including its parts, weights,
    graph representation, and points of interest.

    Attributes:
        maze_parts (np.ndarray[MazePart]): 
            A 2D array where each element is a `MazePart` enum representing the type 
            of tile at that position in the maze (e.g., walls, spaces, spawn points).
        maze_weight (np.ndarray[np.uint16]): 
            A 2D array where each cell represents the cost of traversing that part 
            of the maze. Higher values indicate less traversable areas (e.g., walls).
        maze_graph (list[MazeNode]): 
            A list of `MazeNode` objects representing the graph structure of the maze.
            Each node corresponds to a significant point in the maze (e.g., intersections, 
            corners, or dead ends) and is connected to its neighbors with edges that 
            have weights representing the cost of traversal.
        maze_dict (dict[MazeCoord, MazeNode]): 
            A dictionary mapping `MazeCoord` objects (or tuples representing coordinates) 
            to their corresponding `MazeNode` objects. This allows for quick lookup of 
            nodes based on their positions in the maze.
        points_of_interest (dict[MazePart, list[MazeCoord]]): 
            A dictionary where keys are `MazePart` enums (e.g., spawn points) and values 
            are lists of `MazeCoord` objects representing the locations of those parts 
            in the maze. This is useful for identifying specific areas of interest 
            (e.g., spawn points for ghosts or Pac-Man).
    """
    maze_parts: np.ndarray[MazePart]
    maze_weight: np.ndarray[np.uint16]
    points_of_interest: dict[MazePart, list[MazeCoord]]

    # Only available after "building" the maze
    maze_graph: list[MazeNode] = field(default_factory=list)
    maze_dict: dict[MazeCoord, MazeNode] = field(default_factory=dict)

    def surface_sizes(self, tile_size = TILE_SIZE) -> tuple[int, int]:
        """
        Get the size of the maze surface that would return by `draw_surface`.

        Returns:
            tuple[int, int]: The width and height of the maze surface in pixels.
        """
        return (self.maze_parts.shape[1] * tile_size, self.maze_parts.shape[0] * tile_size)

    def draw_surface(
            self,
            *,
            screen: pg.Surface = None,
            center_to_offset: tuple[int, int] = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
            tile_size = TILE_SIZE,
            ) -> pg.Surface:
        """
        Create a maze surface from the level data.

        **Requires Pygame to be initialized.**
        
        Generate a Pygame surface representing the maze based on the level data.
        This method creates a Pygame surface object with dimensions proportional 
        to the maze grid and tile size. It iterates through the maze grid, 
        retrieves the corresponding image for each maze part, and blits (draws) 
        it onto the surface at the appropriate position.
        Returns:
            pg.Surface: A Pygame surface object containing the visual representation 
            of the maze, where each tile corresponds to a part of the maze grid.
        """
        maze_size = self.surface_sizes(tile_size=tile_size)

        surface_dict = MazePart.get_surface_dict()
        for key in surface_dict:
            surface_dict[key] = surface_dict[key].convert()

        if screen:
            # If a screen is provided, blit the maze onto it
            maze_center = np.array((maze_size[0] // 2, maze_size[1] // 2))
            coordinate_delta = np.array(center_to_offset) - np.array(maze_center)

            for y, row in enumerate(self.maze_parts):
                for x, part in enumerate(row):
                    screen.blit(
                        surface_dict[part],
                        np.array((x * tile_size, y * tile_size)) + coordinate_delta
                        )
            return screen

        # If no screen is provided, create a new surface
        maze_surface = pg.Surface(maze_size).convert()
        for y, row in enumerate(self.maze_parts):
            for x, part in enumerate(row):
                maze_surface.blit(
                    surface_dict[part],
                    (x * tile_size, y * tile_size)
                    )
        return maze_surface
