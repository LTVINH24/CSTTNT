"""
This module serves as a template for setting up and running a level in a Pacman-like game.

It provides the necessary setup for the maze, player (Pacman), ghosts, and pathfinding logic. 
The module is designed to be used as a reference for creating new levels.

Constants:
    MIN_GHOST_SPAWN_DISTANCE: The minimum distance the ghost(s) can be spawned from Pac-Man's position.
    TILE_SIZE: Size of a tile in the map.
    NUMBER_OF_GHOSTS (int): The number of ghosts to spawn in the level.
    INITIAL_SPEED_MULTIPLIER (int): The initial speed multiplier for the ghosts.
    BASE_SPEED (int): The base speed of ghosts in pixels per second.
    ARBITARY_SCREEN_SIZES (tuple[int, int]): The screen size for the maze layout.
    LEVEL (int): The level number, used to load the corresponding maze layout file.

Notes:
- The `path_dispatcher` is initialized with a placeholder pathfinding algorithm 
  (`random_walk_path_finder`). Replace it with your own pathfinding algorithm for better gameplay.
- The maze layout is loaded using the `set_up_level` function, which expects a corresponding 
  level file (e.g., "level_1.txt") in the "assets/levels" directory.    
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
from src.pathfinding import PathDispatcher, breadth_first_search_path_finder
from src.constant import TILE_SIZE
from src.ghost import Ghost, GHOST_TYPES
from src.player import Player

MIN_GHOST_SPAWN_DISTANCE = 5 * TILE_SIZE # the minimum distance the ghost(s) can be spawned from Pac-Man's position
NUMBER_OF_GHOSTS = 1 # number of ghosts spawned in the level applying this algorithm 
INITIAL_SPEED_MULTIPLIER = 4  # initial speed multiplier for the ghosts
BASE_SPEED = TILE_SIZE * INITIAL_SPEED_MULTIPLIER  # base speed in pixels per second

ARBITARY_SCREEN_SIZES = (800, 600)  # arbitrary screen sizes for the maze layout
LEVEL = 1 # create your own "level_.txt" file in "assets/levels" directory

def check_collision(ghost, pacman):
    """
    Check for collision between the ghost and Pac-Man. Return True if there is a collision, False otherwise.
    """
    # using Pygame's built-in function
    return pg.sprite.collide_rect(ghost, pacman)
 
def calculate_distance(first_position, second_position):
    """
    Calculate the Euclidean distance between Pac-Man and Inky to ensure no overlapping spawns.
    """
    return ((first_position[0] - second_position[0])**2 + (first_position[1] - second_position[1])**2)**0.5

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
        pathfinder = breadth_first_search_path_finder,
    )

    inky = set_up_inky(
        ghost_group = maze_level.ghosts,
        spawn_points = maze_level.spawn_points,
        path_dispatcher = path_dispatcher,
        pacman_spawn = pacman_spawn
    )

    while True:
        for event in pg.event.get():
            if event.type == QUIT:
                sys.exit()

        delta_time = clock.tick(60) # in ms

        if inky and check_collision(inky, pacman):
            print("Game Over! Inky đã bắt được Pac-Man!")
            pg.time.wait(1000)  # waiting for 1 second
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
        ghost_type = "inky",  # Decide ghost type is Inky (blue ghost).
        ghost_group = ghost_group,
        path_dispatcher = path_dispatcher,
    )

    # # Optional ghost number limit by the number of spawn points
    # maximum_ghost = min(len(spawn_points), NUMBER_OF_GHOSTS)

    # # Feel free to uncomment the below line if you want to spawn more ghosts than spawn points
    # # maximum_ghost = NUMBER_OF_GHOSTS
    # for i in range(maximum_ghost):
    #     spawn_point = spawn_points[i % len(spawn_points)]
    #     ghost_type = next(ghost_type_picker)

    #     # if ghost_type == "blue":
    #     #     pathfinder = breadth_first_search_path_finder

    #     _ = Ghost(
    #         initial_position = spawn_point,
    #         speed = BASE_SPEED,
    #         ghost_type = ghost_type,
    #         ghost_group = ghost_group,
    #         path_dispatcher = path_dispatcher,
    #     )

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
