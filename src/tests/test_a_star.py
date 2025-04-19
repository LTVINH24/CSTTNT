import time
import math
import pygame as pg
from src.maze import set_up_level, render_maze_level
from src.player import Player
from src.ghost import Ghost
from src.constant import TILE_SIZE
from src.pathfinding import PathDispatcher, a_star_pathfinder
import csv 

def compute_distance(sp1, sp2):
    c1 = sp1.rect.center
    c2 = sp2.rect.center
    return math.hypot(c1[0] - c2[0], c1[1] - c2[1])

def select_spawn_pair(maze_level, test_case: int):
    """
    Chọn cặp spawn cho Pac-Man và Ghost dựa trên các test case:
      1. Khoảng cách nhỏ nhất (Euclidean).
      2. Khoảng cách lớn nhất (Euclidean).
      3. Chênh lệch X nhỏ nhất: hai spawn gần nhau về phương ngang nhất.
      4. Khoảng cách nhỏ thứ hai (Euclidean).
      5. Dựa trên toạ độ Y: Pac-Man ở spawn có Y nhỏ nhất (cao nhất trên màn hình),
         Ghost ở spawn có Y lớn nhất (thấp nhất trên màn hình).
    """
    spawn_points = maze_level.spawn_points
    n = len(spawn_points)
    if n < 2:
        raise ValueError("Cần ít nhất 2 spawn point để chọn vị trí cho Pac-Man và Ghost.")

    # Test case 3: chênh lệch X nhỏ nhất
    if test_case == 3:
        best_pair = None
        min_dx = float('inf')
        for i in range(n):
            for j in range(i+1, n):
                dx = abs(spawn_points[i].rect.centerx - spawn_points[j].rect.centerx)
                if dx < min_dx:
                    min_dx = dx
                    best_pair = (i, j)
        idx_i, idx_j = best_pair
        return spawn_points[idx_i], spawn_points[idx_j]

    # Test case 5: dựa theo vị trí Y
    if test_case == 5:
        pacman_spawn = min(spawn_points, key=lambda sp: sp.rect.centery)
        ghost_spawn = max(spawn_points, key=lambda sp: sp.rect.centery)
        return pacman_spawn, ghost_spawn

    # Tính khoảng cách Euclidean giữa các cặp điểm spawn
    pairs = []
    for i in range(n):
        for j in range(i+1, n):
            d = compute_distance(spawn_points[i], spawn_points[j])
            pairs.append(((i, j), d))
    pairs_sorted = sorted(pairs, key=lambda x: x[1])

    # Nếu chỉ có một cặp duy nhất
    if len(pairs_sorted) == 1:
        i, j = pairs_sorted[0][0]
        return spawn_points[i], spawn_points[j]

    # Chọn theo test case
    if test_case == 1:
        idx_i, idx_j = pairs_sorted[0][0]
    elif test_case == 2:
        idx_i, idx_j = pairs_sorted[-1][0]
    elif test_case == 4:
        idx_i, idx_j = pairs_sorted[1][0]
    else:
        # Default: khoảng cách trung vị
        median = len(pairs_sorted) // 2
        idx_i, idx_j = pairs_sorted[median][0]

    pacman_spawn = spawn_points[idx_i]
    ghost_spawn = spawn_points[idx_j]
    return pacman_spawn, ghost_spawn



