"""Constants for the game."""
import os

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

TILE_SIZE = 16

## Deal with the annoying path conflict (Windows vs Linux)
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMAGES_PATH = os.path.join(BASE_PATH, "assets", "images")
