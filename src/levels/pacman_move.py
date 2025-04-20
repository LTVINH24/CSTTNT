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
- The maze layout and level-specific configurations are expected to be defined
in the "assets/levels" directory.
"""
import sys
import random
from collections.abc import Iterable, Generator
from time import time_ns

import pygame as pg
# pylint: disable=no-name-in-module
from pygame.locals import QUIT, K_UP, K_DOWN, K_LEFT, K_RIGHT
# pylint: enable=no-name-in-module
import numpy as np

from src.maze import (
    MazeCoord, MazePart,
    set_up_level, render_maze_level
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
from src.ui.game_over import show_game_over_screen

NUMBER_OF_GHOSTS = 1
INITIAL_SPEED_MULTIPLIER = 4  # initial speed multiplier for the ghosts
BASE_SPEED = TILE_SIZE * INITIAL_SPEED_MULTIPLIER  # base speed in pixels per second
SCREEN_SIZE = (800, 600)
LEVEL = 6
PLAYER_SPEED = 8 * TILE_SIZE

PATH_FINDER_BY_GHOST = {
    "blinky": a_star_pathfinder,
    "clyde": ucs_pathfinder,
    "inky": breadth_first_search_path_finder,
    "pinky": depth_first_search_path_finder,
}

def check_collision(ghost, pacman):
    """
    Kiểm tra va chạm giữa ma và Pacman.
    Trả về True nếu có va chạm, False nếu không.
    """
    # Sử dụng hàm va chạm có sẵn của Pygame
    return pg.sprite.collide_rect(ghost, pacman)

def calculate_distance(pos1, pos2):
    """
    Tính khoảng cách Euclidean giữa hai điểm của Pacman và Blinky để đảm bảo không spawn trùng nhau.
    """
    return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5

def run_level() -> None:
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
    pacman = None
    pacman_group = None
    path_dispatcher = None
    maze_level = None
    pacman_direction = None
    pacman_target_pos = None

    def initialize_level():
        nonlocal pacman, pacman_group, path_dispatcher, \
          maze_level, pacman_direction, pacman_target_pos

        pacman_direction = None
        pacman_target_pos = None
        # maze level setup
        maze_level = set_up_level(
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
            speed=PLAYER_SPEED,
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
        return maze_level

    maze_level = initialize_level()
    while True:
        for event in pg.event.get():
            if event.type == QUIT:
                sys.exit()
        delta_time = clock.tick(60) # in ms
        for ghost in maze_level.ghosts:
            if check_collision(ghost,pacman):
                print("Game Over! Ghost đã bắt được Pacman!")
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
        keys = pg.key.get_pressed()
        pacman_direction, pacman_target_pos = handle_pacman_movement(
            pacman=pacman,
            keys=keys,
            maze_weights=maze_level.maze_layout.maze_weight,
            current_direction=pacman_direction,
            target_pos=pacman_target_pos,
            dt=delta_time
        )
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

def handle_pacman_movement(
    pacman: Player,
    keys: any,
    maze_weights: np.ndarray[np.uint16],
    current_direction :tuple[int,int] = None,
    target_pos: tuple[int, int] = None,
    dt:float = 0
) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Handle the movement of Pacman based on keyboard input.
    """
    if current_direction is None:
        current_direction = (0, 0)
    new_direction = current_direction
    if keys[K_UP]:
        new_direction = (0, -1)
    elif keys[K_DOWN]:
        new_direction = (0, 1)
    elif keys[K_LEFT]:
        new_direction = (-1, 0)
    elif keys[K_RIGHT]:
        new_direction = (1, 0)

    speed_pixel_per_ms = pacman.speed / 1000  # speed in pixels per millisecond
    distance = speed_pixel_per_ms * dt
    current_pos = pacman.rect.topleft
    if target_pos is None \
      or (abs(current_pos[0] - target_pos[0]) < 2 and abs(current_pos[1] - target_pos[1]) <2) \
      or new_direction !=current_direction:
        potential_x =current_pos[0] + new_direction[0] * TILE_SIZE
        potential_y =current_pos[1] + new_direction[1] * TILE_SIZE
        potential_target = (potential_x, potential_y)
        maze_coord = MazeCoord.nearest_coord(potential_target)
        if maze_coord is not None \
          and maze_weights[maze_coord.y,maze_coord.x] < MazePart.WALL.weight:
            current_direction = new_direction
            target_pos = maze_coord.rect.topleft
        elif target_pos is None:
            return (0,0),None


    if target_pos is not None:
        move_x = 0
        move_y =0
        if current_pos[0] < target_pos[0]:
            move_x = min (distance, target_pos[0] - current_pos[0])
        elif current_pos[0] > target_pos[0]:
            move_x  = max (-distance, target_pos[0] - current_pos[0])
        if current_pos[1] < target_pos[1]:
            move_y  =min (distance, target_pos[1] - current_pos[1])
        elif current_pos[1] > target_pos[1]:
            move_y  =max (-distance, target_pos[1] - current_pos[1])

        pacman.rect.topleft = (current_pos[0] + move_x, current_pos[1] + move_y)
    return current_direction, target_pos

def move_pacman_by_keys(
        pacman: Player,
        keys:any,
        maze_weights: np.ndarray[np.uint16]) -> None:
    """
    Move the pacman using arrow keys.
    """
    current_position = pacman.rect.topleft
    new_position = list(current_position)
    if keys[K_UP]:
        new_position[1] -= TILE_SIZE
    elif keys[K_DOWN]:
        new_position[1] += TILE_SIZE
    elif keys[K_LEFT]:
        new_position[0] -= TILE_SIZE
    elif keys[K_RIGHT]:
        new_position[0] += TILE_SIZE
    else:
        # No movement keys pressed
        return
    maze_coord = MazeCoord.nearest_coord(new_position)
    if maze_coord is not None and maze_weights[maze_coord.y, maze_coord.x] < MazePart.WALL.weight:
        # Move pacman to the new position
        pacman.rect.topleft = maze_coord.rect.topleft
def move_pacman_by_mouse(
        pacman: Player,
        mouse_pos: tuple[int, int],
        maze_weights: np.ndarray[np.uint16]) -> None:
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
    run_level()
