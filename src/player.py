"""Player class for the player character in Pygame."""
import os
import pygame as pg
# pylint: disable=no-name-in-module
from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT
# pylint: enable=no-name-in-module

from .constant import IMAGES_PATH, SCREEN_HEIGHT, SCREEN_WIDTH

PLAYER_SPRITE_PATH = os.path.join(IMAGES_PATH, "pacman-right", "1.png")

class Player(pg.sprite.Sprite):
    """
    Player class for the player character in Pygame.
    """
    SPRITE_WIDTH = 16
    SPRITE_HEIGHT = 16

    def __init__(self, initial_position: tuple[int, int], speed: int):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.image.load(PLAYER_SPRITE_PATH).convert()
        self.rect = self.image.get_rect()

        self.rect.center = initial_position
        self.speed = speed

    def move(self, up: bool = False, down: bool = False, left: bool = False, right: bool = False):
        """
        Move the game object in the specified direction.
        The movement is based on the speed of the object.
        """
        if up:
            self.rect.top -= self.speed
        if down:
            self.rect.top += self.speed
        if left:
            self.rect.left -= self.speed
        if right:
            self.rect.left += self.speed
        # Boundary normalization
        self.rect.top = max(0, min(self.rect.top, SCREEN_HEIGHT - self.SPRITE_HEIGHT))
        self.rect.left = max(0, min(self.rect.left, SCREEN_WIDTH - self.SPRITE_WIDTH))

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
