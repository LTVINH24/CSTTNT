"""
Module này triển khai cấp độ "Red Ghost" với ma đỏ Blinky sử dụng thuật toán tìm đường A*.

Blinky (ma đỏ) được lập trình để đuổi theo Pac-Man sử dụng thuật toán A* search,
cung cấp hành vi truy đuổi thông minh và hiệu quả.

Constants:
    NUMBER_OF_GHOSTS (int): Số lượng ma trong cấp độ (luôn là 1).
    INITIAL_SPEED_MULTIPLIER (int): Hệ số tốc độ ban đầu của ma đỏ.
    BASE_SPEED (int): Tốc độ cơ bản của ma tính bằng pixels/giây.
    ARBITARY_SCREEN_SIZES (tuple[int, int]): Kích thước màn hình cho bố cục mê cung.
    LEVEL (int): Số cấp độ, được sử dụng để tải file bố cục mê cung tương ứng.

Notes:
- Module này sử dụng thuật toán A* để tìm đường đi, giúp ma đỏ đuổi theo Pacman.
- Bố cục mê cung được tải bằng hàm `set_up_level` từ thư mục "assets/levels".
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
from src.pathfinding import PathDispatcher, a_star_pathfinder
from src.constant import TILE_SIZE
from src.ghost import Ghost
from src.player import Player

NUMBER_OF_GHOSTS = 1
INITIAL_SPEED_MULTIPLIER = 4  # Hệ số tốc độ ban đầu của ma
BASE_SPEED = TILE_SIZE * INITIAL_SPEED_MULTIPLIER  # Tốc độ cơ bản tính bằng pixels/giây
MIN_GHOST_SPAWN_DISTANCE = 5 * TILE_SIZE
ARBITARY_SCREEN_SIZES = (800, 600)  # Kích thước màn hình tùy ý cho bố cục mê cung
LEVEL = 1  # Tạo file "level_.txt" của riêng bạn trong thư mục "assets/levels"

def check_collision(ghost, pacman):
    """
    Kiểm tra va chạm giữa ma và Pacman.
    Trả về True nếu có va chạm, False nếu không.
    """
    # Sử dụng hàm va chạm có sẵn của Pygame
    return pg.sprite.collide_rect(ghost, pacman)

def calculate_distance(pos1, pos2):
    """
    Tính khoảng cách Euclidean giữa hai điểm.
    """
    return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5

def run_level():
    """
    Chạy cấp độ mê cung với ma đỏ (Blinky).
    """
    # Thiết lập pygame
    # pylint: disable=no-member
    pg.init()
    # pylint: enable=no-member
    screen_sizes = ARBITARY_SCREEN_SIZES
    screen = pg.display.set_mode(screen_sizes)
    pg.display.set_caption(f"Blinky - Level {LEVEL}")
    clock = pg.time.Clock()

    # Thiết lập cấp độ mê cung
    maze_level: MazeLevel = set_up_level(
        screen=screen,
        level=LEVEL,
    )

    # Thiết lập pacman với điểm xuất hiện ngẫu nhiên
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
        pathfinder=a_star_pathfinder  # Sử dụng thuật toán A* để tìm đường
    )

    blinky = set_up_blinky(
        ghost_group=maze_level.ghosts,
        spawn_points=maze_level.spawn_points,
        path_dispatcher=path_dispatcher,
        pacman_spawn=pacman_spawn
    )

    while True:
        for event in pg.event.get():
            if event.type == QUIT:
                sys.exit()

        delta_time = clock.tick(60)  # Tính bằng ms

        # Kiểm tra va chạm giữa Blinky và Pacman
        if blinky and check_collision(blinky, pacman):
            print("Game Over! Blinky đã bắt được Pacman!")
            pg.time.wait(1000)  # Đợi 1 giây
            sys.exit() 
        # Làm mới màn hình
        screen.fill((0, 0, 0))

        # Vẽ mê cung và cập nhật ma
        render_maze_level(
            maze_level=maze_level,
            screen=screen,
            dt=delta_time,
        )
        # Vẽ pacman
        pacman_group.draw(screen)
        # Cập nhật path dispatcher
        path_dispatcher.update(dt=delta_time)

        # Cập nhật màn hình
        pg.display.flip()

def set_up_blinky(
        ghost_group: pg.sprite.Group,
        spawn_points: list[MazeCoord],
        path_dispatcher: PathDispatcher = None,
        pacman_spawn: MazeCoord = None,
    ) -> None:
    """
    Thiết lập ma đỏ (Blinky) trong mê cung.
    """
    # Lọc các điểm spawn cách xa Pacman
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
    # Chọn điểm xuất hiện ngẫu nhiên cho Blinky
    spawn_point = random.choice(valid_spawn_points)
    
    # Tạo ma đỏ (Blinky) - luôn sử dụng ghost_type="blinky" cho ma đỏ
    blinky = Ghost(
        initial_position=spawn_point,
        speed=BASE_SPEED,
        ghost_type="blinky",  # Chỉ định loại ma là Blinky (ma đỏ)
        ghost_group=ghost_group,
        path_dispatcher=path_dispatcher,
    )
    
    # In thông tin về ma đỏ
    print(f"Blinky (Red Ghost) spawned at position: {spawn_point.rect.center}")
    
    if pacman_spawn:
        distance = calculate_distance(spawn_point.rect.center, pacman_spawn.rect.center)
        print(f"Distance between Pacman and Blinky: {distance/TILE_SIZE:.2f} tiles")
    return blinky

def random_picker[T](items: Iterable[T], seed=None) -> Generator[T, None, None]:
    """Trình tạo để chọn ngẫu nhiên các mục từ danh sách."""
    generator = random.Random(seed)
    managing_items = list(items)
    while True:
        generator.shuffle(managing_items)
        yield from managing_items

if __name__ == "__main__":
    run_level()