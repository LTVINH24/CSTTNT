"""
Thuật toán Uniform Cost Search (UCS) cho bài toán tìm đường đi.

UCS là thuật toán tìm kiếm theo đơn giá, chọn mở rộng nút có chi phí thấp nhất từ
điểm bắt đầu. Khác với thuật toán A*, UCS không sử dụng hàm heuristic.
"""
from queue import PriorityQueue

from src.maze import MazeNode
from .pathfinder import Pathfinder, PathfindingResult
from .pathfinding_monitor import pathfinding_monitor

@pathfinding_monitor
def ucs_pathfinder(
    _: list[MazeNode],
    start_location: tuple[MazeNode, MazeNode | None],
    target_location: tuple[MazeNode, MazeNode | None],
) -> PathfindingResult:
    """Thuật toán Uniform Cost Search (UCS) tìm đường đi."""
    # Xác định điểm bắt đầu
    start_path = []
    if start_location[1] is not None:
        starting_node = start_location[1]
        start_path = [start_location[0]]
    else:
        starting_node = start_location[0]

    # Xác định điểm đích
    target_node = target_location[0]
    target_second_node = None
    if target_location[1] is not None:
        target_second_node = target_location[1]

    # Khởi tạo cấu trúc dữ liệu
    open_set = PriorityQueue()
    closed_set = set()
    expanded_nodes = [starting_node]

    # Thêm node bắt đầu vào hàng đợi ưu tiên
    # (cost, counter, node, path_so_far)
    counter = 0
    open_set.put((0, counter, starting_node, start_path))

    # Theo dõi chi phí tới mỗi node
    cost_so_far = {starting_node: 0}

    while not open_set.empty():
        # Lấy node có chi phí thấp nhất
        cost, _, current, path = open_set.get()

        # Kiểm tra đích
        if current == target_node:
            final_path = path + [current]
            if target_second_node is not None and target_second_node not in final_path:
                final_path.append(target_second_node)
            return PathfindingResult(final_path, expanded_nodes)

        if target_second_node and current == target_second_node:
            final_path = path + [current]
            if target_node not in final_path:
                final_path.append(target_node)
            return PathfindingResult(final_path, expanded_nodes)

        # Bỏ qua nếu đã xét
        if current in closed_set:
            continue

        # Đánh dấu đã xét
        closed_set.add(current)

        # Xét các node kề
        for neighbor, edge_cost in current.neighbors.values():
            if neighbor in closed_set:
                continue

            # Tính tổng chi phí mới
            new_cost = cost + edge_cost

            # Nếu đường đi mới tốt hơn
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost

                # Thêm vào expanded_nodes nếu chưa có
                if neighbor not in expanded_nodes:
                    expanded_nodes.append(neighbor)

                # Thêm vào queue
                counter += 1
                open_set.put((new_cost, counter, neighbor, path + [current]))

    # Không tìm thấy đường đi
    return PathfindingResult(start_path, expanded_nodes)

assert isinstance(ucs_pathfinder, Pathfinder)
