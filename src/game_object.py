"""GameObject class for game objects in Pygame."""
from pygame import Surface
from .constant import SCREEN_WIDTH, SCREEN_HEIGHT

class GameObject:
    """
    Base class for game objects in Pygame.
    This class handles the image, position, and movement of game objects.
    """
    SPRITE_WIDTH = 16
    SPRITE_HEIGHT = 16

    def __init__(self, image: Surface, initial_position: tuple[int, int], speed: int):
        self.image = image
        self.speed = speed
        self.position = image.get_rect().move(*initial_position)

    def move(self, up: bool = False, down: bool = False, left: bool = False, right: bool = False):
        """
        Move the game object in the specified direction.
        The movement is based on the speed of the object.
        """
        if up:
            self.position.top -= self.speed
        if down:
            self.position.top += self.speed
        if left:
            self.position.left -= self.speed
        if right:
            self.position.left += self.speed
        # Boundary normalization
        self.position.top = max(0, min(self.position.top, SCREEN_HEIGHT - self.SPRITE_HEIGHT))
        self.position.left = max(0, min(self.position.left, SCREEN_WIDTH - self.SPRITE_WIDTH))

def clear_objects_on_screen(screen: Surface, background: Surface, *objects: GameObject):
    """
    Clear the objects on the screen by blitting the background.
    """
    for obj in objects:
        screen.blit(background, obj.position, obj.position)

def draw_objects_on_screen(screen: Surface, *objects: GameObject):
    """
    Draw the objects on the screen by blitting their images.
    """
    for obj in objects:
        screen.blit(obj.image, obj.position)
