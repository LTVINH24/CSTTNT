"""
Level demonstrating the Orange Ghost using Uniform Cost Search algorithm.

This level showcases the Uniform Cost Search pathfinding algorithm implemented
for the Orange Ghost (Clyde) to chase Pac-Man in an optimal way.
"""
import sys
import random
from collections.abc import Iterable, Generator
from time import time_ns
import heapq  # For priority queue in UCS implementation

import pygame as pg
# pylint: disable=no-name-in-module
from pygame.locals import QUIT
# pylint: enable=no-name-in-module

from src.maze import (
    MazeCoord,
    MazeLevel, set_up_level, render_maze_level
)
from src.pathfinding import PathDispatcher
from src.pathfinding.uniform_cost_search import uniform_cost_search
from src.constant import TILE_SIZE
from src.ghost import Ghost, GHOST_TYPES
from src.player import Player

# Constants
NUMBER_OF_GHOSTS = 1
INITIAL_SPEED_MULTIPLIER = 4  # initial speed multiplier for the ghosts
BASE_SPEED = TILE_SIZE * INITIAL_SPEED_MULTIPLIER  # base speed in pixels per second
ARBITARY_SCREEN_SIZES = (800, 600)  # arbitrary screen sizes for the maze layout
LEVEL = 1  # use level 1 for testing

def get_manhattan_distance(pos1, pos2):
    """Calculate Manhattan distance between two positions"""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def custom_ucs_orange_ghost(start_node, goal_node, graph):
    """
    Custom Uniform Cost Search implementation specifically for Orange Ghost behavior
    
    The Orange Ghost (Clyde) should:
    1. Chase Pac-Man directly when far away (using UCS)
    2. Try to avoid Pac-Man when too close (scatter behavior)
    """
    if not start_node or not goal_node:
        print("Warning: Invalid start or goal node for UCS")
        return []
        
    print(f"Running custom UCS from {start_node} to {goal_node}")
    
    # Calculate Manhattan distance between start and goal
    start_pos = start_node.pos.rect.center if hasattr(start_node, 'pos') else (0, 0)
    goal_pos = goal_node.pos.rect.center if hasattr(goal_node, 'pos') else (0, 0)
    distance_to_pacman = get_manhattan_distance(start_pos, goal_pos)
    
    # If ghost is too close to Pac-Man (scatter mode threshold), 
    # find an alternative target to create scatter behavior
    SCATTER_THRESHOLD = TILE_SIZE * 8  # 8 tiles away
    if distance_to_pacman < SCATTER_THRESHOLD:
        print(f"Orange ghost too close to Pac-Man ({distance_to_pacman} < {SCATTER_THRESHOLD}), entering scatter mode")
        # Use bottom-left corner of maze as scatter target when too close
        scatter_nodes = [node for node in graph if hasattr(node, 'pos')]
        if scatter_nodes:
            # Find node furthest from Pac-Man (bottom-left area preferred)
            scatter_target = max(scatter_nodes, 
                key=lambda n: get_manhattan_distance(n.pos.rect.center, goal_pos))
            print(f"Scatter target: {scatter_target}")
            goal_node = scatter_target
    
    # Use standard UCS to find path to target
    return uniform_cost_search(start_node, goal_node, graph)

def safe_request_new_path(ghost, path_dispatcher):
    """
    A safer version of halt_current_and_request_new_path that handles
    different types of path objects
    """
    # Check if path is a list or a MazeNode
    if not hasattr(ghost, 'path') or not ghost.path:
        print("Ghost has no path to follow.")
        return
        
    if isinstance(ghost.path, list):
        if len(ghost.path) > 0:
            # Normal case - path is a list with at least one node
            first_node = ghost.path[0]
            second_node = ghost.path[1] if len(ghost.path) > 1 else None
            path_dispatcher.receive_request_for(
                ghost,
                (first_node, second_node)
            )
    else:
        # Path is a single MazeNode (non-list)
        path_dispatcher.receive_request_for(
            ghost,
            (ghost.path, None)
        )