def run_visual_test(test_case: int, simulation_duration=20) -> dict:
    """
    Chạy một test case trực quan với ghost đuổi Pac-Man.
      - test_case: số thứ tự test (1 đến 5) để chọn cấu hình spawn của Pac-Man và Ghost.
      - simulation_duration: thời gian tối đa chạy test case (giây).

    Khi ghost chạm vào Pac-Man, test case dừng lại ngay.
    Hàm trả về dictionary thống kê gồm:
         "Test Case", "Collision", "Duration (s)", "Search Time (s)",
         "Memory Peak (bytes)", "Expanded Nodes"
    """
    pg.init()
    screen_sizes = (800, 600)
    screen = pg.display.set_mode(screen_sizes)
    pg.display.set_caption(f"Visual Test Case {test_case}: Ghost đuổi Pac-Man")
    clock = pg.time.Clock()

    # Khởi tạo giá trị mặc định cho elapsed_time
    elapsed_time = 0

    maze_level = set_up_level(screen=screen, level=1)
    pacman_spawn, ghost_spawn = select_spawn_pair(maze_level, test_case)

    pacman = Player(initial_position=pacman_spawn.rect.topleft, speed=TILE_SIZE * 2)
    pacman_group = pg.sprite.GroupSingle(pacman)

    # Tạo đối tượng path dispatcher với thuật toán A_star.
    # Chú ý: đối tượng này sẽ lưu các số liệu thật sau mỗi lần gọi A_star vào thuộc tính last_stats.
    path_dispatcher = PathDispatcher(
        maze_layout=maze_level.maze_layout,
        player=pacman,
        pathfinder=a_star_pathfinder
    )

    ghost = Ghost(
        initial_position=ghost_spawn,
        speed=TILE_SIZE * 4,
        ghost_type="blinky",
        ghost_group=maze_level.ghosts,
        path_dispatcher=path_dispatcher,
    )

    start_ticks = pg.time.get_ticks()
    collision_occurred = False
    running = True

    while running:
        dt = clock.tick(60)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        screen.fill((0, 0, 0))
        render_maze_level(maze_level, screen, dt)
        pacman_group.draw(screen)
        ghost.update(dt)  # Trong ghost.update, path_dispatcher sẽ gọi A_star và cập nhật last_stats
        maze_level.ghosts.draw(screen)
        
        pg.display.flip()

        if pg.sprite.collide_rect(ghost, pacman):
            collision_occurred = True
            elapsed_time = (pg.time.get_ticks() - start_ticks) / 1000.0
            print(f"Test Case {test_case}: Ghost đã chạm vào Pac-Man sau {elapsed_time:.2f} giây.")
            pg.time.wait(1000)
            running = False

        if (pg.time.get_ticks() - start_ticks) > simulation_duration * 1000:
            elapsed_time = simulation_duration
            running = False

    pg.quit()

    # Lấy số liệu thực từ đối tượng path_dispatcher (đã được cập nhật bởi quá trình gọi A_star)
    stats = getattr(a_star_pathfinder, 'last_stats', {})
    search_time = stats.get('search_time', 0)
    memory_peak = stats.get('memory_peak', 0)
    expanded_nodes = stats.get('expanded_nodes', 0)

    return {
        "Test Case": test_case,
        "Collision": "Yes" if collision_occurred else "No",
        "Duration (s)": elapsed_time,
        "Search Time (s)": search_time,
        "Memory Peak (bytes)": memory_peak,
        "Expanded Nodes": expanded_nodes
    }

def print_statistics_table(stats_list):
    headers = ["Test Case", "Collision", "Duration (s)", "Search Time (s)", "Memory Peak (bytes)", "Expanded Nodes"]
    header_format = "{:<10} {:<10} {:<15} {:<18} {:<20} {:<15}"
    print("\n" + header_format.format(*headers))
    print("-" * 90)
    
    for stats in stats_list:
        # Định dạng các giá trị cho bảng
        formatted_values = [
            stats["Test Case"],
            stats["Collision"],
            stats["Duration (s)"],
            "{:.6f}".format(stats["Search Time (s)"]),
            stats["Memory Peak (bytes)"],
            stats["Expanded Nodes"]
        ]
        print(header_format.format(*formatted_values))
def write_statistics_to_file(stats_list, filename):
    """
    Write the statistics table to a CSV file.
    
    Args:
        stats_list (list): List of dictionaries containing test statistics.
        filename (str): Name of the output file.
    """
    # Ensure the filename has .csv extension
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    headers = ["Test Case", "Collision", "Duration (s)", "Search Time (s)", "Memory Peak (bytes)", "Expanded Nodes"]
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write title as a comment
        writer.writerow(['# UNIFORM COST SEARCH (UCS) TEST RESULTS'])
        # Write headers
        writer.writerow(headers)
        
        # Write data rows
        for stats in stats_list:
            row = [
                stats["Test Case"],
                stats["Collision"],
                stats["Duration (s)"],
                "{:.6f}".format(stats["Search Time (s)"]),
                stats["Memory Peak (bytes)"],
                stats["Expanded Nodes"]
            ]
            writer.writerow(row)

def main():
    all_stats = []
    for test in range(1, 6):
        print(f"\nĐang chạy Test Case {test} ")
        stats = run_visual_test(test_case=test, simulation_duration=60)
        all_stats.append(stats)
        print(f"Test Case {test} hoàn tất. Chuyển sang test case tiếp theo trong 2 giây...")
        time.sleep(2)
    print("\nBảng thống kê các thông số của 5 lần chạy:")
    print_statistics_table(all_stats)

    # Write statistics to file
    write_statistics_to_file(all_stats, "test_a_star.csv")

if __name__ == "__main__":
    main()
