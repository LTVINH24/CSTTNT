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
from copy import copy
from time import time_ns

import pygame as pg
# pylint: disable=no-name-in-module
from pygame.locals import QUIT
# pylint: enable=no-name-in-module

from src.maze import (
    MazeNode, MazeCoord,
    MazeLevel, set_up_level, render_maze_level
)
from src.pathfinding import PathDispatcher, build_path_dispatcher, random_walk_path_finder
from src.constant import TILE_SIZE
from src.ghost import Ghost, GHOST_TYPES
from src.player import Player

NUMBER_OF_GHOSTS = 4
INITIAL_SPEED_MULTIPLIER = 20  # initial speed multiplier for the ghosts
BASE_SPEED = TILE_SIZE * INITIAL_SPEED_MULTIPLIER  # base speed in pixels per second

ARBITARY_SCREEN_SIZES = (800, 600)  # arbitrary screen sizes for the maze layout
LEVEL = 1 # create your own "level_.txt" file in "assets/levels" directory

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
    pg.display.set_caption(f"Level {LEVEL}")
    clock = pg.time.Clock()

    # maze level setup
    maze_level: MazeLevel = set_up_level(
        screen=screen,
        level=LEVEL,
    )

    # pacman setup with random spawn point
    pacman_position = random.choice(maze_level.spawn_points).rect.center
    pacman = Player(
        initial_position= (
            pacman_position[0] + MazeCoord.maze_offset[0],
            pacman_position[1] + MazeCoord.maze_offset[1],
        ),
        speed=BASE_SPEED,
    )
    pacman_group = pg.sprite.GroupSingle(pacman)

    path_dispatcher = build_path_dispatcher(
        maze_layout=maze_level.maze_layout,
        player=pacman,
        pathfinder=random_walk_path_finder, # TODO: replace with your own pathfinding algorithm
    )

    set_up_ghosts(
        ghost_group=maze_level.ghosts,
        spawn_points=maze_level.spawn_points,
        spawn_nodes=maze_level.maze_layout.maze_graph,
        path_dispatcher=path_dispatcher,
    )

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
        # Render the pacman
        pacman_group.draw(screen)
        # Update the path dispatcher
        path_dispatcher.update(dt=delta_time)

        # Update the screen
        pg.display.flip()

def set_up_ghosts(
        ghost_group: pg.sprite.Group,
        spawn_points: list[MazeCoord],
        spawn_nodes: list[MazeNode],
        path_dispatcher: PathDispatcher = None,
    ) -> None:
    """
    Set up the ghosts in the maze level.
    """
    spawn_node_picker = random_picker(
        spawn_nodes,
        seed=int(time_ns() % 2**32) # Random seed based on time
    )
    ghost_type_picker = random_picker(
        list(GHOST_TYPES),
        seed=int(time_ns() % 2**32) # Random seed based on time
    )
    for i in range(NUMBER_OF_GHOSTS):
        spawn_point = spawn_points[i % len(spawn_points)]
        spawn_node = next(spawn_node_picker)
        ghost_type = next(ghost_type_picker)
        _ = Ghost(
            initial_position=spawn_point,
            speed=BASE_SPEED,
            ghost_type=ghost_type,
            ghost_group=ghost_group,
            initial_node=copy(spawn_node),
            path_dispatcher=path_dispatcher,
        )

def random_picker[T](items: Iterable[T], seed=None) -> Generator[T, None, None]:
    """Generator to pick random items from a list."""
    generator = random.Random(seed)
    managing_items = list(items)
    while True:
        generator.shuffle(managing_items)
        yield from managing_items

if __name__ == "__main__":
    run_level()
