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
    """Thuật toán A* tìm đường đi."""
    
    # Lấy node bắt đầu và node đích
    start_first_node = start_location[0]
    start_second_node = start_location[1] if len(start_location) > 1 else None
    
    # Lấy node đích
    target_first_node = target_location[0]
    target_second_node = target_location[1] if len(target_location) > 1 else None

    print(f"Start node: {start_first_node}, Second start node: {start_second_node}")
    
    # Chọn node để chạy thuật toán A*
    start_node = start_second_node if start_second_node is not None else start_first_node
    target_node = target_first_node

    # Nếu nó là điểm đích, trả về cả hai node bắt đầu
    if start_node == target_node:
        result_path = []
        if start_first_node:
            result_path.append(start_first_node)
        if start_second_node and start_second_node != start_first_node:
            result_path.append(start_second_node)
        if target_second_node:
            result_path.append(target_second_node)
        return PathfindingResult(result_path, result_path)

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

        # Kiểm tra xem đã đến đích chưa, kiểm tra xem nó đến target_first hay là target_second trước
        reached_target_first = None
        reached_target_second = None
        if current == target_second_node:
            reached_target_second = target_second_node
        elif current == target_first_node:
            reached_target_first = target_first_node

        # Nếu đã đến một trong các đích
        if reached_target_first or reached_target_second:
            # Tạo đường đi từ đích về điểm bắt đầu
            temp_path = [current]
            temp_current = current
            while temp_current in came_from:
                temp_current = came_from[temp_current]
                temp_path.append(temp_current)
            
            # Đảo ngược để có đường đi từ đầu đến cuối
            temp_path.reverse()
            
            # Tạo đường đi cuối cùng, luôn đảm bảo start_location[0] và start_location[1] có trong đường đi
            final_path = []
            
            # Luôn thêm start_first_node vào đầu đường đi
            if start_first_node and start_first_node not in temp_path:
                final_path.append(start_first_node)
            
            # Luôn thêm start_second_node nếu có
            if start_second_node and start_second_node != start_first_node and start_second_node not in temp_path:
                final_path.append(start_second_node)
            
            # Thêm phần còn lại của đường đi
            final_path.extend(temp_path)

            # Xử lý thứ tự target nodes dựa trên node nào được đến trước
            if reached_target_second:
                # Ghost đến target_second trước - thêm target_second trước, sau đó là target_first
                
                # Đảm bảo target_second được thêm vào nếu nó không có trong đường đi
                if target_second_node not in final_path:
                    final_path.append(target_second_node)
                
                # Sau đó thêm target_first nếu nó không có trong đường đi
                if target_first_node not in final_path:
                    final_path.append(target_first_node)
            else:
                # Ghost đến target_first trước - thêm target_first trước, sau đó là target_second
                
                # Đảm bảo target_first có trong đường đi (có thể đã có từ temp_path)
                if target_first_node not in final_path:
                    final_path.append(target_first_node)
                
                # Sau đó thêm target_second nếu có và chưa có trong đường đi
                if target_second_node and target_second_node not in final_path:
                    final_path.append(target_second_node)

            return PathfindingResult(final_path, expanded_nodes)

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
    
    # Không tìm thấy đường đi, trả về các node bắt đầu
    result_path = []
    if start_first_node:
        result_path.append(start_first_node)
    if start_second_node and start_second_node != start_first_node:
        result_path.append(start_second_node)
        
    return PathfindingResult(result_path, expanded_nodes)


assert isinstance(a_star_pathfinder, Pathfinder)
