"""
This module implements the Breadth-First Search (BFS) algorithm for the blue ghost.
"""

from collections import deque
import time
import tracemalloc
from src.maze import MazeNode
from src.maze import MazeDirection
from .pathfinder import Pathfinder, PathfindingResult
from .pathfinding_monitor import pathfinding_monitor

@pathfinding_monitor
def breadth_first_search_path_finder(
    maze_graph: list[MazeNode],
    start_location: tuple[MazeNode, MazeNode | None],
    target_location: tuple[MazeNode, MazeNode | None],
) -> PathfindingResult:
    """
    Finds a path in a maze graph from a start location to a target location using Breadth-First Search.

    BFS explores all neighbors at the present depth before moving on to nodes at the next depth level. 
    It uses a queue to keep track of nodes to be explored, and visits the earliest discovered node first.
    """
    # Bắt đầu theo dõi bộ nhớ và thời gian
    tracemalloc.start()
    start_time = time.time()

    start_path = []
    
    if len(start_location) > 1 and start_location[1] is not None:
        starting_node = start_location[1]
        start_path = [start_location[0]]
    else:
        starting_node = start_location[0]
    
    target_node = target_location[0]
    target_second_node = None
    if len(target_location) > 1 and target_location[1] is not None:
        target_second_node = target_location[1]

    # Kiểm tra nếu đã ở đích
    if starting_node == target_node:
        final_path = start_path + [starting_node]
        if target_second_node is not None and target_second_node not in final_path:
            final_path.append(target_second_node)
            
        # Lấy thông tin bộ nhớ và thời gian
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end_time = time.time()
        
        # Lưu thống kê
        breadth_first_search_path_finder.last_stats = {
            'search_time': end_time - start_time,
            'memory_peak': peak,
            'expanded_nodes': 1
        }
        
        return PathfindingResult(final_path, [starting_node])

    queue = deque([(starting_node, start_path)])
    visited = set()
    expanded_nodes = []

    while queue:
        current_node, path = queue.popleft()
        if current_node == target_node:
            final_path = path + [current_node]
            
            if target_second_node is not None and target_second_node not in final_path:
                final_path.append(target_second_node)
                
            # Lấy thông tin bộ nhớ và thời gian
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            end_time = time.time()
            
            # Lưu thống kê
            breadth_first_search_path_finder.last_stats = {
                'search_time': end_time - start_time,
                'memory_peak': peak,
                'expanded_nodes': len(expanded_nodes)
            }
            
            return PathfindingResult(final_path, expanded_nodes)
        
        if current_node not in visited:
            visited.add(current_node)
            expanded_nodes.append(current_node)
            
            for neighbor, _ in current_node.neighbors.values():
                if neighbor not in visited:
                    queue.append((neighbor, path + [current_node]))

    # Nếu không tìm được đường đi
    # Lấy thông tin bộ nhớ và thời gian
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    end_time = time.time()
    
    # Lưu thống kê
    breadth_first_search_path_finder.last_stats = {
        'search_time': end_time - start_time,
        'memory_peak': peak,
        'expanded_nodes': len(expanded_nodes)
    }

    return PathfindingResult([], expanded_nodes)

assert isinstance(breadth_first_search_path_finder, Pathfinder)