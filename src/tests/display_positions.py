import time
import math
import sys
import pygame as pg
from src.maze import set_up_level, render_maze_level
from src.player import Player
from src.ghost import Ghost
from src.constant import TILE_SIZE
from src.pathfinding import PathDispatcher

def euclidean_distance(sp1, sp2):
    """
    Tính khoảng cách Euclidean giữa hai spawn point.
    """
    # Lấy tọa độ trung tâm của hai spawn point
    c1 = sp1.rect.center
    c2 = sp2.rect.center
    return math.hypot(c1[0] - c2[0], c1[1] - c2[1])

def find_min_x_pair(spawn_points):
    """Tìm cặp spawn points có chênh lệch trên trục X nhỏ nhất trong test case 4."""
    n = len(spawn_points)
    best_pair = None
    min_dx = float('inf')
    for i in range(n):
        for j in range(i + 1, n):
            dx = abs(spawn_points[i].rect.centerx - spawn_points[j].rect.centerx)
            if dx < min_dx:
                min_dx = dx
                best_pair = (i, j)
    return best_pair

def find_y_pair(spawn_points):
    """Tìm spawn với Y nhỏ nhất cho Pac-Man (cao nhất màn hình) và Y lớn nhất cho Ghost trong test case 5."""
    pacman_spawn = min(spawn_points, key=lambda sp: sp.rect.centery)
    ghost_spawn = max(spawn_points, key=lambda sp: sp.rect.centery)
    return pacman_spawn, ghost_spawn

def find_max_x_pair(spawn_points):
    """Tìm cặp spawn points có chênh lệch trên trục X lớn nhất trong test case 2."""
    n = len(spawn_points)
    best_pair = None
    max_dx = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = abs(spawn_points[i].rect.centerx - spawn_points[j].rect.centerx)
            if dx > max_dx:
                max_dx = dx
                best_pair = (i, j)
    return best_pair

def select_spawn_pair(maze_level, test_case: int):
    """
    Chọn cặp spawn cho Pac-Man và Ghost dựa trên các test case:
        1. Khoảng cách nhỏ nhất (Euclidean).
        2. Chênh lệch X lớn nhất: hai spawn xa nhau về phương ngang nhất.
        3. Khoảng cách nhỏ thứ hai (Euclidean).
        4. Chênh lệch X nhỏ nhất: hai spawn gần nhau về phương ngang nhất.
        5. Dựa trên toạ độ Y: Pac-Man ở spawn có Y nhỏ nhất, Ghost ở spawn có Y lớn nhất.
    """
    spawn_points = maze_level.spawn_points
    if len(spawn_points) < 2:
        raise ValueError("Cần ít nhất 2 spawn point để chọn vị trí cho Pac-Man và Ghost.")

    # Test case 2: chênh lệch X lớn nhất
    if test_case == 2:
        best_pair = find_max_x_pair(spawn_points)
        return spawn_points[best_pair[0]], spawn_points[best_pair[1]]
    
    # Test case 4: chênh lệch X nhỏ nhất
    if test_case == 4:
        best_pair = find_min_x_pair(spawn_points)
        return spawn_points[best_pair[0]], spawn_points[best_pair[1]]

    # Test case 5: dựa theo vị trí Y
    if test_case == 5:
        return find_y_pair(spawn_points)

    # Các test case dựa trên khoảng cách Euclidean (còn lại)
    n = len(spawn_points)
    pairs = []
    for i in range(n):
        for j in range(i+1, n):
            d = euclidean_distance(spawn_points[i], spawn_points[j])
            pairs.append(((i, j), d))
    pairs_sorted = sorted(pairs, key=lambda x: x[1])
    
    idx_pair = None
    # Chọn cặp spawn dựa trên test case còn lại
    if len(pairs_sorted) == 1:
        idx_pair = pairs_sorted[0][0]
    elif test_case == 1:  # Khoảng cách nhỏ nhất tính bằng thuật toán Euclidean
        idx_pair = pairs_sorted[0][0]
    elif test_case == 3:  # Khoảng cách nhỏ thứ hai
        idx_pair = pairs_sorted[1][0] if len(pairs_sorted) > 1 else pairs_sorted[0][0]

    return spawn_points[idx_pair[0]], spawn_points[idx_pair[1]]

