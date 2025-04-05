"""
Ghost class for the ghost character in Pygame.
Inherits from GameObject.
"""
import os
import random
import pygame as pg

from src.maze import MazeNode, MazeCoord, move_along_path, is_snap_within
from src.pathfinding import PathListener, PathDispatcher
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

class Ghost(pg.sprite.Sprite, PathListener):
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
            path_dispatcher: PathDispatcher = None,
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
        self.path: list[MazeNode] = [ initial_node ]
        self.path_dispatcher = path_dispatcher

        # Cumulative delta time for movement update
        self.cumulative_delta_time = 0 # in milliseconds

    def halt_current_and_request_new_path(self):
        if len(self.path) == 0:
            # TODO: Infer the path from the initial position.
            pass
        elif is_snap_within(self.rect.center, self.path[0]):
            self.path = self.path[0] # Keep the first node in the path
        else:
            self.path = self.path[:2] # Keep the first two nodes in the path
        self.path_dispatcher.receive_request_for(
            self,
            tuple(self.path),
            )

    def update(self, dt: int) -> None:
        """
        Update the ghost's position based on its speed and direction.

        Time delta is in milliseconds. Speed is pixels per second.
        """
        if self.new_path:
            self.path = self.new_path
            self.new_path = []
        if not self.path or len(self.path) == 0:
            # TODO: Infer the path from the initial position.
            return
        if len(self.path) <= 1:
            if self.waiting_for_path:
                return
            self.path_dispatcher.receive_request_for(
                self,
                tuple(self.path),
                )
            return
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
