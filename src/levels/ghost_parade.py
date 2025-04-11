"""
This module implements the "Ghost Parade" level for a Pacman-like game. It sets up a maze
with ghosts that increase their speed over time.

Functions:
    run_level():
        Runs the maze level with ghosts, handling game logic, rendering, and ghost speed updates.
"""
import sys
import random
from collections.abc import Iterable, Generator
from time import time_ns

import pygame as pg
# pylint: disable=no-name-in-module
from pygame.locals import QUIT
# pylint: enable=no-name-in-module

from src.maze import (
    MazeCoord,
    MazeLevel, set_up_level, render_maze_level
)
from src.pathfinding import PathDispatcher, random_walk_path_finder
from src.constant import TILE_SIZE
from src.ghost import Ghost, GHOST_TYPES
from src.player import Player

MAXIMUM_NUMBER_OF_GHOSTS = 25
INITIAL_SPEED_MULTIPLIER = 1  # initial speed multiplier for the ghosts
BASE_SPEED = TILE_SIZE * INITIAL_SPEED_MULTIPLIER  # base speed in pixels per second
INTENSITY_RATE = 1.25  # increase speed by {value} times every INTENSITY_COOLDOWN_TIME seconds
INTENSITY_COOLDOWN_TIME = 0.5  # seconds
MAX_SPEED_MULTIPLIER = 5  # maximum speed multiplier for the ghosts

ARBITARY_SCREEN_SIZES = (800, 600)  # arbitrary screen sizes for the maze layout
LEVEL = 1

def run_level():
    """
    Run the maze level with ghosts.
    """
    # pygame setup
    # pylint: disable=no-member
    pg.init()
    # pylint: enable=no-member
    screen_sizes = ARBITARY_SCREEN_SIZES
    screen = pg.display.set_mode(screen_sizes)
    pg.display.set_caption("Ghost Parade")
    clock = pg.time.Clock()

    # maze level setup
    maze_level: MazeLevel = set_up_level(
        screen=screen,
        level=LEVEL,
    )

    pacman_position = random.choice(maze_level.spawn_points).rect.topleft
    pacman = Player(
        initial_position=pacman_position,
        speed=BASE_SPEED,
    )
    pacman_group = pg.sprite.GroupSingle(pacman)

    path_dispatcher = PathDispatcher(
        maze_layout=maze_level.maze_layout,
        player=pacman,
        pathfinder=random_walk_path_finder,
    )

    set_up_ghosts(
        ghost_group=maze_level.ghosts,
        spawn_points=maze_level.spawn_points,
        path_dispatcher=path_dispatcher,
    )

    # Speed setup
    cumulative_delta_time = 0
    intensity = INITIAL_SPEED_MULTIPLIER
    while True:
        for event in pg.event.get():
            if event.type == QUIT:
                sys.exit()

        delta_time = clock.tick(60) # in ms

        # Refresh the screen
        screen.fill((0, 0, 0))

        # Render the maze level and update the ghosts
        render_maze_level(
            maze_level=maze_level,
            screen=screen,
            dt=delta_time,
        )
        cumulative_delta_time, intensity = update_ghost_speed(
            ghost_group=maze_level.ghosts,
            dt=delta_time,
            cumulative_delta_time=cumulative_delta_time,
            intensity=intensity,
        )
        pacman_group.draw(screen)
        path_dispatcher.update(dt=delta_time)

        # Update the screen
        pg.display.flip()

def set_up_ghosts(
        ghost_group: pg.sprite.Group,
        spawn_points: list[MazeCoord],
        path_dispatcher: PathDispatcher = None,
    ) -> None:
    """
    Set up the ghosts in the maze level.
    """
    ghost_type_picker = random_picker(
        list(GHOST_TYPES),
        seed=int(time_ns() % 2**32) # Random seed based on time
    )
    for i in range(min(MAXIMUM_NUMBER_OF_GHOSTS, len(spawn_points))):
        spawn_point = spawn_points[i % len(spawn_points)]
        ghost_type = next(ghost_type_picker)
        _ = Ghost(
            initial_position=spawn_point,
            speed=BASE_SPEED,
            ghost_type=ghost_type,
            ghost_group=ghost_group,
            path_dispatcher=path_dispatcher,
        )

def update_ghost_speed(
        ghost_group: pg.sprite.Group,
        dt: int, # delta time in milliseconds
        cumulative_delta_time: int = 0,
        intensity: float = INITIAL_SPEED_MULTIPLIER,
        ) -> tuple[int, float]:
    """
    Update the speed of the ghosts based on the time passed.

    Args:
        ghost_group (pg.sprite.Group): The group of ghosts to update.
        dt (int): The delta time in milliseconds.

    Returns:
        None
    """
    cumulative_delta_time += dt
    # Increase the intensity every X seconds
    if cumulative_delta_time >= INTENSITY_COOLDOWN_TIME * 1000:
        intensity *= INTENSITY_RATE if intensity * INTENSITY_RATE <= MAX_SPEED_MULTIPLIER else 1
        ghost: Ghost
        for ghost in ghost_group:
            ghost.speed = int(BASE_SPEED * intensity)
        cumulative_delta_time = 0
    return cumulative_delta_time, intensity

def random_picker[T](items: Iterable[T], seed=None) -> Generator[T, None, None]:
    """Generator to pick random items from a list."""
    generator = random.Random(seed)
    managing_items = list(items)
    while True:
        generator.shuffle(managing_items)
        yield from managing_items

if __name__ == "__main__":
    run_level()
