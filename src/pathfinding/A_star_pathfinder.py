"""
Thuật toán A* tìm đường đi tối ưu sử dụng khoảng cách Manhattan làm heuristic.
A* kết hợp chi phí đường đi thực tế và ước lượng khoảng cách đến đích để tìm đường đi
ngắn nhất một cách hiệu quả.
"""
from queue import PriorityQueue
from src.maze import MazeNode
from .pathfinder import Pathfinder, PathfindingResult
from .pathfinding_monitor import pathfinding_monitor

def manhattan_distance(p1, p2):
    """
    Tính khoảng cách Manhattan giữa hai điểm p1 và p2.
    Khoảng cách Manhattan là tổng của độ chênh lệch tuyệt đối giữa các tọa độ x và y.
    """
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

@pathfinding_monitor
def a_star_pathfinder(
    maze_graph: list[MazeNode],
    start_location: tuple[MazeNode, MazeNode | None],
    target_location: tuple[MazeNode, MazeNode | None],
) -> PathfindingResult:
    """
    Tìm đường đi từ vị trí bắt đầu đến vị trí đích sử dụng thuật toán A*.
    
    A* chọn node tiếp theo để mở rộng dựa trên tổng chi phí f(n) = g(n) + h(n),
    trong đó g(n) là chi phí từ vị trí bắt đầu đến node hiện tại và h(n) là 
    ước lượng chi phí từ node hiện tại đến đích.
    """
    # Xác định node bắt đầu và đường dẫn ban đầu
    start_path = []
    if start_location[1] is not None:
        starting_node = start_location[1]
        start_path = [start_location[0]]
    else:
        starting_node = start_location[0]
        
    # Xác định node đích
    target_node = target_location[0]
    target_second_node = None
    if target_location[1] is not None:
        target_second_node = target_location[1]
        
    # Khởi tạo cấu trúc dữ liệu
    open_set = PriorityQueue()
    visited = set()
    expanded_nodes = []
    
    # Khởi tạo g_score và f_score cho tất cả các node
    g_score = {node: float('inf') for node in maze_graph}
    f_score = {node: float('inf') for node in maze_graph}
    
    # Cập nhật g_score và f_score cho node bắt đầu
    g_score[starting_node] = 0
    f_score[starting_node] = manhattan_distance(starting_node.pos.center, target_node.pos.center)
    
    # Thêm node bắt đầu vào hàng đợi ưu tiên
    counter = 0
    open_set.put((f_score[starting_node], counter, starting_node, start_path))
    
    while not open_set.empty():
        # Lấy node có f_score thấp nhất
        _, _, current_node, path = open_set.get()
        
        # Kiểm tra đích
        if current_node == target_node:
            final_path = path + [current_node]
            if target_second_node is not None and target_second_node not in final_path:
                final_path.append(target_second_node)
            return PathfindingResult(final_path, expanded_nodes)
            
        if target_second_node is not None and current_node == target_second_node:
            final_path = path + [current_node]
            if target_node not in final_path:
                final_path.append(target_node)
            return PathfindingResult(final_path, expanded_nodes)
        
        # Bỏ qua nếu đã thăm node này
        if current_node in visited:
            continue
            
        # Đánh dấu node đã thăm và mở rộng
        visited.add(current_node)
        expanded_nodes.append(current_node)
        
        # Xét các node kề
        for neighbor, cost in current_node.neighbors.values():
            if neighbor in visited:
                continue
                
            # Tính toán g_score mới
            tentative_g = g_score[current_node] + cost
            
            # Nếu tìm thấy đường đi tốt hơn
            if tentative_g < g_score[neighbor]:
                # Cập nhật g_score và f_score
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + manhattan_distance(neighbor.pos.center, target_node.pos.center)
                
                # Thêm vào hàng đợi ưu tiên
                counter += 1
                open_set.put((f_score[neighbor], counter, neighbor, path + [current_node]))
    
    # Không tìm thấy đường đi
    return PathfindingResult(start_path, expanded_nodes)

assert isinstance(a_star_pathfinder, Pathfinder)
