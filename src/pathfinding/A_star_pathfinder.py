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
    Thuật toán A* tìm đường đi từ điểm bắt đầu đến điểm đích trong mê cung
    """
    # Lấy node bắt đầu và node đích
    start_node = start_location[0]
    if len(start_location) > 1 and start_location[1] is not None:
        start_node = start_location[1]
    target_node = target_location[0]
    
    # Bảng tra cứu nhanh từ ID sang node
    node_lookup = {id(node): node for node in maze_graph}
    
    # Kiểm tra nếu đã ở điểm đích
    if start_node == target_node:
        return PathfindingResult([start_node], [start_node])

    # Khởi tạo các tập hợp và danh sách
    open_set = PriorityQueue()  # Danh sách mở
    closed_set = set()          # Danh sách đóng
    in_open_set = set()         # Kiểm tra node trong open_set
    expanded_nodes = [start_node] # Node đã mở rộng
    
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
    
    # Giới hạn thời gian và số lần lặp - TĂNG THỜI GIAN TỐI ĐA
    start_time = time.time()
    max_time = 2  # Giảm xuống 2 giây để nếu bị kẹt thì sẽ trả về kết quả sớm hơn
    iterations = 0
    max_iterations = 1000  # Giảm số lần lặp tối đa để tránh đứng hình
    
    # Vòng lặp chính
    while not open_set.empty() and iterations < max_iterations:
        # Kiểm tra thời gian thực thi NGHIÊM NGẶT hơn
        if time.time() - start_time > max_time:
            # Thoát sớm nếu quá thời gian
            break
        
        iterations += 1
        
        # Lấy node có f_score tốt nhất 
        try:
            _, _, current_id = open_set.get(block=False)  # Không block để tránh treo
            current = node_lookup[current_id]
            in_open_set.remove(current_id)
        except Exception:
            # Xử lý lỗi khi không thể lấy node từ queue
            break
        
        # Nếu đã xét node này rồi, bỏ qua
        if current_id in closed_set:
            continue
        
        # Nếu đã đến đích
        if current_id == id(target_node):
            path = reconstruct_path(came_from, current_id, node_lookup)
            return PathfindingResult(path, expanded_nodes)
        
        # Cập nhật node gần đích nhất 
        current_distance = Manhattan_distance(current.pos.center, target_node.pos.center)
        if current_distance < best_distance:
            best_node = current
            best_distance = current_distance
        
        # Đánh dấu node hiện tại đã xét
        closed_set.add(current_id)
        
        # Xét các node kề - THÊM KIỂM TRA AN TOÀN
        if not hasattr(current, 'neighbors'):
            continue  # Bỏ qua node không có thuộc tính neighbors
            
        for direction, neighbor_data in current.neighbors.items():
            # Kiểm tra dữ liệu kề hợp lệ
            if not neighbor_data or len(neighbor_data) < 2:
                continue
                
            neighbor, cost = neighbor_data
            neighbor_id = id(neighbor)
            
            # Bỏ qua node đã xét
            if neighbor_id in closed_set:
                continue
            
            # Tính toán chi phí mới
            new_g_score = g_score[current_id] + cost
            
            # Xử lý ngã ba, ngã tư - tính phạt cho việc đổi hướng
            # Giảm mức phạt xuống để không ảnh hưởng quá nhiều
            penalty = calculate_turning_penalty(came_from, current_id, direction, node_lookup) * 0.5
            
            # Tính heuristic và f_score mới
            heuristic = Manhattan_distance(neighbor.pos.center, target_node.pos.center)
            new_f_score = new_g_score + heuristic + penalty
            
            # Nếu đường đi mới tốt hơn
            if new_g_score < g_score[neighbor_id]:
                # Cập nhật thông tin đường đi
                came_from[neighbor_id] = current_id
                g_score[neighbor_id] = new_g_score
                f_score[neighbor_id] = new_f_score
                
                # Thêm vào danh sách mở nếu chưa có
                if neighbor_id not in in_open_set:
                    if neighbor not in expanded_nodes:
                        expanded_nodes.append(neighbor)
                    counter += 1
                    open_set.put((new_f_score, counter, neighbor_id))
                    in_open_set.add(neighbor_id)
    
    # Nếu không tìm thấy đường đi hoàn chỉnh
    if best_node != start_node:
        # Trả về đường đi tốt nhất có thể
        path = reconstruct_path(came_from, id(best_node), node_lookup)
        return PathfindingResult(path, expanded_nodes)
    else:
        # Tìm hướng đi tốt nhất
        best_next_node = find_best_direction(start_node, target_node)
        if best_next_node:
            # CHỈ TRẢ VỀ NODE KẾ TIẾP, KHÔNG BAO GỒM NODE HIỆN TẠI
            # Điều này giúp tránh lặp lại node hiện tại và không bị đứng im
            return PathfindingResult([best_next_node], expanded_nodes)
        else:
            return PathfindingResult([start_node], expanded_nodes)


def calculate_turning_penalty(came_from, current_id, direction, node_lookup):
    """Tính phạt cho việc đổi hướng (rẽ trái, rẽ phải, quay đầu)"""
    try:
        if current_id not in came_from:
            return 0
            
        # Tìm node trước đó
        prev_node_id = came_from[current_id]
        prev_node = node_lookup[prev_node_id]
        current = node_lookup[current_id]
            
        # Tìm hướng di chuyển trước đó
        prev_direction = None
        for d, neighbor_data in prev_node.neighbors.items():
            if not neighbor_data or len(neighbor_data) < 1:
                continue
                
            neighbor = neighbor_data[0]
            if id(neighbor) == current_id:
                prev_direction = d
                break
        
        if not prev_direction:
            return 0
            
        # Xử lý ngã ba, ngã tư - thêm phạt cho đổi hướng
        if direction != prev_direction:
            # Quay đầu (phạt nhiều nhất)
            if (prev_direction == 'up' and direction == 'down') or \
               (prev_direction == 'down' and direction == 'up') or \
               (prev_direction == 'left' and direction == 'right') or \
               (prev_direction == 'right' and direction == 'left') or \
                (prev_direction == 'down' and direction == 'right') or \
                (prev_direction == 'up' and direction == 'left'):
                print(prev_direction, direction)
                return 0.75  # Giảm xuống từ 1.0
            
            else:
                # Rẽ trái hoặc rẽ phải (phạt ít hơn)
                return 0.2  # Giảm xuống từ 0.3
        return 0
    except Exception:
        # Trả về 0 nếu có lỗi xảy ra
        return 0


def reconstruct_path(came_from, end_node_id, node_lookup):
    """Tạo lại đường đi từ điểm bắt đầu đến điểm kết thúc"""
    try:
        path = [node_lookup[end_node_id]]
        current_id = end_node_id
        
        # Giới hạn độ dài đường đi tối đa để tránh vòng lặp vô hạn
        max_path_length = 100
        path_length = 0
        
        while current_id in came_from and path_length < max_path_length:
            current_id = came_from[current_id]
            path.append(node_lookup[current_id])
            path_length += 1
        
        path.reverse()
        return path
    except Exception:
        # Trả về đường đi gồm chỉ node kết thúc nếu có lỗi
        if end_node_id in node_lookup:
            return [node_lookup[end_node_id]]
        return []


def find_best_direction(start_node, target_node):
    """Tìm hướng đi tốt nhất khi không tìm thấy đường đi hoàn chỉnh"""
    try:
        best_next_node = None
        best_score = float('inf')
        
        if not hasattr(start_node, 'neighbors'):
            return None
        
        for direction, neighbor_data in start_node.neighbors.items():
            if not neighbor_data or len(neighbor_data) < 2:
                continue
                
            neighbor, cost = neighbor_data
            
            h_score = Manhattan_distance(neighbor.pos.center, target_node.pos.center)
            score = h_score + cost
            
            # Tránh quay lại vị trí cũ
            if best_next_node and best_next_node == neighbor:
                continue

            if score < best_score:
                best_score = score
                best_next_node = neighbor
        
        return best_next_node
    except Exception:
        # Trả về None nếu có lỗi xảy ra
        return None


assert isinstance(a_star_pathfinder, Pathfinder)