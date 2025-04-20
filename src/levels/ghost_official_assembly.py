"""
This module sets up and runs a level in a Pacman-like game.

It initializes the maze, player (Pacman), ghosts, and pathfinding logic. 
The module is designed to be reusable for creating and running different levels.

Constants:
    NUMBER_OF_GHOSTS (int): The number of ghosts to spawn in the level.
    INITIAL_SPEED_MULTIPLIER (int): The initial speed multiplier for the ghosts.
    BASE_SPEED (int): The base speed of ghosts in pixels per second.
    SCREEN_SIZE (tuple[int, int]): The screen size for the game window.
    LEVEL (int): The level number, used to load the corresponding maze layout.

Key Features:
- The `path_dispatcher` dynamically assigns pathfinding algorithms to ghosts based on their type.
- The maze layout is loaded using the `set_up_level` function, which initializes the maze, player, 
  and ghost spawn points.
- Ghosts are assigned specific pathfinding strategies, such as BFS, DFS, UCS, or A*.

Notes:
- The `enable_movement_by_mouse` flag allows Pacman to be moved using mouse clicks for testing.
- The maze layout and level-specific configurations are expected to be defined
in the "assets/levels" directory.
"""
import sys
import random
from collections.abc import Iterable, Generator
from time import time_ns

import pygame as pg
# pylint: disable=no-name-in-module
from pygame.locals import QUIT, MOUSEBUTTONDOWN
# pylint: enable=no-name-in-module
import numpy as np

from src.maze import (
    MazeCoord, MazePart,
    MazeLevel, set_up_level, render_maze_level
)
# pylint: disable=unused-import
from src.pathfinding import (
  PathDispatcher,
  breadth_first_search_path_finder,
  depth_first_search_path_finder,
  ucs_pathfinder,
  a_star_pathfinder
)
# pylint: enable=unused-import
from src.constant import TILE_SIZE
from src.ghost import Ghost, GHOST_TYPES
from src.player import Player

NUMBER_OF_GHOSTS = 1
INITIAL_SPEED_MULTIPLIER = 8  # initial speed multiplier for the ghosts
BASE_SPEED = TILE_SIZE * INITIAL_SPEED_MULTIPLIER  # base speed in pixels per second
SCREEN_SIZE = (800, 600)
LEVEL = 6

PATH_FINDER_BY_GHOST = {
    "inky": breadth_first_search_path_finder,
    "clyde": ucs_pathfinder,
    "pinky": depth_first_search_path_finder,
    "blinky": a_star_pathfinder,
}

def run_level(enable_movement_by_mouse: bool = False) -> None:
    """
    Run the maze level with ghosts.
    """
    # pygame setup
    # pylint: disable=no-member
    pg.init()
    # pylint: enable=no-member
    screen_sizes = SCREEN_SIZE
    screen = pg.display.set_mode(screen_sizes)
    pg.display.set_caption("Level 6")
    clock = pg.time.Clock()

    # maze level setup
    maze_level: MazeLevel = set_up_level(
        screen=screen,
        level=LEVEL,
    )

    # pacman setup with random spawn point
    pacman_position: tuple[int, int]
    if maze_level.player_spawn_points is None or len(maze_level.player_spawn_points) == 0:
        pacman_position = random.choice(maze_level.spawn_points).rect.topleft
    else:
        pacman_position = random.choice(maze_level.player_spawn_points).rect.topleft
    pacman = Player(
        initial_position=pacman_position,
        speed=BASE_SPEED,
    )
    pacman_group = pg.sprite.GroupSingle(pacman)

    path_dispatcher = PathDispatcher(
        maze_layout=maze_level.maze_layout,
        player=pacman,
    )

    set_up_ghosts(
        ghost_group=maze_level.ghosts,
        spawn_points=maze_level.spawn_points,
        path_dispatcher=path_dispatcher,
    )

    while True:
        for event in pg.event.get():
            if event.type == QUIT:
                sys.exit()
            if event.type == MOUSEBUTTONDOWN and event.button == 1 and enable_movement_by_mouse:
                move_pacman_by_mouse(
                    pacman=pacman,
                    mouse_pos=pg.mouse.get_pos(),
                    maze_weights=maze_level.maze_layout.maze_weight,
                )

        delta_time = clock.tick(60) # in ms

        # Refresh the screen
        screen.fill((0, 0, 0))

        # Render the maze level and update the ghosts
        render_maze_level(
            maze_level=maze_level,
            screen=screen,
            dt=delta_time,
        )

        if pg.sprite.spritecollideany(pacman, maze_level.ghosts):
            # If pacman collides with any ghost, move pacman to the furthest spawn point from ghosts
            spawn_point = furthest_spawn_point_from_ghosts(
                ghost_group=maze_level.ghosts,
                spawn_points=maze_level.spawn_points,
            )
            pacman.rect.topleft = spawn_point.rect.topleft

        # Render the pacman
        pacman_group.draw(screen)
        # Update the path dispatcher
        path_dispatcher.update(dt=delta_time)

        # Update the screen
        pg.display.flip()

def furthest_spawn_point_from_ghosts(
    ghost_group: pg.sprite.Group,
    spawn_points: list[MazeCoord],
    ) -> MazeCoord:
    """
    Move the pacman to the furthest spawn point.
    """
    def distance_from_ghosts(spawn_point: MazeCoord) -> float:
        """
        Calculate the distance from the spawn point to the ghosts.
        """
        ghosts: list[Ghost] = ghost_group.sprites()
        return min(
            np.linalg.norm(
                np.array(spawn_point.rect.topleft) - np.array(ghost.rect.topleft)
            )
            for ghost in ghosts
        )
    return max(
        spawn_points,
        key=distance_from_ghosts,
    )

def move_pacman_by_mouse(
    pacman: Player,
    mouse_pos: tuple[int, int],
    maze_weights: np.ndarray[np.uint16]
    ) -> None:
    """
    Move the pacman to the mouse position.
    """
    maze_coord = MazeCoord.nearest_coord(mouse_pos)
    if maze_coord is not None and maze_weights[maze_coord.y, maze_coord.x] < MazePart.WALL.weight:
        # Move pacman to the nearest maze coordinate
        pacman.rect.topleft = maze_coord.rect.topleft

def set_up_ghosts(
    ghost_group: pg.sprite.Group,
    spawn_points: list[MazeCoord],
    path_dispatcher: PathDispatcher = None,
    ) -> None:
    """
    Set up the ghosts in the maze level.
    """
    spawn_point_picker = random_picker(
        spawn_points,
        seed=int(time_ns() % 2**32) # Random seed based on time
    )
    for ghost_type in GHOST_TYPES:
        ghost_group.add(
            Ghost(
                initial_position=next(spawn_point_picker),
                speed=BASE_SPEED,
                ghost_type=ghost_type,
                ghost_group=ghost_group,
                path_dispatcher=path_dispatcher,
                path_finder=PATH_FINDER_BY_GHOST[ghost_type],
            )
        )

def random_picker[T](items: Iterable[T], seed=None) -> Generator[T, None, None]:
    """Generator to pick random items from a list."""
    generator = random.Random(seed)
    managing_items = list(items)
    while True:
        generator.shuffle(managing_items)
        yield from managing_items

if __name__ == "__main__":
    run_level(enable_movement_by_mouse=True)
