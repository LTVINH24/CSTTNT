import time
from queue import PriorityQueue
from src.maze import MazeNode
from .pathfinder import Pathfinder, PathfindingResult
from .pathfinding_monitor import pathfinding_monitor

# Hàm tính khoảng cách Manhattan
def Manhattan_distance(position1, position2):
    return abs(position1[0] - position2[0]) + abs(position1[1] - position2[1])

# Hàm tính khoảng cách Euclidean
def Euclidean_distance(position1, position2):
    return ((position1[0] - position2[0])**2 + (position1[1] - position2[1])**2)**0.5

@pathfinding_monitor
def a_star_pathfinder(
    maze_graph: list[MazeNode],
    start_location: tuple[MazeNode, MazeNode | None],
    target_location: tuple[MazeNode, MazeNode | None],
) -> PathfindingResult:
    """
    Thuật toán A* tìm đường đi từ điểm bắt đầu đến điểm đích trong mê cung.
    """
    # Lấy node bắt đầu và node đích
    start_node = start_location[0]
    if len(start_location) > 1 and start_location[1] is not None:
        start_node = start_location[1]
    target_node = target_location[0]
    
    # Kiểm tra nếu đã ở điểm đích
    if start_node == target_node:
        return PathfindingResult([start_node], [start_node])
    
    # Bảng tra cứu nhanh từ ID sang node
    node_lookup = {id(node): node for node in maze_graph}

    # Khởi tạo các tập hợp và danh sách
    open_set = PriorityQueue()  # Danh sách mở
    closed_set = set()          # Danh sách đóng
    in_open_set = set()         # Kiểm tra node trong open_set
    expanded_nodes = [start_node]  # Node đã mở rộng
    
    # Lưu đường đi và chi phí
    came_from = {}
    g_score = {id(node): float('inf') for node in maze_graph}
    f_score = {id(node): float('inf') for node in maze_graph}
    
    # Khởi tạo node bắt đầu
    start_id = id(start_node)
    g_score[start_id] = 0
    h_score = Manhattan_distance(start_node.pos.center, target_node.pos.center)
    f_score[start_id] = h_score
    
    # Thêm node bắt đầu vào danh sách mở
    counter = 0
    open_set.put((f_score[start_id], counter, start_id))
    in_open_set.add(start_id)
    
    # Lưu node gần đích nhất
    best_node = start_node
    best_distance = Manhattan_distance(start_node.pos.center, target_node.pos.center)
    
    # Giới hạn thời gian và số lần lặp
    start_time = time.time()
    max_time = 2  # Giới hạn thời gian tối đa
    iterations = 0
    max_iterations = 100  # Giới hạn số lần lặp tối đa
    
    # Vòng lặp chính
    while not open_set.empty() and iterations < max_iterations:
        # Kiểm tra thời gian thực thi
        if time.time() - start_time > max_time:
            # Trả về đường đi tốt nhất tìm được nếu hết thời gian
            if best_node != start_node:
                path = reconstruct_path(came_from, id(best_node), node_lookup)
                return PathfindingResult(path, expanded_nodes)
            break
        
        iterations += 1
        
        # Lấy node có f_score tốt nhất
        _, _, current_id = open_set.get(block=False)  # Không block để tránh treo
        current = node_lookup[current_id]
        in_open_set.remove(current_id)
        
        # Nếu đã xét node này rồi, bỏ qua
        if current_id in closed_set:
            continue
        
        # Nếu đã đến đích
        if current_id == id(target_node):
            path = reconstruct_path(came_from, current_id, node_lookup)
            # Thêm target_node[1] vào đường đi nếu tồn tại
            if len(target_location) > 1 and target_location[1] is not None:
                path.append(target_location[1])
            return PathfindingResult(path, expanded_nodes)
        
        # Cập nhật node gần đích nhất
        current_distance = Manhattan_distance(current.pos.center, target_node.pos.center)
        if current_distance < best_distance:
            best_node = current
            best_distance = current_distance
        
        # Đánh dấu node hiện tại đã xét
        closed_set.add(current_id)
        
        # Xét các node kề
        if not hasattr(current, 'neighbors'):
            continue  # Bỏ qua node không có thuộc tính neighbors
            
        for direction, neighbor_data in current.neighbors.items():
            if not neighbor_data or len(neighbor_data) < 2:
                continue
            
            neighbor, cost = neighbor_data
            neighbor_id = id(neighbor)
            
            if neighbor_id in closed_set:
                continue
            
            # Tính toán chi phí mới
            new_g_score = g_score[current_id] + cost
            heuristic = Manhattan_distance(neighbor.pos.center, target_node.pos.center)
            new_f_score = new_g_score + heuristic
            
            # Nếu đường đi mới tốt hơn
            if new_f_score < f_score[neighbor_id]:
                came_from[neighbor_id] = current_id
                g_score[neighbor_id] = new_g_score
                f_score[neighbor_id] = new_f_score
                
                # Thêm vào danh sách mở nếu chưa có
                if neighbor_id not in in_open_set:
                    expanded_nodes.append(neighbor)
                    counter += 1
                    open_set.put((new_f_score, counter, neighbor_id))
                    in_open_set.add(neighbor_id)
    
    # Nếu không tìm thấy đường đi hoàn chỉnh, trả về đường đi tốt nhất
    if best_node != start_node:
        print("Best node found:", best_node)
        path = reconstruct_path(came_from, id(best_node), node_lookup)
        return PathfindingResult(path, expanded_nodes)
        
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

assert isinstance(a_star_pathfinder, Pathfinder)