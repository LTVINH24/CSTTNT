"""MazeMaster class to manage a maze level."""
import random
from collections.abc import Iterable, Generator
from time import time_ns
import sys

import pygame as pg
# pylint: disable=no-name-in-module
from pygame.locals import QUIT
# pylint: enable=no-name-in-module

from src.constant import TILE_SIZE
from src.ghost import Ghost, GHOST_TYPES
from src.game_object import draw_objects_on_screen
from .maze_node import MazeNode
from .maze_builder import load_maze, build_maze
from .maze_parts import MazePart

def random_picker[T](items: Iterable[T], seed=None) -> Generator[T, None, None]:
    """Generator to pick random items from a list."""
    generator = random.Random(seed)
    managing_items = list(items)
    while True:
        generator.shuffle(managing_items)
        yield from managing_items

NUMBER_OF_GHOSTS = 10
INITIAL_SPEED_MULTIPLIER = 1  # initial speed multiplier for the ghosts
INTENSITY_COOLDOWN_TIME = 2  # seconds
INTENSITY_RATE = 1.25  # increase speed by {value} times every INTENSITY_COOLDOWN_TIME seconds
MAX_SPEED_MULTIPLIER = 10  # maximum speed multiplier for the ghosts

ARBITARY_SCREEN_SIZES = (600, 400)  # arbitrary screen sizes for the maze layout

class MazeMaster:
    """MazeMaster class to manage a maze level."""
    def __init__(self, screen: pg.Surface, level: int = 1):
        self.screen = screen
        self.maze_layout = build_maze(
            maze_layout=load_maze(f"level{level}.txt"),
            screen_sizes=ARBITARY_SCREEN_SIZES
            )
        self.maze_graph = self.maze_layout.maze_graph
        self.spawn_points = self.maze_layout.points_of_interest[MazePart.SPAWN_POINT]

        spawn_point_picker = random_picker(
            self.spawn_points,
            seed=f"spawn_point{time_ns().numerator % 69}"
            )
        ghost_type_picker = random_picker(
            list(GHOST_TYPES),
            seed=f"ghost_type{time_ns().numerator % 420}"
            )
        # TODO: temporary node provider
        node_picker = random_picker(self.maze_graph, seed=f"node{time_ns().numerator % 777}")

        # TODO: using event system of some kind
        def path_provider(
                starting_node: MazeNode,
                path_length: int = 5
                ) -> list[tuple[MazeNode, MazeNode]]:
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

        self.cumulative_delta_time = 0
        self.intensity = INITIAL_SPEED_MULTIPLIER
        self.maze_ghosts = [
            Ghost(
                next(ghost_type_picker),
                next(spawn_point_picker),
                int(TILE_SIZE * self.intensity),
                initial_node=MazeNode.__copy__(next(node_picker)),
                path_provider=path_provider,
                ) for _ in range(NUMBER_OF_GHOSTS)
            ]

    def update(self, dt: float) -> None:
        """Update the maze level."""
        self.cumulative_delta_time += dt
        # Increase the intensity every X seconds
        if self.cumulative_delta_time >= INTENSITY_COOLDOWN_TIME:
            self.intensity *= INTENSITY_RATE if self.intensity <= MAX_SPEED_MULTIPLIER else 1
            for ghost in self.maze_ghosts:
                ghost.speed = int(TILE_SIZE * self.intensity)
            self.cumulative_delta_time = 0
        for ghost in self.maze_ghosts:
            ghost.update(dt)
        draw_objects_on_screen(
            self.screen,
            *self.maze_ghosts
            )

LEVEL = 1
if __name__ == "__main__":
    # pylint: disable=no-member
    pg.init()
    # pylint: enable=no-member
    screen_sizes = ARBITARY_SCREEN_SIZES
    pg.display.set_mode(screen_sizes)
    pg.display.set_caption("Maze Master Test")

    main_screen = pg.display.get_surface()
    clock = pg.time.Clock()
    maze_master = MazeMaster(main_screen, level=LEVEL)

    while True:
        for event in pg.event.get():
            if event.type == QUIT:
                sys.exit()

        delta_time = clock.tick(60) / 1000.0  # Convert milliseconds to seconds

        # Draw the maze layout
        maze_master.maze_layout.draw_surface(
            screen=main_screen,
            center_to_offset=main_screen.get_rect().center
            )
        # Draw the ghosts within the maze
        maze_master.update(delta_time)
        pg.display.flip()
