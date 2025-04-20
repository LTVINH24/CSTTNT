"""
This module implements the "Blue Ghost" level with the ghost Inky
using the Breadth-First Search (BFS) algorithm.

Inky (the blue ghost) is programmed to chase Pac-Man
using the BFS algorithm, providing predictable behavior
based on the shortest path in terms of steps.

Constants:
    MIN_GHOST_SPAWN_DISTANCE (int):
        The minimum distance the ghost(s) can be spawned from Pac-Man's position.
    TILE_SIZE (int): The size of a tile in the map.
    NUMBER_OF_GHOSTS (int): The number of ghosts to spawn in the level.
    INITIAL_SPEED_MULTIPLIER (int): The initial speed multiplier for the ghosts.
    BASE_SPEED (int): The base speed of ghosts in pixels per second.
    SCREEN_SIZES (tuple[int, int]): The screen size for the maze layout.
    LEVEL (int): The level number, used to load the corresponding maze layout file.

Notes:
- This module uses the Breadth-First Search (BFS) algorithm to find paths,
  enabling Inky to chase Pac-Man.
- The maze layout is loaded using the `set_up_level` function,
  which expects a corresponding level file
  (e.g., "level_1.txt") in the "assets/levels" directory.
- The `path_dispatcher` is initialized with the BFS pathfinding algorithm
  (`breadth_first_search_path_finder`).
"""
import sys
import random
from collections.abc import Iterable, Generator

import pygame as pg
# pylint: disable=no-name-in-module
from pygame.locals import QUIT
# pylint: enable=no-name-in-module

from src.maze import (
    MazeCoord,
    MazeLevel, set_up_level, render_maze_level
)
from src.pathfinding import PathDispatcher, breadth_first_search_path_finder, Pathfinder
from src.constant import TILE_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH
from src.ghost import Ghost
from src.player import Player
from src.ui.game_over import show_game_over_screen

MIN_GHOST_SPAWN_DISTANCE = 5 * TILE_SIZE
# the minimum distance the ghost(s) can be spawned from Pac-Man's position
NUMBER_OF_GHOSTS = 1 # number of ghosts spawned in the level applying this algorithm
INITIAL_SPEED_MULTIPLIER = 4  # initial speed multiplier for the ghosts
BASE_SPEED = TILE_SIZE * INITIAL_SPEED_MULTIPLIER  # base speed in pixels per second

SCREEN_SIZES = (SCREEN_WIDTH, SCREEN_HEIGHT)
LEVEL = 1

def check_collision(ghost, pacman):
    """
    Check for collision between the ghost and Pac-Man.
    Return True if there is a collision, False otherwise.
    """
    # using Pygame's built-in function
    return pg.sprite.collide_rect(ghost, pacman)

def calculate_distance(first_position, second_position):
    """
    Calculate the Euclidean distance between Pac-Man and Inky to ensure no overlapping spawns.
    """
    return (
        (first_position[0] - second_position[0])**2 + \
          (first_position[1] - second_position[1])**2
        )**0.5

