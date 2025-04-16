"""
This module serves as a template for setting up and running a level in a Pacman-like game.

It provides the necessary setup for the maze, player (Pacman), ghosts, and pathfinding logic. 
The module is designed to be used as a reference for creating new levels.

Constants:
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
from src.pathfinding import PathDispatcher, depth_first_search_path_finder
from src.constant import TILE_SIZE
from src.ghost import Ghost, GHOST_TYPES
from src.player import Player
from src.ui.game_over import show_game_over_screen
MIN_GHOST_SPAWN_DISTANCE = 5 * TILE_SIZE
NUMBER_OF_GHOSTS = 1
INITIAL_SPEED_MULTIPLIER = 4  # initial speed multiplier for the ghosts
BASE_SPEED = TILE_SIZE * INITIAL_SPEED_MULTIPLIER  # base speed in pixels per second

ARBITARY_SCREEN_SIZES = (800, 600)  # arbitrary screen sizes for the maze layout
LEVEL = 1 # create your own "level_.txt" file in "assets/levels" directory
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
    pacman = None
    pacman_group = None
    pinky = None  # Thay bằng tên ghost trong level
    path_dispatcher = None
    def initialize_level():
        nonlocal pacman,pacman_group,pinky,path_dispatcher
        maze_level: MazeLevel = set_up_level(
            screen=screen,
            level=LEVEL,
        )
        pacman_spawn = random.choice(maze_level.spawn_points)
        pacman_position = pacman_spawn.rect.topleft
        pacman = Player(
        initial_position=pacman_position,
        speed=BASE_SPEED,
        )
        pacman_group = pg.sprite.GroupSingle(pacman)
        path_dispatcher = PathDispatcher(
        maze_layout=maze_level.maze_layout,
        player=pacman,
        pathfinder=depth_first_search_path_finder, # TODO: replace with your own pathfinding algorithm
        )
        pinky = set_up_pinky(   #thay bằng tên ghost trong level
        ghost_group=maze_level.ghosts,
        spawn_points=maze_level.spawn_points,
        path_dispatcher=path_dispatcher,
        pacman_spawn=pacman_spawn
        )
        return maze_level

    # maze level setup
    maze_level = initialize_level()

    # pacman setup with random spawn point
    while True:
        for event in pg.event.get():
            if event.type == QUIT:
                sys.exit()

        delta_time = clock.tick(60) # in ms
        if pinky and check_collision(pinky, pacman):
            print("Game Over! Pinky đã bắt được Pacman!")
            
            screen.fill((0, 0, 0))
            render_maze_level(maze_level=maze_level, screen=screen, dt=0)
            pacman_group.draw(screen)
            choice = show_game_over_screen(screen)
            if choice =="replay":
                maze_level = initialize_level()
                continue
            elif choice == "exit":
                sys.exit()
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

def set_up_pinky(
        ghost_group: pg.sprite.Group,
        spawn_points: list[MazeCoord],
        path_dispatcher: PathDispatcher = None,
        pacman_spawn: MazeCoord = None,
    ) -> None:
    valid_spawn_points = []
    
    if pacman_spawn:
        pacman_center = pacman_spawn.rect.center
        # Lọc các điểm ở xa Pacman
        for point in spawn_points:
            if point != pacman_spawn:  # Không dùng cùng điểm với Pacman
                distance = calculate_distance(point.rect.center, pacman_center)
                if distance >= MIN_GHOST_SPAWN_DISTANCE:
                    valid_spawn_points.append(point)
    
    # Nếu không có điểm hợp lệ, chọn từ tất cả các điểm (trừ điểm của Pacman)
    if not valid_spawn_points:
        valid_spawn_points = [p for p in spawn_points if p != pacman_spawn]
        print("Cảnh báo: Không tìm thấy điểm spawn đủ xa cho Clyde!")
    
    # Nếu vẫn không có điểm nào, dùng tất cả các điểm
    if not valid_spawn_points:
        valid_spawn_points = spawn_points
        print("Cảnh báo: Buộc phải dùng tất cả các điểm spawn!")
    # Chọn điểm xuất hiện ngẫu nhiên cho Pinky
    spawn_point = random.choice(valid_spawn_points)
    
    # Tạo ma đỏ (Pinky) - luôn sử dụng ghost_type="pinky" cho ma đỏ
    pinky = Ghost(
        initial_position=spawn_point,
        speed=BASE_SPEED,
        ghost_type="pinky",  # Chỉ định loại ma là Pinky (ma hồng)
        ghost_group=ghost_group,
        path_dispatcher=path_dispatcher,
    )
    
    # In thông tin về ma đỏ
    print(f"pinky (Red Ghost) spawned at position: {spawn_point.rect.center}")
    
    if pacman_spawn:
        distance = calculate_distance(spawn_point.rect.center, pacman_spawn.rect.center)
        print(f"Distance between Pacman and Blinky: {distance/TILE_SIZE:.2f} tiles")
    return pinky

def random_picker[T](items: Iterable[T], seed=None) -> Generator[T, None, None]:
    """Generator to pick random items from a list."""
    generator = random.Random(seed)
    managing_items = list(items)
    while True:
        generator.shuffle(managing_items)
        yield from managing_items

if __name__ == "__main__":
    run_level()
