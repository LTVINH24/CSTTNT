"""Player class for the player character in Pygame."""
import os
import pygame
# pylint: disable=no-name-in-module
from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT
# pylint: enable=no-name-in-module

from .constant import IMAGES_PATH
from .game_object import GameObject

PLAYER_SPRITE_PATH = os.path.join(IMAGES_PATH, "pacman-right", "1.png")

class Player(GameObject):
    """
    Player class for the player character in Pygame.
    Inherits from GameObject.
    """

    def __init__(self, initial_position: tuple[int, int], speed: int):
        image = pygame.image.load(PLAYER_SPRITE_PATH).convert()
        super().__init__(image, initial_position, speed)
        self.score = 0  # Initialize score attribute

    def update_score(self, points: int):
        """
        Update the player's score by adding points.
        """
        self.score += points

    def move_by_arrow_keys(self, keys: any):
        """
        Move the player based on arrow key presses.
        """
        if keys[K_UP]:
            self.move(up=True)
        if keys[K_DOWN]:
            self.move(down=True)
        if keys[K_LEFT]:
            self.move(left=True)
        if keys[K_RIGHT]:
            self.move(right=True)
