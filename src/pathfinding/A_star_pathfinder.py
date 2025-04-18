"""
Thuật toán A* 

Module này thực hiện thuật toán A* để tìm đường đi tối ưu giữa các node trong một lưới.
Thuật toán sử dụng khoảng cách Manhattan để làm heuristic.
"""

from queue import PriorityQueue
from src.maze import MazeNode
from .pathfinder import Pathfinder, PathfindingResult
from .pathfinding_monitor import pathfinding_monitor

# Ta tính khoảng cách mahattan để làm heuristic cho A*
def manhattan_distance(p1, p2):
    """
    Calculates the Manhattan distance between two points.

    Args:
        p1 (tuple): The first point as a tuple (x1, y1).
        p2 (tuple): The second point as a tuple (x2, y2).

    Returns:
        int: The Manhattan distance between the two points.
    """
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


@pathfinding_monitor
def a_star_pathfinder(
    maze_graph: list[MazeNode],
    start_location: tuple[MazeNode, MazeNode | None],
    target_location: tuple[MazeNode, MazeNode | None],
) -> PathfindingResult:
    
    """Thuật toán A* tìm đường đi."""
    
    # Lấy node bắt đầu và node đích
    start_node = start_location[1] if len(start_location) > 1 and start_location[1] else start_location[0]
    target_node = target_location[0]
    
    # Nếu nó là điểm đích, trả về start_node
    if start_node == target_node:
        return PathfindingResult([start_node], [start_node])
    
    # Khởi tạo 
    open_set = PriorityQueue()
    closed_set = set()
    expanded_nodes = [start_node]
    came_from = {}
    g_score = {node: float('inf') for node in maze_graph}
    f_score = {node: float('inf') for node in maze_graph}
    
    # Khởi tạo node bắt đầu
    g_score[start_node] = 0
    f_score[start_node] = manhattan_distance(start_node.pos.center, target_node.pos.center)
    
    # Thêm node bắt đầu vào danh sách mở
    counter = 0
    open_set.put((f_score[start_node], counter, start_node))
    
    # Vòng lặp chính
    while not open_set.empty():
        # Lấy node có f_score tốt nhất
        _, _, current = open_set.get()
        
        # Nếu đã xét node này rồi, bỏ qua
        if current in closed_set:
            continue
        
        # Nếu đã đến đích
        if current == target_node:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            
            # Thêm target_node[1] vào đường đi nếu tồn tại
            if len(target_location) > 1 and target_location[1]:
                path.append(target_location[1])
                          
            return PathfindingResult(path, expanded_nodes)
        
        # Đánh dấu node hiện tại đã xét
        closed_set.add(current)
        
        # Xét các node kề
        if not hasattr(current, 'neighbors'):
            continue
            
        for _, neighbor_data in current.neighbors.items():
            if not neighbor_data or len(neighbor_data) < 2:
                continue
            
            neighbor, cost = neighbor_data
            
            if neighbor in closed_set:
                continue
            
            # Tính toán chi phí mới
            new_g_score = g_score[current] + cost
            
            # Nếu đường đi mới tốt hơn, ta thực hiện cập nhật f_score và g_score
            if new_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = new_g_score
                f_score[neighbor] = new_g_score + manhattan_distance(neighbor.pos.center, target_node.pos.center)
                
                # Thêm vào danh sách mở
                expanded_nodes.append(neighbor)
                counter += 1
                open_set.put((f_score[neighbor], counter, neighbor))
    return PathfindingResult([start_node], expanded_nodes)

assert isinstance(a_star_pathfinder, Pathfinder)
