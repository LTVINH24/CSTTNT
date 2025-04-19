"""
Test pathfinding algorithms in a Pac-Man game environment.
In this module, we will runn 5 different test cases
and give information about the algorithm's performance.
"""
import time
import math
import csv
import sys
import os
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

def select_spawn_pair(maze_level, test_case: int):
    """
    Chọn cặp spawn cho Pac-Man và Ghost dựa trên các test case:
        1. Khoảng cách nhỏ nhất (Euclidean).
        2. Khoảng cách lớn nhất (Euclidean).
        3. Khoảng cách nhỏ thứ hai (Euclidean).
        4. Chênh lệch X nhỏ nhất: hai spawn gần nhau về phương ngang nhất.
        5. Dựa trên toạ độ Y: Pac-Man ở spawn có Y nhỏ nhất, Ghost ở spawn có Y lớn nhất.
    """
    spawn_points = maze_level.spawn_points
    if len(spawn_points) < 2:
        raise ValueError("Cần ít nhất 2 spawn point để chọn vị trí cho Pac-Man và Ghost.")

    # Test case 4: chênh lệch X nhỏ nhất
    if test_case == 4:
        best_pair = find_min_x_pair(spawn_points)
        return spawn_points[best_pair[0]], spawn_points[best_pair[1]]

    # Test case 5: dựa theo vị trí Y
    if test_case == 5:
        return find_y_pair(spawn_points)

    # Các test case dựa trên khoảng cách Euclidean (hợp nhất hai hàm)
    n = len(spawn_points)
    pairs = []
    for i in range(n):
        for j in range(i+1, n):
            d = euclidean_distance(spawn_points[i], spawn_points[j])
            pairs.append(((i, j), d))
    pairs_sorted = sorted(pairs, key=lambda x: x[1])
    
    idx_pair = None
    # Chọn cặp spawn dựa trên test case
    if len(pairs_sorted) == 1:
        idx_pair = pairs_sorted[0][0]
    elif test_case == 1:  # Khoảng cách nhỏ nhất tính bằng thuật toán Euclidean
        idx_pair = pairs_sorted[0][0]
    elif test_case == 2:  # Khoảng cách lớn nhất tính bằng thuật toán Euclidean
        idx_pair = pairs_sorted[-1][0]
    elif test_case == 3:  # Khoảng cách nhỏ thứ hai
        idx_pair = pairs_sorted[1][0] if len(pairs_sorted) > 1 else pairs_sorted[0][0]

    return spawn_points[idx_pair[0]], spawn_points[idx_pair[1]]

# Bảng ánh xạ thuật toán với loại ma tương ứng
ALGORITHM_TO_GHOST = {
    "A*": "blinky",    
    "BFS": "inky",     
    "DFS": "pinky",
    "UCS": "clyde"
}

# Thực hiện chạy test case trực quan với Ghost đuổi Pacman khi Pacman đứng yên.
def run_visual_test(
        test_case: int,
        pathfinder,
        algorithm_name: str,
        simulation_duration=20)-> dict:
    """
    Chạy một test case trực quan với ghost đuổi Pac-Man.
      - test_case: số thứ tự test (1 đến 5) để chọn cấu hình spawn của Pac-Man và Ghost.
      - pathfinder: thuật toán tìm đường đi (a_star, dijkstra, bfs, dfs, ...)
      - algorithm_name: tên thuật toán tìm đường để hiển thị và ghi vào báo cáo
      - simulation_duration: thời gian tối đa chạy test case (giây).

    Khi ghost chạm vào Pac-Man, test case dừng lại ngay.
    Hàm trả về dictionary thống kê gồm:
        "Test Case", "Algorithm", "Ghost Type", "Collision", "Duration (s)", "Search Time (s)", 
        "Memory Peak (bytes)", "Expanded Nodes", "Nodes are passed", "Path Weight"
    """
    # pylint: disable=no-member
    pg.init()
    # pylint: enable=no-member
    screen_sizes = (800, 600)
    screen = pg.display.set_mode(screen_sizes)
    pg.display.set_caption(f"Test Case {test_case}: {algorithm_name} - Ghost đuổi Pac-Man")
    clock = pg.time.Clock()

    # Khởi tạo giá trị mặc định cho elapsed_time
    elapsed_time = 0

    maze_level = set_up_level(screen=screen, level=1)
    pacman_spawn, ghost_spawn = select_spawn_pair(maze_level, test_case)

    pacman = Player(initial_position=pacman_spawn.rect.topleft, speed=TILE_SIZE * 2)
    pacman_group = pg.sprite.GroupSingle(pacman)

    # Tạo đối tượng path dispatcher với thuật toán được chọn.
    path_dispatcher = PathDispatcher(
        maze_layout=maze_level.maze_layout,
        player=pacman,
        pathfinder=pathfinder
    )

    # Chọn loại ghost dựa vào tên thuật toán
    ghost_type = "blinky"  # Mặc định là blinky (đỏ - A*)
    for alg_name, ghost in ALGORITHM_TO_GHOST.items():
        if alg_name in algorithm_name:
            ghost_type = ghost
            break

    ghost = Ghost(
        initial_position=ghost_spawn,
        speed=TILE_SIZE * 4,
        ghost_type=ghost_type,  # Sử dụng ghost_type tương ứng với thuật toán
        ghost_group=maze_level.ghosts,
        path_dispatcher=path_dispatcher,
    )

    start_ticks = pg.time.get_ticks()
    collision_occurred = False
    running = True

    while running:
        dt = clock.tick(60)
        for event in pg.event.get():
            if event.type == pg.QUIT: #pylint: disable=no-member
                running = False
                pg.quit() #pylint: disable=no-member
                sys.exit(0)  # Thoát hoàn toàn khỏi chương trình

        screen.fill((0, 0, 0))
        render_maze_level(maze_level, screen, dt)
        pacman_group.draw(screen)
        ghost.update(dt)  # Trong ghost.update, path_dispatcher sẽ gọi thuật toán và cập nhật last_stats
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
    # pylint: disable=no-member
    pg.quit()

    # Lấy số liệu  từ đối tượng path_dispatcher
    stats = getattr(pathfinder, 'last_stats', {})
    search_time = stats.get('search_time', 0)
    memory_peak = stats.get('memory_peak', 0)
    expanded_nodes = stats.get('expanded_nodes', 0)
    path_length = stats.get('path_length', 0)  # số node (ô) mà con ma đã đi qua
    path_weight = stats.get('path_weight', 0)  # tổng chi phí của dường đi

    return {
        "Test Case": test_case,
        "Algorithm": algorithm_name,
        "Ghost Type": ghost_type.capitalize(),  # Thêm thông tin về loại ghost được sử dụng
        "Collision": "Yes" if collision_occurred else "No",
        "Duration (s)": elapsed_time,
        "Search Time (s)": search_time,
        "Memory Peak (bytes)": memory_peak,
        "Expanded Nodes": expanded_nodes,
        "Nodes are passed": path_length,
        "Path Weight": path_weight
    }

