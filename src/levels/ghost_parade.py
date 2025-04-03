
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
from src.constant import TILE_SIZE
from src.ghost import Ghost, GHOST_TYPES

NUMBER_OF_GHOSTS = 10
INITIAL_SPEED_MULTIPLIER = 1  # initial speed multiplier for the ghosts
BASE_SPEED = TILE_SIZE * INITIAL_SPEED_MULTIPLIER  # base speed in pixels per second
INTENSITY_RATE = 1.25  # increase speed by {value} times every INTENSITY_COOLDOWN_TIME seconds
INTENSITY_COOLDOWN_TIME = 2  # seconds
MAX_SPEED_MULTIPLIER = 10  # maximum speed multiplier for the ghosts

ARBITARY_SCREEN_SIZES = (600, 400)  # arbitrary screen sizes for the maze layout
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

    set_up_ghosts(
        ghost_group=maze_level.ghosts,
        spawn_points=maze_level.spawn_points,
        spawn_nodes=maze_level.maze_layout.maze_graph
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

        # Update the screen
        pg.display.flip()

def set_up_ghosts(
        ghost_group: pg.sprite.Group,
        spawn_points: list[MazeCoord],
        spawn_nodes: list[MazeNode],
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
            path_provider=path_provider,
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

def path_provider(
        starting_node: MazeNode,
        path_length: int = 5
        ) -> list[tuple[MazeNode, MazeNode]]:
    """
    Generate a random path of nodes in the maze.

    Args:
        starting_node (MazeNode): The starting node for the path.
        path_length (int):
            The length of the path.
            Default is 5.

    Returns:
        list[tuple[MazeNode, MazeNode]]:
            A list of tuples containing the starting and ending nodes of the path.
            Each tuple is of the form (starting_node, ending_node).
    """
    path = []
    _current_node = starting_node
    for _ in range(path_length):
        next_node: MazeNode = random.choice(
            list(
                filter(None, _current_node.neighbors.values())
                )
        )[0] # Only take the node part, not along with the weight part
        path.append((_current_node, next_node))
        _current_node = next_node
    return path

def random_picker[T](items: Iterable[T], seed=None) -> Generator[T, None, None]:
    """Generator to pick random items from a list."""
    generator = random.Random(seed)
    managing_items = list(items)
    while True:
        generator.shuffle(managing_items)
        yield from managing_items

if __name__ == "__main__":
    run_level()