def get_test_case_description(test_case):
    """Returns the description of selection criteria for a test case."""
    descriptions = {
        1: "Closest spawn points (minimum Euclidean distance)",
        2: "Maximum X-axis difference (horizontally farthest apart)", # Mô tả mới cho test case 2
        3: "Second closest spawn points",
        4: "Minimum X-axis difference (vertically aligned)",
        5: "Pac-Man at top, Ghost at bottom (Y-based positions)"
    }
    return descriptions.get(test_case, "Unknown test case")

def display_test_positions():
    """
    Hiển thị trực quan vị trí Pac-Man và Ghost trong từng test case.
    Mỗi test case hiển thị trong 5 giây.
    """
    # Khởi tạo pygame
    pg.init()
    screen = pg.display.set_mode((800, 600))
    clock = pg.time.Clock()
    
    # Khởi tạo font để hiển thị thông tin
    font = pg.font.SysFont('Arial', 20)
    title_font = pg.font.SysFont('Arial', 24, bold=True)
    
    # Tạo maze level
    maze_level = set_up_level(screen=screen, level=1)
    
    # ALGORITHM_TO_GHOST mapping for displaying different ghost types
    ghost_types = ["blinky", "inky", "pinky", "clyde", "blinky"]
    
    for test_case in range(1, 6):
        pg.display.set_caption(f"Test Case {test_case} Positions")
        
        # Lấy vị trí spawn cho test case hiện tại
        pacman_spawn, ghost_spawn = select_spawn_pair(maze_level, test_case)
        
        # Tạo đối tượng Pac-Man và Ghost
        pacman = Player(initial_position=pacman_spawn.rect.topleft, speed=0)  # speed=0 để không di chuyển
        pacman_group = pg.sprite.GroupSingle(pacman)
        
        # Sử dụng ghost_types[test_case-1] để hiển thị các loại ghost khác nhau trong mỗi test case
        ghost = Ghost(
            initial_position=ghost_spawn,
            speed=0,  # speed=0 để không di chuyển
            ghost_type=ghost_types[test_case-1],
            ghost_group=maze_level.ghosts,
            path_dispatcher=None,  # Không cần path_dispatcher vì không di chuyển
        )
        
        # Vị trí theo tile và pixel
        pacman_pos_tile = (pacman_spawn.rect.centerx // TILE_SIZE, 
                          pacman_spawn.rect.centery // TILE_SIZE)
        ghost_pos_tile = (ghost_spawn.rect.centerx // TILE_SIZE, 
                         ghost_spawn.rect.centery // TILE_SIZE)
        
        pacman_pos_pixel = pacman_spawn.rect.topleft
        ghost_pos_pixel = ghost_spawn.rect.topleft
        
        # Tính khoảng cách Euclidean
        distance = euclidean_distance(pacman_spawn, ghost_spawn)
        
        # Thời điểm bắt đầu hiển thị test case
        start_time = time.time()
        running = True
        
        # Hiển thị test case trong 5 giây
        while running and (time.time() - start_time) < 5:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit(0)
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        pg.quit()
                        sys.exit(0)
                    elif event.key == pg.K_SPACE:
                        # Bỏ qua test case hiện tại nếu nhấn space
                        running = False
            
            # Xóa màn hình
            screen.fill((0, 0, 0))
            
            # Vẽ mê cung
            render_maze_level(maze_level, screen, 0)
            
            # Vẽ Pac-Man và Ghost
            pacman_group.draw(screen)
            maze_level.ghosts.draw(screen)
            
            # Hiển thị thông tin của test case
            title_text = title_font.render(f"Test Case {test_case}", True, (255, 255, 255))
            screen.blit(title_text, (20, 20))
            
            info_texts = [
                f"Selection: {get_test_case_description(test_case)}",
                f"Pac-Man: Tile ({pacman_pos_tile[0]}, {pacman_pos_tile[1]}), Pixel {pacman_pos_pixel}",
                f"Ghost: Tile ({ghost_pos_tile[0]}, {ghost_pos_tile[1]}), Pixel {ghost_pos_pixel}",
                f"Euclidean distance: {distance:.2f} pixels",
                f"Time left: {5 - (time.time() - start_time):.1f}s"
            ]
            
            y_offset = 60
            for text in info_texts:
                text_surface = font.render(text, True, (255, 255, 255))
                screen.blit(text_surface, (20, y_offset))
                y_offset += 30
            
            pg.display.flip()
            clock.tick(60)
        
        # Xóa ghost trước khi chuyển qua test case tiếp theo
        maze_level.ghosts.empty()
    
    # In thông báo kết thúc
    print("Đã hiển thị xong tất cả các test case")
    pg.quit()
    
if __name__ == "__main__":
    display_test_positions()