def print_statistics_table(stats_list):
    """
    In bảng thống kê các thông số của 5 lần chạy với thuật toán ra màn hình console.
    """
    headers = ["Test Case", "Algorithm", "Ghost Type", "Collision", "Duration (s)", "Search Time (s)",
            "Memory Peak (bytes)", "Expanded Nodes", "Nodes are passed", "Path Weight"]
    header_format = "{:<10} {:<12} {:<12} {:<10} {:<15} {:<18} {:<20} {:<15} {:<12} {:<12}"
    print("\n" + header_format.format(*headers))
    print("-" * 140)
    
    for stats in stats_list:
        # Định dạng các giá trị cho bảng
        formatted_values = [
            stats["Test Case"],
            stats["Algorithm"],
            stats["Ghost Type"],
            stats["Collision"],
            stats["Duration (s)"],
            f"{stats['Search Time (s)']:.6f}",
            stats["Memory Peak (bytes)"],
            stats["Expanded Nodes"],
            stats["Nodes are passed"],
            stats["Path Weight"]
        ]
        print(header_format.format(*formatted_values))

def write_statistics_to_file(stats_list, algorithm_name):
    """
    Viết vào file csv các thông số thống kê của 5 lần chạy với thuật toán.
    File sẽ được thêm mới (append) nếu đã tồn tại, không ghi đè lên nội dung cũ.
    """
    try:
        # Tạo tên file hợp lệ bằng cách loại bỏ các ký tự đặc biệt
        safe_name = algorithm_name.lower().replace(' ', '_').replace('*', 'star')
        filename = f"test_{safe_name}.csv"
        
        # Sử dụng đường dẫn tuyệt đối cho file đầu ra
        output_dir = os.path.join(os.getcwd(), "results")
        
        # Tạo thư mục results nếu chưa tồn tại
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Đường dẫn đầy đủ đến file
        filepath = os.path.join(output_dir, filename)
        
        # Kiểm tra xem file đã tồn tại chưa
        file_exists = os.path.isfile(filepath)
        
        headers = ["Test Case", "Algorithm", "Ghost Type", "Collision", "Duration (s)", "Search Time (s)", 
                  "Memory Peak (bytes)", "Expanded Nodes", "Nodes are passed", "Path Weight"]
        
        print(f"\nĐang ghi kết quả vào file: {filepath}")
        
        # Mở file ở chế độ append - thêm vào cuối file
        with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Chỉ viết headers nếu file chưa tồn tại
            if not file_exists:
                writer.writerow(headers)
            
            # Ghi dữ liệu của các lần chạy
            for stats in stats_list:
                row = [
                    stats["Test Case"],
                    stats["Algorithm"],
                    stats["Ghost Type"],
                    stats["Collision"],
                    stats["Duration (s)"],
                    f"{stats['Search Time (s)']:.6f}",
                    stats["Memory Peak (bytes)"],
                    stats["Expanded Nodes"],
                    stats["Nodes are passed"],
                    stats["Path Weight"]
                ]
                writer.writerow(row)
        
        print(f"Đã lưu kết quả thành công vào file: {filepath}")
    except Exception as e:
        print(f"Lỗi khi lưu file: {str(e)}")
        print("Tiếp tục chương trình mà không lưu kết quả.")

def run_algorithm_tests(pathfinder, algorithm_name, simulation_duration=60):
    """
    Run all test cases for a specific pathfinding algorithm.
    
    Args:
        pathfinder: The pathfinding algorithm function to use
        algorithm_name: Name of the algorithm for display and reporting
        simulation_duration: Maximum duration for each test in seconds
        
    Returns:
        List of dictionaries containing test statistics
    """
    all_stats = []
    for test in range(1, 6):
        print(f"\nĐang chạy Test Case {test} với thuật toán {algorithm_name}")
        stats = run_visual_test(
            test_case=test, 
            pathfinder=pathfinder,
            algorithm_name=algorithm_name,
            simulation_duration=simulation_duration
        )
        all_stats.append(stats)
        print(f"Test Case {test} hoàn tất. Chuyển sang test case tiếp theo trong 2 giây...")
        time.sleep(2)
    
    print(f"\nBảng thống kê các thông số của 5 lần chạy với thuật toán {algorithm_name}:")
    print_statistics_table(all_stats)
    
    # Viết thống kê vào file csv
    write_statistics_to_file(all_stats, algorithm_name)
    
    return all_stats