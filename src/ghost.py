"""
Ghost class for the ghost character in Pygame.
Inherits from GameObject.
"""
import os
import pygame

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
    def __init__(self, ghost_type: str | int, initial_position: tuple[int, int], speed: int):
        if isinstance(ghost_type, int):
            ghost_type = list(GHOST_TYPES)[ghost_type % len(GHOST_TYPES)]
        if ghost_type not in GHOST_TYPES:
            raise ValueError(f"Invalid ghost type: {ghost_type}. Must be one of {GHOST_TYPES}.")

        image = pygame.image.load(ghost_sprite_paths[ghost_type]).convert()
        super().__init__(image, initial_position, speed)
        self.ghost_type = ghost_type
