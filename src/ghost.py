"""
Ghost class for the ghost character in Pygame.
Inherits from GameObject.
"""
import os
from typing import Callable
from math import ceil
import pygame

from src.maze import MazeNode, MazeCoord, move_along_path
from .constant import IMAGES_PATH
from .game_object import GameObject

GHOST_TYPES = { "blinky", "clyde", "inky", "pinky"}

GHOST_SPRITES_BASE_PATH = os.path.join(IMAGES_PATH, "ghosts")
ghost_sprite_paths = {
    "blinky": os.path.join(GHOST_SPRITES_BASE_PATH, "blinky.png"),
    "clyde": os.path.join(GHOST_SPRITES_BASE_PATH, "clyde.png"),
    "inky": os.path.join(GHOST_SPRITES_BASE_PATH, "inky.png"),
    "pinky": os.path.join(GHOST_SPRITES_BASE_PATH, "pinky.png"),
}

class Ghost(GameObject):
    """
    Ghost class for the ghost character in Pygame.
    Inherits from GameObject.
    """

    # TODO: Remove the `initial_node` parameter and use `initial_position` instead.
    def __init__(
            self,
            ghost_type: str | int,
            initial_position: MazeCoord,
            speed: int,
            initial_node: MazeNode = MazeNode(),
            path_provider: Callable[[MazeNode, int], list[tuple[MazeNode, MazeNode]]] = None,
            ):
        if isinstance(ghost_type, int):
            ghost_type = list(GHOST_TYPES)[ghost_type % len(GHOST_TYPES)]
        if ghost_type not in GHOST_TYPES:
            raise ValueError(f"Invalid ghost type: {ghost_type}. Must be one of {GHOST_TYPES}.")

        image = pygame.image.load(ghost_sprite_paths[ghost_type]).convert()

        # TODO: Fix the initial position (corresponding to MazeCoord)
        _initial_position = initial_node.pos.rect.topleft
        super().__init__(image, _initial_position, speed)
        self.ghost_type = ghost_type

        self.path: list[tuple[MazeNode, MazeNode]] = []
        self.last_standing_node: MazeNode = initial_node
        self.path_provider = path_provider

        self.cumulative_delta_time = 0

    # TODO: Using integer delta time for better precision
    def update(self, dt: float) -> None:
        """
        Update the ghost's position based on its speed and direction.
        """
        if not self.path:
            if self.path_provider is not None:
                self.path = self.path_provider(self.last_standing_node)
        if self.path:
            # TODO: Naive calculation
            self.last_standing_node = self.path[-1][1]

            _moving_distance: int
            if dt * self.speed >= 1:
                _moving_distance = ceil(dt * self.speed)
                # Cumulate the fractional part of the distance
                self.cumulative_delta_time += dt - _moving_distance * self.speed
                if self.cumulative_delta_time * self.speed >= 1:
                    _moving_distance += ceil(self.cumulative_delta_time * self.speed)
                    self.cumulative_delta_time = 0
            else:
                # Less-than-1-pixel-per-second fix
                self.cumulative_delta_time += dt
                if self.cumulative_delta_time * self.speed < 1:
                    return
                _moving_distance = ceil(self.cumulative_delta_time * self.speed)
                self.cumulative_delta_time = 0

            new_path, new_center = move_along_path(
                self.position.center,
                self.path,
                max(_moving_distance, 2)
                )
            self.path = new_path
            self.position.center = new_center
