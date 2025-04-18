"""
This module implements the Breadth-First Search (BFS) algorithm for the blue ghost.
"""

from collections import deque
from src.maze import MazeNode
from .pathfinder import Pathfinder, PathfindingResult
from .pathfinding_monitor import pathfinding_monitor

@pathfinding_monitor
def breadth_first_search_path_finder(
    _: list[MazeNode],
    start_location: tuple[MazeNode, MazeNode | None],
    target_location: tuple[MazeNode, MazeNode | None],
) -> PathfindingResult:
    """
    Finds a path in a maze graph from a start location to a target location using Breadth-First Search.

    BFS explores all neighbors at the present depth before moving on to nodes at the next depth level. 
    It uses a queue to keep track of nodes to be explored, and visits the earliest discovered node first.
    """
    # Lấy node bắt đầu và node đích
    start_first_node = start_location[0]
    start_second_node = start_location[1] if len(start_location) > 1 else None
    
    # Lấy node đích
    target_first_node = target_location[0]
    target_second_node = target_location[1] if len(target_location) > 1 else None

    print(f"Start node: {start_first_node}, Second start node: {start_second_node}")
    
    # Chọn node để chạy thuật toán BFS
    start_node = start_second_node if start_second_node is not None else start_first_node
    
    # Nếu đã ở đích, trả về cả hai node bắt đầu
    if start_node == target_first_node:
        result_path = []
        if start_first_node:
            result_path.append(start_first_node)
        if start_second_node and start_second_node != start_first_node:
            result_path.append(start_second_node)
        if target_second_node:
            result_path.append(target_second_node)
        return PathfindingResult(result_path, [start_node])

    # Khởi tạo queue và set visited cho BFS
    queue = deque([(start_node, [])])  # (node, đường đi đến node)
    visited = set()
    expanded_nodes = []

    while queue:
        current_node, path_to_current = queue.popleft()
        
        if current_node in visited:
            continue
            
        # Thêm vào danh sách đã thăm và expanded_nodes
        visited.add(current_node)
        expanded_nodes.append(current_node)
        
        # Kiểm tra xem đã đến đích chưa, kiểm tra xem nó đến target_first hay là target_second trước
        reached_target_first = (current_node == target_first_node)
        reached_target_second = (current_node == target_second_node)

        # Nếu đã đến một trong các đích
        if reached_target_first or reached_target_second:
            # Tạo đường đi từ điểm bắt đầu đến hiện tại
            temp_path = path_to_current + [current_node]
            
            # Tạo đường đi cuối cùng, luôn đảm bảo start_location[0] và start_location[1] có trong đường đi
            final_path = []
            
            # Luôn thêm start_first_node vào đầu đường đi
            if start_first_node:
                final_path.append(start_first_node)
                # Nếu node này đã có trong temp_path, loại bỏ để tránh trùng lặp
                if start_first_node in temp_path:
                    temp_path.remove(start_first_node)
            
            # Luôn thêm start_second_node nếu có
            if start_second_node and start_second_node != start_first_node:
                final_path.append(start_second_node)
                # Nếu node này đã có trong temp_path, loại bỏ để tránh trùng lặp
                if start_second_node in temp_path:
                    temp_path.remove(start_second_node)
            
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
        
        # Thêm các láng giềng vào queue
        for neighbor, _ in current_node.neighbors.values():
            if neighbor and neighbor not in visited:
                queue.append((neighbor, path_to_current + [current_node]))

    # Không tìm thấy đường đi, trả về các node bắt đầu
    result_path = []
    if start_first_node:
        result_path.append(start_first_node)
    if start_second_node and start_second_node != start_first_node:
        result_path.append(start_second_node)
        
    return PathfindingResult(result_path, expanded_nodes)

assert isinstance(breadth_first_search_path_finder, Pathfinder)