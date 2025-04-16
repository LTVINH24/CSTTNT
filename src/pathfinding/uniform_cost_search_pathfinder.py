"""
Thuật toán Uniform Cost Search (UCS) cho bài toán tìm đường đi.

UCS là thuật toán tìm kiếm theo đơn giá, chọn mở rộng nút có chi phí thấp nhất từ 
điểm bắt đầu. Khác với thuật toán A*, UCS không sử dụng hàm heuristic.
"""
import time
import tracemalloc
from queue import PriorityQueue

from src.maze import MazeNode
from .pathfinder import Pathfinder, PathfindingResult
from .pathfinding_monitor import pathfinding_monitor

@pathfinding_monitor
def ucs_pathfinder(
    maze_graph: list[MazeNode],
    start_location: tuple[MazeNode, MazeNode | None],
    target_location: tuple[MazeNode, MazeNode | None],
) -> PathfindingResult:
    """Thuật toán Uniform Cost Search (UCS) tìm đường đi."""
    # Bắt đầu theo dõi bộ nhớ và thời gian
    tracemalloc.start()
    start_time = time.time()
    
    # Lấy node bắt đầu và node đích
    start_node = start_location[0]
    if len(start_location) > 1 and start_location[1] is not None:
        start_node = start_location[1]
    target_node = target_location[0]
    
    # Kiểm tra nếu đã ở điểm đích
    if start_node == target_node:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end_time = time.time()
        # Lưu thống kê
        ucs_pathfinder.last_stats = {
            'search_time': end_time - start_time,
            'memory_peak': peak,
            'expanded_nodes': 1
        }
        return PathfindingResult([start_node], [start_node])
    
    # Khởi tạo cấu trúc dữ liệu
    node_lookup = {id(node): node for node in maze_graph}
    open_set = PriorityQueue()
    closed_set = set()
    expanded_nodes = [start_node]
    came_from = {}
    g_score = {id(node): float('inf') for node in maze_graph}
    
    # Khởi tạo node bắt đầu
    start_id = id(start_node)
    g_score[start_id] = 0
    counter = 0
    open_set.put((0, counter, start_id))
    
    # Vòng lặp chính
    while not open_set.empty():
        # Lấy node có chi phí thấp nhất
        _, _, current_id = open_set.get()
        current = node_lookup[current_id]
        
        # Nếu đã xét node này rồi, bỏ qua
        if current_id in closed_set:
            continue
        
        # Nếu đã đến đích
        if current_id == id(target_node):
            path = reconstruct_path(came_from, current_id, node_lookup)
            if len(target_location) > 1 and target_location[1] is not None:
                path.append(target_location[1])
                
            # Lấy thông tin bộ nhớ và thời gian
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            end_time = time.time()
            
            # Lưu thống kê
            ucs_pathfinder.last_stats = {
                'search_time': end_time - start_time,
                'memory_peak': peak,
                'expanded_nodes': len(expanded_nodes)
            }
            
            return PathfindingResult(path, expanded_nodes)
        
        # Đánh dấu node hiện tại đã xét
        closed_set.add(current_id)
        
        # Xét các node kề
        if not hasattr(current, 'neighbors'):
            continue
            
        for direction, neighbor_data in current.neighbors.items():
            if not neighbor_data or len(neighbor_data) < 2:
                continue
            
            neighbor, cost = neighbor_data
            neighbor_id = id(neighbor)
            
            if neighbor_id in closed_set:
                continue
            
            # Tính toán chi phí mới
            new_g_score = g_score[current_id] + cost
            
            # Nếu đường đi mới tốt hơn
            if new_g_score < g_score[neighbor_id]:
                came_from[neighbor_id] = current_id
                g_score[neighbor_id] = new_g_score
                expanded_nodes.append(neighbor)
                counter += 1
                open_set.put((new_g_score, counter, neighbor_id))
    
    # Nếu không tìm được đường đi
    # Lấy thông tin bộ nhớ và thời gian
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    end_time = time.time()
    
    # Lưu thống kê
    ucs_pathfinder.last_stats = {
        'search_time': end_time - start_time,
        'memory_peak': peak,
        'expanded_nodes': len(expanded_nodes)
    }
    
    return PathfindingResult([start_node], expanded_nodes)

def reconstruct_path(came_from, end_node_id, node_lookup):
    """Tạo lại đường đi từ điểm bắt đầu đến điểm kết thúc"""
    path = [node_lookup[end_node_id]]
    current_id = end_node_id
    
    while current_id in came_from:
        current_id = came_from[current_id]
        path.append(node_lookup[current_id])
    
    path.reverse()
    return path

assert isinstance(ucs_pathfinder, Pathfinder)