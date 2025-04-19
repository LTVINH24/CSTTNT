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
    "blinky": a_star_pathfinder,
    "clyde": ucs_pathfinder,
    "inky": breadth_first_search_path_finder,
    "pinky": depth_first_search_path_finder,
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
    pacman_direction = None
    pacman_target_pos = None
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
        current_direction: tuple[int, int] = None,
        target_pos: tuple[int, int] = None,
        dt: float = 0) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Xử lý di chuyển mượt mà cho Pacman.
    """
    # Tốc độ pixel mỗi mili giây
    speed = pacman.speed / 1000
    
    # Xác định hướng mới nếu người dùng nhấn phím
    new_direction = None
    if keys[pg.K_UP]:
        new_direction = (0, -1)
    elif keys[pg.K_DOWN]:
        new_direction = (0, 1)
    elif keys[pg.K_LEFT]:
        new_direction = (-1, 0)
    elif keys[pg.K_RIGHT]:
        new_direction = (1, 0)
    
    # Nếu không có hướng hiện tại hoặc đã đến điểm mục tiêu, thiết lập hướng mới
    if target_pos is None or (abs(pacman.rect.x - target_pos[0]) <= 2 and abs(pacman.rect.y - target_pos[1]) < 2):
        if new_direction is not None:
            # Tính toán vị trí mục tiêu tiếp theo
            next_x = ((pacman.rect.x + TILE_SIZE//2) // TILE_SIZE) * TILE_SIZE
            next_y = ((pacman.rect.y + TILE_SIZE//2) // TILE_SIZE) * TILE_SIZE
            
            # Kiểm tra xem có thể di chuyển theo hướng mới không
            test_x = next_x + new_direction[0] * TILE_SIZE
            test_y = next_y + new_direction[1] * TILE_SIZE
            maze_coord = MazeCoord.nearest_coord((test_x, test_y))
            
            if maze_coord is not None and maze_weights[maze_coord.y, maze_coord.x] < MazePart.WALL.weight:
                # Căn chỉnh vị trí hiện tại về ô lưới
                pacman.rect.x = next_x
                pacman.rect.y = next_y
                current_direction = new_direction
                target_pos = (test_x, test_y)
    
    # Nếu đang di chuyển, tiếp tục di chuyển theo hướng hiện tại
    if current_direction is not None and target_pos is not None:
        pacman.rect.x += current_direction[0] * speed * dt
        pacman.rect.y += current_direction[1] * speed * dt
        
        # Kiểm tra xem đã đến đích chưa
        if (current_direction[0] > 0 and pacman.rect.x >= target_pos[0]) or \
           (current_direction[0] < 0 and pacman.rect.x <= target_pos[0]) or \
           (current_direction[1] > 0 and pacman.rect.y >= target_pos[1]) or \
           (current_direction[1] < 0 and pacman.rect.y <= target_pos[1]):
            pacman.rect.topleft = target_pos
            
            # Kiểm tra xem có thể tiếp tục di chuyển theo hướng hiện tại không
            next_x = target_pos[0] + current_direction[0] * TILE_SIZE
            next_y = target_pos[1] + current_direction[1] * TILE_SIZE
            maze_coord = MazeCoord.nearest_coord((next_x, next_y))
            
            if maze_coord is not None and maze_weights[maze_coord.y, maze_coord.x] < MazePart.WALL.weight:
                target_pos = (next_x, next_y)
    
    # Xử lý đổi hướng khi đang di chuyển
    if new_direction is not None and current_direction is not None and new_direction != current_direction:
        # Kiểm tra xem có thể đổi hướng không
        next_x = pacman.rect.x + new_direction[0] * TILE_SIZE
        next_y = pacman.rect.y + new_direction[1] * TILE_SIZE
        maze_coord = MazeCoord.nearest_coord((next_x, next_y))
        
        if maze_coord is not None and maze_weights[maze_coord.y, maze_coord.x] < MazePart.WALL.weight:
            # Căn chỉnh vị trí về ô lưới gần nhất trước khi đổi hướng
            pacman.rect.x = ((pacman.rect.x + TILE_SIZE//2) // TILE_SIZE) * TILE_SIZE
            pacman.rect.y = ((pacman.rect.y + TILE_SIZE//2) // TILE_SIZE) * TILE_SIZE
            current_direction = new_direction
            target_pos = (next_x, next_y)
    
    return current_direction, target_pos
def move_pacman_by_keys(
        pacman: Player,
        keys:any,
        maze_weights: np.ndarray[np.uint16]) -> None:
    current_position = pacman.rect.topleft
    new_position = list(current_position)
    if keys[pg.K_UP]:
        new_position[1] -= TILE_SIZE
    elif keys[pg.K_DOWN]:
        new_position[1] += TILE_SIZE
    elif keys[pg.K_LEFT]:
        new_position[0] -= TILE_SIZE
    elif keys[pg.K_RIGHT]:
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
    run_level(enable_movement_by_mouse=True)
