"""
Ghost class for the ghost character in Pygame.
Inherits from GameObject.
"""
import os
import random
from typing import Callable
import pygame as pg

from src.maze import MazeNode, MazeCoord, move_along_path
from .constant import IMAGES_PATH

GHOST_TYPES = { "blinky", "clyde", "inky", "pinky"}

GHOST_SPRITES_BASE_PATH = os.path.join(IMAGES_PATH, "ghosts")
ghost_sprite_paths = {
    "blinky": os.path.join(GHOST_SPRITES_BASE_PATH, "blinky.png"),
    "clyde": os.path.join(GHOST_SPRITES_BASE_PATH, "clyde.png"),
    "inky": os.path.join(GHOST_SPRITES_BASE_PATH, "inky.png"),
    "pinky": os.path.join(GHOST_SPRITES_BASE_PATH, "pinky.png"),
}

THOUSAND = 1000
ONE_PIXEL = 1
DEFAULT_PATH_LENGTH = 5

def empty_path_provider(_: MazeNode, __: int) -> list[MazeNode]:
    """
    Empty path provider function that returns an empty path.
    """
    return []

class Ghost(pg.sprite.Sprite):
    """
    Ghost class for the ghost character in Pygame.
    Inherits from GameObject.
    """

    # TODO: Remove the `initial_node` parameter and use `initial_position` instead.
    def __init__(
            self,
            initial_position: MazeCoord,
            speed: int,
            *,
            ghost_type: str | int = None,
            ghost_group: pg.sprite.Group = None,
            initial_node: MazeNode = MazeNode(),
            path_provider: Callable[[MazeNode, int], list[MazeNode]] = empty_path_provider,
            ):
        if ghost_group is None:
            pg.sprite.Sprite.__init__(self)
        else:
            # Add the ghost to the provided group
            pg.sprite.Sprite.__init__(self, ghost_group)

        # Deal with ghost type
        if ghost_type is None:
            ghost_type = random.choice(list(GHOST_TYPES))
        elif isinstance(ghost_type, int):
            ghost_type = list(GHOST_TYPES)[ghost_type % len(GHOST_TYPES)]
        elif ghost_type not in GHOST_TYPES:
            raise ValueError(f"Invalid ghost type: {ghost_type}. Must be one of {GHOST_TYPES}.")
        self.image = pg.image.load(ghost_sprite_paths[ghost_type]).convert()
        self.ghost_type = ghost_type

        # TODO: Fix the initial position (corresponding to MazeCoord)
        _initial_position = initial_position.rect.topleft
        _initial_position = initial_node.pos.rect.topleft # Don't doubt about topleft
        self.rect = self.image.get_rect().move(_initial_position)
        self.speed = speed # in pixels per second

        # Path related attributes

        # TODO: Infer the path from the initial position, not using the initial node.
        self.path: list[MazeNode] = []
        self.last_standing_node: MazeNode = initial_node
        self.path_provider = path_provider

        # Cumulative delta time for movement update
        self.cumulative_delta_time = 0 # in milliseconds

    def update(self, dt: int) -> None:
        """
        Update the ghost's position based on its speed and direction.

        Time delta is in milliseconds. Speed is pixels per second.
        """
        if self.path and len(self.path) == 1:
            self.last_standing_node = self.path[0]
            self.path = []
        if not self.path or len(self.path) == 0:
            self.path = self.path_provider(self.last_standing_node, DEFAULT_PATH_LENGTH)
        if self.path:
            _moving_distance: int
            if dt * self.speed // THOUSAND >= ONE_PIXEL:
                _moving_distance = dt * self.speed // THOUSAND
                # Cumulate the remainder part of the distance
                self.cumulative_delta_time += dt - _moving_distance * THOUSAND // self.speed
                if self.cumulative_delta_time * self.speed // THOUSAND >= ONE_PIXEL:
                    _moving_distance += self.cumulative_delta_time * self.speed // THOUSAND
                    self.cumulative_delta_time = 0
            else:
                # Less-than-1-pixel-per-second fix
                self.cumulative_delta_time += dt
                if self.cumulative_delta_time * self.speed // THOUSAND < ONE_PIXEL:
                    return
                _moving_distance = self.cumulative_delta_time * self.speed // THOUSAND
                self.cumulative_delta_time = 0

            new_path, new_center = move_along_path(
                self.rect.center,
                self.path,
                max(_moving_distance, 1)
                )
            self.path = new_path
            self.rect.center = new_center