def run_level():
    """
    Run the maze level with ghosts.
    """
    # pygame setup
    # pylint: disable=no-member
    pg.init()
    # pylint: enable=no-member
    screen_sizes = SCREEN_SIZES
    screen = pg.display.set_mode(screen_sizes)
    pg.display.set_caption(f"Level {LEVEL}")
    clock = pg.time.Clock()
    pacman = None
    pacman_group = None
    inky = None  # change the ghost variable corresponding to the level, e.g. (inky, BFS)
    path_dispatcher = None

    def initialize_level():
        nonlocal pacman, pacman_group, inky, path_dispatcher

        # maze level setup
        maze_level: MazeLevel = set_up_level(
            screen = screen,
            level = LEVEL,
        )

        # pacman setup with random spawn point
        pacman_spawn = random.choice(maze_level.spawn_points)
        pacman_position = pacman_spawn.rect.topleft

        pacman = Player(
            initial_position = pacman_position,
            speed = BASE_SPEED,
        )

        pacman_group = pg.sprite.GroupSingle(pacman)

        path_dispatcher = PathDispatcher(
            maze_layout = maze_level.maze_layout,
            player = pacman,
        )

        inky = set_up_inky(
            ghost_group = maze_level.ghosts,
            spawn_points = maze_level.spawn_points,
            path_finder = breadth_first_search_path_finder,
            path_dispatcher = path_dispatcher,
            pacman_spawn = pacman_spawn
        )

        return maze_level

    maze_level = initialize_level()

    while True:
        for event in pg.event.get():
            if event.type == QUIT:
                sys.exit()

        delta_time = clock.tick(60) # in ms

        if inky and check_collision(inky, pacman):
            print("Game Over! Inky đã bắt được Pac-Man!")
            pg.time.wait(5)
            screen.fill((0, 0, 0))
            render_maze_level(maze_level=maze_level, screen=screen, dt=0)
            pacman_group.draw(screen)
            choice = show_game_over_screen(screen)
            if choice =="replay":
                maze_level = initialize_level()
                continue
            if choice == "exit":
                sys.exit()

        # Refresh the screen
        screen.fill((0, 0, 0))

        # Render the maze level and update the ghosts
        render_maze_level(
            maze_level = maze_level,
            screen = screen,
            dt = delta_time,
        )
        # Render the pacman
        pacman_group.draw(screen)
        # Update the path dispatcher
        path_dispatcher.update(dt = delta_time)

        # Update the screen
        pg.display.flip()

def set_up_inky(
        ghost_group: pg.sprite.Group,
        spawn_points: list[MazeCoord],
        path_finder: Pathfinder,
        path_dispatcher: PathDispatcher = None,
        pacman_spawn: MazeCoord = None,
    ) -> None:
    """
    Set up the ghosts in the maze level.
    """
    valid_spawn_points = []

    if pacman_spawn:
        pacman_center = pacman_spawn.rect.center

        # Filter valid ghost spawn points:
        #   - Exclude the same point as Pacman's spawn point.
        #   - Ensure the point is at least MIN_GHOST_SPAWN_DISTANCE away from Pacman.
        for point in spawn_points:
            if point != pacman_spawn:
                distance = calculate_distance(point.rect.center, pacman_center)
                if distance >= MIN_GHOST_SPAWN_DISTANCE:
                    valid_spawn_points.append(point)

    # If there are no valid points, choose from all points (except Pac-Man's points).
    if not valid_spawn_points:
        valid_spawn_points = [point for point in spawn_points if point != pacman_spawn]
        print("Cảnh báo: Không tìm thấy điểm spawn đủ xa cho Inky!")

    # If there are still no points, use all points to spawn.
    if not valid_spawn_points:
        valid_spawn_points = spawn_points
        print("Cảnh báo: Buộc phải dùng tất cả các điểm spawn!")

    # Randomly select spawn point for Inky.
    spawn_point = random.choice(valid_spawn_points)

    # Create a blue ghost (Inky).
    # Always using ghost_type = "inky" for blue ghosts.
    inky = Ghost(
        initial_position = spawn_point,
        speed = BASE_SPEED,
        ghost_type = "inky",  # Decide the ghost type is Inky (blue ghost).
        ghost_group = ghost_group,
        path_dispatcher = path_dispatcher,
        path_finder=path_finder,
    )

    # Print blue ghost's information.
    print(f"Inky (ma xanh) được sinh ra tại vị trí: {spawn_point.rect.center}.")

    if pacman_spawn:
        distance = calculate_distance(spawn_point.rect.center, pacman_spawn.rect.center)
        print(f"Khoảng cách giữa Pac-Man và Inky là: {distance/TILE_SIZE:.2f} ô.")
    return inky

def random_picker[T](items: Iterable[T], seed = None) -> Generator[T, None, None]:
    """Generator to pick random items from a list."""
    generator = random.Random(seed)
    managing_items = list(items)
    while True:
        generator.shuffle(managing_items)
        yield from managing_items

if __name__ == "__main__":
    run_level()
