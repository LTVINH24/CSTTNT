"""
Uniform Cost Search pathfinding algorithm implementation for Pac-Man ghost movement.
"""
import heapq
from typing import Dict, List, Set, Tuple

from src.maze import MazeNode
from .pathfinder import Pathfinder, PathfindingResult
from .pathfinding_monitor import pathfinding_monitor

@pathfinding_monitor
def uniform_cost_search(
    maze_graph: list[MazeNode],
    start_location: tuple[MazeNode, MazeNode | None],
    target_location: tuple[MazeNode, MazeNode | None],
) -> PathfindingResult:
    """
    Finds a path using Uniform Cost Search algorithm from start to target location.
    
    The Uniform Cost Search algorithm expands nodes in order of their path cost from the start.
    This ensures finding the optimal (lowest cost) path to the target.
    """
    # Extract start node - use the second node if moving between nodes
    start_node = start_location[0] if len(start_location) <= 1 or start_location[1] is None else start_location[1]
    
    # Determine target nodes (could be one or two)
    target_nodes = set()
    target_nodes.add(target_location[0])
    if target_location[1] is not None:
        target_nodes.add(target_location[1])
    
    # Initialize data structures
    frontier = [(0, id(start_node), start_node)]  # (cost, node_id for tiebreaking, node)
    came_from = {start_node: (0, [start_node])}   # node -> (cost, path to node)
    explored_nodes = []  # Track explored nodes for visualization
    
    while frontier:
        # Get node with lowest cost
        current_cost, _, current_node = heapq.heappop(frontier)
        
        # Add to explored nodes list for visualization
        explored_nodes.append(current_node)
        
        # Check if we've reached a target node
        if current_node in target_nodes:
            # Construct the full path including start_location
            full_path = []
            
            # Add the start_location to the path
            if start_location[0] != start_node:
                full_path.append(start_location[0])
            
            # Add the path found by UCS
            full_path.extend(came_from[current_node][1])
            
            return PathfindingResult(full_path, explored_nodes)
        
        # Explore all neighboring nodes
        for direction, neighbor_data in current_node.neighbors.items():
            if neighbor_data is None:
                continue
                
            neighbor, step_cost = neighbor_data
            
            # Calculate the new cost to reach this neighbor
            new_cost = current_cost + step_cost
            
            # If we haven't visited this node or found a cheaper path
            if neighbor not in came_from or new_cost < came_from[neighbor][0]:
                # Update the cost and path
                current_path = came_from[current_node][1].copy()
                current_path.append(neighbor)
                came_from[neighbor] = (new_cost, current_path)
                
                # Add to frontier
                heapq.heappush(frontier, (new_cost, id(neighbor), neighbor))
    
    # No path found - return an empty path with explored nodes
    return PathfindingResult([], explored_nodes)

assert isinstance(uniform_cost_search, Pathfinder)