def smooth_move_towards(ghost, target_pos, seconds, speed_factor=1.0):
    """
    Di chuyển ma một cách mượt mà đến vị trí mục tiêu
    """
    # Tính hướng di chuyển
    direction_x = target_pos[0] - ghost.rect.centerx
    direction_y = target_pos[1] - ghost.rect.centery
    distance = (direction_x**2 + direction_y**2)**0.5
    
    # Nếu đã gần đến mục tiêu, không cần di chuyển thêm
    if distance < 2:
        return False
    
    # Chuẩn hóa hướng di chuyển
    if distance > 0:
        direction_x /= distance
        direction_y /= distance
    
    # Cập nhật hướng di chuyển cho ghost
    ghost.direction = pg.Vector2(direction_x, direction_y)
    
    # Tính toán khoảng cách di chuyển trong frame này
    move_distance = min(distance, ghost.speed * speed_factor * seconds)
    
    # Di chuyển theo hướng đã tính
    ghost.rect.centerx += direction_x * move_distance
    ghost.rect.centery += direction_y * move_distance
    
    return True

def setup_orange_ghost(
        ghost_group: pg.sprite.Group,
        spawn_points: list[MazeCoord],
        path_dispatcher: PathDispatcher = None,
    ) -> Ghost:
    """
    Set up a single Orange ghost (Clyde) using the first spawn point.
    """
    if not spawn_points:
        print("Warning: No spawn points available for the Orange ghost.")
        return None
        
    # Use the second spawn point if available to avoid starting with Pacman
    spawn_point = spawn_points[1] if len(spawn_points) > 1 else spawn_points[0]
    
    try:
        # Ensure spawn position aligns with the grid
        spawn_point_x = (spawn_point.rect.x // TILE_SIZE) * TILE_SIZE
        spawn_point_y = (spawn_point.rect.y // TILE_SIZE) * TILE_SIZE
        
        # Update the spawn point position
        spawn_point.rect.topleft = (spawn_point_x, spawn_point_y)
        
        # Create the Orange ghost (Clyde) with adjusted parameters
        ghost = Ghost(
            initial_position=spawn_point,
            speed=BASE_SPEED * 0.6,  # Giảm tốc độ xuống 60% để di chuyển mượt mà hơn
            ghost_type="clyde", 
            ghost_group=ghost_group,
            path_dispatcher=path_dispatcher,
        )
        
        # Initialize tracking attributes directly
        ghost._last_positions = []
        ghost._stuck_count = 0
        ghost._path_history = []  # Add path history tracking
        ghost._alternative_path_active = False
        ghost._scatter_mode = False  # Track if currently in scatter mode
        ghost._chase_mode_timer = 0  # Timer to alternate between chase/scatter
        ghost._current_target_node = None  # Node đang hướng tới
        ghost._path_progress = 0  # Tiến trình trên đường đi hiện tại
        
        # Add attributes for better wall collision handling
        if hasattr(ghost, 'collision_tolerance'):
            ghost.collision_tolerance = TILE_SIZE / 2.5  # Increase movement tolerance
        
        # Make sure ghost has a direction attribute
        if not hasattr(ghost, 'direction') or ghost.direction is None:
            ghost.direction = pg.Vector2(1, 0)  # Default direction (right)
        
        # Add ability for Orange ghost to periodically recalculate path
        ghost._path_recalc_timer = 0
        
        # Ghi đè phương thức update của ghost để sử dụng di chuyển mượt mà
        original_update = ghost.update
        
        def smooth_update(seconds):
            # Gọi phương thức update gốc
            original_update(seconds)
            
            # Di chuyển mượt mà theo đường đi
            if hasattr(ghost, 'path') and ghost.path and isinstance(ghost.path, list) and len(ghost.path) > 0:
                # Nếu chưa có node mục tiêu hoặc đã đến gần node hiện tại
                if (ghost._current_target_node is None or 
                    pg.Vector2(ghost.rect.center).distance_to(
                        pg.Vector2(ghost._current_target_node.pos.rect.center)
                    ) < TILE_SIZE/2):
                    
                    # Thử lấy node tiếp theo trong đường đi
                    ghost._path_progress += 1
                    if ghost._path_progress < len(ghost.path):
                        # Cập nhật node mục tiêu mới
                        next_node = ghost.path[ghost._path_progress]
                        if hasattr(next_node, 'pos') and hasattr(next_node.pos, 'rect'):
                            ghost._current_target_node = next_node
                        else:
                            # Nếu node không hợp lệ, reset lại tiến trình
                            ghost._path_progress = 0
                            if len(ghost.path) > 0 and hasattr(ghost.path[0], 'pos'):
                                ghost._current_target_node = ghost.path[0]
                    else:
                        # Đã đi hết đường, yêu cầu đường đi mới
                        ghost._path_progress = 0
                        if len(ghost.path) > 0:
                            ghost._current_target_node = ghost.path[0]
                
                # Di chuyển đến node mục tiêu hiện tại
                if ghost._current_target_node and hasattr(ghost._current_target_node, 'pos'):
                    target_pos = ghost._current_target_node.pos.rect.center
                    smooth_move_towards(ghost, target_pos, seconds, 1.0)
        
        # Gán phương thức update mới
        ghost.update = smooth_update
        
        # Tạo phương thức di chuyển mới
        def move_along_path(seconds):
            if hasattr(ghost, 'path') and ghost.path and len(ghost.path) > 0:
                # Bắt đầu từ node đầu tiên nếu chưa có tiến trình
                if ghost._path_progress >= len(ghost.path):
                    ghost._path_progress = 0
                
                if ghost._path_progress < len(ghost.path):
                    current_node = ghost.path[ghost._path_progress]
                    if hasattr(current_node, 'pos'):
                        target = current_node.pos.rect.center
                        # Di chuyển đến node hiện tại
                        moved = smooth_move_towards(ghost, target, seconds)
                        
                        # Nếu đã gần đến node, chuyển sang node tiếp theo
                        if not moved:
                            ghost._path_progress += 1
        
        # Gán phương thức di chuyển mới
        ghost.move_along_path = move_along_path
            
        print(f"Created Orange ghost at position {spawn_point.rect.topleft}")
        return ghost
    except Exception as e:
        print(f"Error setting up ghost: {e}")
        return None

def is_colliding_with_wall(sprite, maze_layout):
    """
    Check if a sprite is colliding with any walls in the maze layout
    """
    # Use MazePart to identify walls in the maze layout
    from src.maze.maze_parts import MazePart
    
    # Get the maze parts array
    maze_parts = maze_layout.maze_parts
    maze_shape = maze_layout.maze_shape()
    tile_size = TILE_SIZE
    
    # Get the offset from the maze coordinates
    from src.maze.maze_coord import MazeCoord
    offset_x, offset_y = MazeCoord.maze_offset
    
    # Calculate which tiles the sprite's rect is overlapping
    sprite_left = max(0, (sprite.rect.left - offset_x) // tile_size)
    sprite_right = min(maze_shape[0] - 1, (sprite.rect.right - 1 - offset_x) // tile_size)
    sprite_top = max(0, (sprite.rect.top - offset_y) // tile_size)
    sprite_bottom = min(maze_shape[1] - 1, (sprite.rect.bottom - 1 - offset_y) // tile_size)
    
    # Check all tiles the sprite is overlapping
    for y in range(sprite_top, sprite_bottom + 1):
        for x in range(sprite_left, sprite_right + 1):
            try:
                # If this tile is a wall, there's a collision
                if maze_parts[y, x] == MazePart.WALL:
                    return True
            except IndexError:
                # If we're somehow out of bounds, consider it a wall
                return True
                
    return False

def change_ghost_direction(ghost, maze_layout):
    """
    Change the ghost's direction when it hits a wall, using a logical approach
    """
    # First, try to determine the current direction if it exists
    current_direction = None
    if hasattr(ghost, 'direction') and ghost.direction:
        current_direction = ghost.direction
        
    # Create prioritized directions based on current direction
    directions = get_prioritized_directions(current_direction)
    
    # Save current position
    old_pos = ghost.rect.topleft
    
    # Try each direction in priority order
    for dx, dy in directions:
        # Move a little bit to check if this direction works
        test_distance = 10
        ghost.rect.move_ip(dx*test_distance, dy*test_distance)
        
        # If this direction doesn't hit a wall, use it
        if not is_colliding_with_wall(ghost, maze_layout):
            # Set the new direction
            if hasattr(ghost, 'direction'):
                ghost.direction = pg.Vector2(dx, dy).normalize()
                print(f"Wall collision detected! Changed direction to {ghost.direction}")
                return True
        
        # Move back to original position
        ghost.rect.topleft = old_pos
    
    # If all directions have walls, no change
    return False

def get_prioritized_directions(current_direction=None):
    """
    Get a list of directions prioritized based on the current direction
    
    1. Continue in same direction if possible
    2. Try perpendicular directions (90° turns)
    3. Use reverse direction as last resort
    """
    # Default directions in priority order
    directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # right, down, left, up
    
    if current_direction is None:
        return directions
    
    # Normalize current direction to get primary direction
    dx = 1 if current_direction.x > 0 else (-1 if current_direction.x < 0 else 0)
    dy = 1 if current_direction.y > 0 else (-1 if current_direction.y < 0 else 0)
    
    # Current direction has highest priority
    prioritized = [(dx, dy)]
    
    # Add perpendicular directions (90° turns)
    if dx != 0:  # If moving horizontally
        prioritized.append((0, 1))   # try down
        prioritized.append((0, -1))  # try up
    else:  # If moving vertically
        prioritized.append((1, 0))   # try right 
        prioritized.append((-1, 0))  # try left
    
    # Add reverse direction as last resort
    prioritized.append((-dx, -dy))
    
    return prioritized

def move_ghost_to_node(ghost, maze_layout, node=None):
    """
    Forcefully move the ghost to a valid node to escape being stuck
    """
    from src.maze.maze_parts import MazePart
    
    # If a specific node is provided, move there directly
    if node is not None:
        print(f"Moving ghost to specific node at {node.pos.rect.center}")
        ghost.rect.center = node.pos.rect.center
        return True
    
    # Otherwise, find a nearby valid position (empty space)
    maze_parts = maze_layout.maze_parts
    maze_shape = maze_layout.maze_shape()
    from src.maze.maze_coord import MazeCoord
    
    # Get current ghost position in tile coordinates
    ghost_center_x = ghost.rect.centerx
    ghost_center_y = ghost.rect.centery
    offset_x, offset_y = MazeCoord.maze_offset
    
    current_tile_x = (ghost_center_x - offset_x) // TILE_SIZE
    current_tile_y = (ghost_center_y - offset_y) // TILE_SIZE
    
    # Check surrounding tiles in expanding squares
    for distance in range(1, 5):  # Try up to 4 tiles away
        for y_offset in range(-distance, distance + 1):
            for x_offset in range(-distance, distance + 1):
                # Only check the perimeter of the square
                if abs(y_offset) != distance and abs(x_offset) != distance:
                    continue
                    
                check_x = current_tile_x + x_offset
                check_y = current_tile_y + y_offset
                
                # Check if this tile is valid and not a wall
                if (0 <= check_x < maze_shape[0] and 
                    0 <= check_y < maze_shape[1] and
                    maze_parts[check_y, check_x] != MazePart.WALL):
                    
                    # Found a valid tile, move the ghost there
                    new_x = check_x * TILE_SIZE + TILE_SIZE // 2 + offset_x
                    new_y = check_y * TILE_SIZE + TILE_SIZE // 2 + offset_y
                    print(f"Emergency relocation: Moving ghost to ({new_x}, {new_y})")
                    ghost.rect.center = (new_x, new_y)
                    return True
                    
    print("Warning: Could not find any valid position to move ghost to")
    return False

def find_alternative_path_nodes(ghost, maze_layout):
    """
    Find alternative nodes to navigate to when the ghost is stuck
    """
    # Get all nodes in the maze graph
    all_nodes = list(maze_layout.maze_graph)
    if not all_nodes:
        return None, None
        
    # Get current position
    current_pos = ghost.rect.center
    
    # Sort nodes by distance to the ghost (excluding current node)
    nearby_nodes = sorted(
        [node for node in all_nodes if node.pos.rect.center != current_pos],
        key=lambda node: ((node.pos.rect.centerx - current_pos[0])**2 + 
                         (node.pos.rect.centery - current_pos[1])**2)
    )
    
    # Get the closest and a random distant node
    closest_node = nearby_nodes[0] if nearby_nodes else None
    
    # Get a node that's further away (20% through the list) to encourage exploration
    distant_idx = min(int(len(nearby_nodes) * 0.2) + 1, len(nearby_nodes) - 1)
    distant_node = nearby_nodes[distant_idx] if distant_idx < len(nearby_nodes) else None
    
    print(f"Found alternative nodes: closest={closest_node}, distant={distant_node}")
    return closest_node, distant_node

def run_level():
    """
    Run the maze level with an Orange Ghost using UCS pathfinding.
    """
    # Ensure we have the random module available in this scope
    import random as random_module

    # pygame setup
    # pylint: disable=no-member
    pg.init()
    # pylint: enable=no-member
    screen_sizes = ARBITARY_SCREEN_SIZES
    screen = pg.display.set_mode(screen_sizes)
    pg.display.set_caption("Orange Ghost with Uniform Cost Search")
    clock = pg.time.Clock()

    # maze level setup
    maze_level: MazeLevel = set_up_level(
        screen=screen,
        level=LEVEL,
    )

    # pacman setup with random spawn point
    pacman_position = random_module.choice(maze_level.spawn_points).rect.topleft
    pacman = Player(
        initial_position=pacman_position,
        speed=BASE_SPEED,
    )
    pacman_group = pg.sprite.GroupSingle(pacman)

    # Set up path dispatcher with custom UCS pathfinder for Orange Ghost
    path_dispatcher = PathDispatcher(
        maze_layout=maze_level.maze_layout,
        player=pacman,
        pathfinder=custom_ucs_orange_ghost,  # Use our custom UCS algorithm for Orange Ghost
    )

    try:
        # Force the ghost to be Orange (Clyde)
        orange_ghost = setup_orange_ghost(
            ghost_group=maze_level.ghosts,
            spawn_points=maze_level.spawn_points,
            path_dispatcher=path_dispatcher,
        )
        
        if orange_ghost is None:
            print("Failed to create Orange ghost. Exiting.")
            return
            
    except Exception as e:
        print(f"Error in run_level: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Track player's last position to detect movement
    last_pacman_pos = pacman.rect.topleft
    last_path_update_time = 0
    stuck_time = 0
    # Main game loop
    last_debug_time = 0
    while True:
        for event in pg.event.get():
            if event.type == QUIT:
                sys.exit()

        delta_time = clock.tick(60)  # in ms
        seconds = delta_time / 1000.0  # Convert to seconds for sprite updates
        current_time = pg.time.get_ticks()

        # Get keyboard input for Pacman
        keys = pg.key.get_pressed()
        pacman.move_by_arrow_keys(keys)
        pacman_group.update(seconds)

        # Check if Pacman has moved since last frame
        current_pacman_pos = pacman.rect.topleft
        pacman_moved = current_pacman_pos != last_pacman_pos
        
        # Force path update in these cases:
        # 1. Pacman has moved
        # 2. It's been more than 70ms since last update
        if pacman_moved or (current_time - last_path_update_time > 70):
            # Trigger path recalculation
            path_dispatcher.update(dt=delta_time * 2)
            last_path_update_time = current_time
            
            if len(maze_level.ghosts) > 0:
                ghost = maze_level.ghosts.sprites()[0]
                
                # Initialize tracking attributes if needed
                if not hasattr(ghost, '_last_positions'):
                    ghost._last_positions = []
                    
                if not hasattr(ghost, '_stuck_count'):
                    ghost._stuck_count = 0
                    
                if not hasattr(ghost, '_path_history'):
                    ghost._path_history = []
                    
                if not hasattr(ghost, '_alternative_path_active'):
                    ghost._alternative_path_active = False
                
                # Add current position to history
                ghost._last_positions.append(ghost.rect.topleft)
                
                # Keep only the 10 most recent positions
                if len(ghost._last_positions) > 10:
                    ghost._last_positions.pop(0)
                
                # Keep track of the current path
                if hasattr(ghost, 'path') and ghost.path:
                    current_path = ghost.path
                    # Store simplified path representation
                    path_repr = [node.pos.rect.center if hasattr(node, 'pos') else str(node) 
                                 for node in current_path] if isinstance(current_path, list) else str(current_path)
                    
                    # Add to path history
                    ghost._path_history.append(path_repr)
                    # Keep last 5 paths
                    if len(ghost._path_history) > 5:
                        ghost._path_history.pop(0)
                
                # Initialize stuck status
                stuck = False
                    
                # Check if ghost is stuck (hasn't moved in 5 frames)
                if len(ghost._last_positions) >= 5:
                    stuck = all(pos == ghost._last_positions[-1] for pos in ghost._last_positions[-5:])
                    if stuck:
                        print("Ghost is stuck! Trying to find new path...")
                        ghost._stuck_count += 1
                        stuck_time += delta_time
                        
                        # First attempt: force path recalculation
                        path_dispatcher.update(dt=delta_time * 20)
                        
                        # Print the current path for debugging
                        if hasattr(ghost, 'path') and ghost.path:
                            if isinstance(ghost.path, list) and ghost.path:
                                print(f"Current path: {[node for node in ghost.path]}")
                            else:
                                print(f"Current path (not a list): {ghost.path}")
                        
                        # Check for path repetition/cycling
                        path_cycling = False
                        if len(ghost._path_history) >= 3:
                            # Check if the last 3 paths are the same
                            path_cycling = ghost._path_history[-1] == ghost._path_history[-2] == ghost._path_history[-3]
                            if path_cycling:
                                print("Ghost is cycling through the same path repeatedly!")
                        
                        # Try to get a new path - with more aggressive changes if cycling detected
                        if path_cycling or ghost._stuck_count >= 3:
                            # Try to find alternative nodes to target
                            closest_node, distant_node = find_alternative_path_nodes(ghost, maze_level.maze_layout)
                            
                            if distant_node and not ghost._alternative_path_active:
                                print(f"Attempting alternative path to distant node: {distant_node}")
                                # Manually set the ghost's target to this node
                                if hasattr(ghost, 'set_target') and callable(ghost.set_target):
                                    ghost.set_target(distant_node.pos.rect.center)
                                    ghost._alternative_path_active = True
                                else:
                                    # Try direct teleport if can't set target
                                    move_ghost_to_node(ghost, maze_level.maze_layout, distant_node)
                            else:
                                # Standard path request
                                try:
                                    safe_request_new_path(ghost, path_dispatcher)
                                except Exception as e:
                                    print(f"Error requesting new path: {e}")
                        else:
                            # Standard path request for less serious stuck situations
                            try:
                                safe_request_new_path(ghost, path_dispatcher)
                            except Exception as e:
                                print(f"Error requesting new path: {e}")
                        
                        # For persistent stuck situations
                        if ghost._stuck_count >= 5 or stuck_time > 5000:  # 5 stuck detections or 5 seconds
                            print(f"Ghost stuck too long! Emergency measures (stuck count: {ghost._stuck_count}, time: {stuck_time}ms)")
                            # Reset counters
                            ghost._stuck_count = 0
                            stuck_time = 0
                            ghost._alternative_path_active = False
                            
                            # More aggressive approach:
                            # 1. Try to change direction using wall avoidance
                            if change_ghost_direction(ghost, maze_level.maze_layout):
                                print("Changed ghost direction successfully")
                                ghost._last_positions = []
                            
                            # 2. If wall avoidance doesn't work, try to find a path node to teleport to
                            else:
                                # Get a random node from the maze graph to teleport to
                                valid_nodes = [node for node in maze_level.maze_layout.maze_graph 
                                             if node.pos.rect.center != ghost.rect.center]
                                
                                if valid_nodes:
                                    # Move to a random valid node
                                    target_node = random_module.choice(valid_nodes)
                                    print(f"Teleporting ghost to node {target_node}")
                                    move_ghost_to_node(ghost, maze_level.maze_layout, target_node)
                                    ghost._last_positions = []
                                    # Force a new path calculation after teleport
                                    path_dispatcher.update(dt=delta_time * 50)
                                else:
                                    # As a last resort, try to find any valid position
                                    move_ghost_to_node(ghost, maze_level.maze_layout)
                                    ghost._last_positions = []
                    else:
                        # Not stuck, reset counters
                        ghost._stuck_count = max(0, ghost._stuck_count - 0.2)  # Gradually decrease stuck count
                        stuck_time = max(0, stuck_time - delta_time/2)  # Gradually decrease stuck time
                        
                        # Reset alternative path flag if we're moving normally
                        if ghost._alternative_path_active and ghost._stuck_count < 1:
                            ghost._alternative_path_active = False
                
                # Update chase/scatter mode timer for Orange ghost behavior
                ghost._chase_mode_timer += delta_time
                
                # Switch behavior every 10 seconds (Orange ghost characteristic)
                if ghost._chase_mode_timer > 10000:  # 10 seconds
                    ghost._scatter_mode = not ghost._scatter_mode
                    ghost._chase_mode_timer = 0
                    print(f"Orange ghost behavior switched to: {'scatter' if ghost._scatter_mode else 'chase'}")
                
                # Force path recalculation every 2 seconds to adapt to Pac-Man movement
                ghost._path_recalc_timer += delta_time
                if ghost._path_recalc_timer > 2000:  # 2 seconds
                    ghost._path_recalc_timer = 0
                    # Force new path calculation
                    try:
                        safe_request_new_path(ghost, path_dispatcher)
                    except Exception as e:
                        print(f"Error in periodic path recalculation: {e}")
                        
                # Reset position history after processing
                if stuck or pacman_moved:
                    ghost._last_positions = []
                        
            last_pacman_pos = current_pacman_pos

        # Refresh the screen
        screen.fill((0, 0, 0))

        # Update ghosts with the new paths
        if len(maze_level.ghosts) > 0:
            ghost = maze_level.ghosts.sprites()[0]
            
            # Sử dụng phương thức di chuyển mượt mà thay vì update thông thường
            if hasattr(ghost, 'move_along_path'):
                ghost.move_along_path(seconds)
            else:
                ghost.update(seconds)
            
            # Store current position
            current_ghost_pos = ghost.rect.topleft
            
            # Calculate distance to Pacman for dynamic behavior adjustment
            pacman_pos = pacman.rect.center
            ghost_pos = ghost.rect.center
            distance_to_pacman = get_manhattan_distance(pacman_pos, ghost_pos)
            
            # Orange ghost should move more cautiously when close to Pac-Man
            if distance_to_pacman < TILE_SIZE * 5:  # Within 5 tiles
                # Be more careful with movement when close to Pac-Man
                careful_factor = 0.8
                # Slow down slightly to avoid overshooting turns
                if hasattr(ghost, 'speed_multiplier'):
                    ghost.speed_multiplier = careful_factor
            else:
                # Normal speed when far from Pac-Man
                if hasattr(ghost, 'speed_multiplier'):
                    ghost.speed_multiplier = 1.0
            
            # Check for wall collisions while moving
            if hasattr(ghost, 'direction') and ghost.direction:
                # Test movement in current direction
                test_distance = 5
                test_dx = ghost.direction.x * test_distance
                test_dy = ghost.direction.y * test_distance
                ghost.rect.move_ip(test_dx, test_dy)
                
                # If wall collision detected, change direction logically
                if is_colliding_with_wall(ghost, maze_level.maze_layout):
                    # Move back to original position
                    ghost.rect.topleft = current_ghost_pos
                    # Find a new direction using our logical approach
                    change_ghost_direction(ghost, maze_level.maze_layout)
                    # Reset path progress to recalculate path
                    ghost._path_progress = 0
                    if hasattr(ghost, 'path') and ghost.path and len(ghost.path) > 0:
                        ghost._current_target_node = ghost.path[0]
                else:
                    # No collision, move back to original position
                    ghost.rect.topleft = current_ghost_pos
        else:
            # Update ghosts with the standard method if no Orange ghost
            maze_level.ghosts.update(seconds)

        # Render the maze level and all entities
        render_maze_level(
            maze_level=maze_level,
            screen=screen,
            dt=delta_time,
        )
        
        # Draw Pacman to the screen
        pacman_group.draw(screen)
        
        # Update the screen display
        pg.display.flip()


if __name__ == "__main__":
    run_level()