"""
This module implements the "Red Ghost" level featuring Blinky with A* pathfinding algorithm.

Blinky (the red ghost) is programmed to chase Pac-Man using the A* search algorithm,
providing an intelligent and efficient pursuit behavior.

Constants:
    INITIAL_SPEED_MULTIPLIER (int): The initial speed multiplier for Blinky.
    BASE_SPEED (int): The base speed of Blinky in pixels per second.
    ARBITARY_SCREEN_SIZES (tuple[int, int]): The screen size for the maze layout.
    LEVEL (int): The level number, used to load the corresponding maze layout file.
    MIN_SPAWN_DISTANCE (int): Minimum tile distance between Pacman and ghost spawn.

Notes:
- This implementation demonstrates the A* pathfinding algorithm with Blinky.
- The ghost will spawn randomly and actively chase Pacman using the most efficient path.
"""
import sys
import random
import time

import pygame as pg
from pygame.locals import QUIT

from src.maze import MazeLevel, set_up_level, render_maze_level, MazeCoord
from src.pathfinding import PathDispatcher, a_star_pathfinder
from src.constant import TILE_SIZE
from src.ghost import Ghost
from src.player import Player

INITIAL_SPEED_MULTIPLIER = 4  # initial speed multiplier for the ghost
BASE_SPEED = TILE_SIZE * INITIAL_SPEED_MULTIPLIER
ARBITARY_SCREEN_SIZES = (800, 600)
LEVEL = 1
MIN_SPAWN_DISTANCE = 5  # Minimum distance (in tiles) between Pacman and ghost spawn

def get_random_spawn_point(maze_level: MazeLevel, avoid_coord: MazeCoord = None) -> MazeCoord:
    # Try to access walkable nodes - try different possible attributes
    try:
        if hasattr(maze_level, 'maze_layout') and hasattr(maze_level.maze_layout, 'walkable_nodes'):
            valid_positions = maze_level.maze_layout.walkable_nodes
        elif hasattr(maze_level, 'walkable_nodes'):
            valid_positions = maze_level.walkable_nodes
        elif hasattr(maze_level, 'nodes'):
            # Filter walkable nodes
            valid_positions = [node for node in maze_level.nodes if node.walkable]
        else:
            # Fallback to spawn points
            valid_positions = maze_level.spawn_points
            print("Warning: Using spawn points as valid positions")
    except Exception as e:
        print(f"Error accessing valid positions: {e}")
        # Emergency fallback
        valid_positions = maze_level.spawn_points
    
    # Calculate Manhattan distance between two coordinates
    def calculate_distance(coord1, coord2):
        # Using rect.center instead of grid_x/grid_y
        x1, y1 = coord1.rect.center
        x2, y2 = coord2.rect.center
        # Convert to grid coordinates by dividing by TILE_SIZE
        grid_x1, grid_y1 = x1 // TILE_SIZE, y1 // TILE_SIZE
        grid_x2, grid_y2 = x2 // TILE_SIZE, y2 // TILE_SIZE
        return abs(grid_x1 - grid_x2) + abs(grid_y1 - grid_y2)
    
    # If we need to avoid a particular coordinate
    if avoid_coord:
        # Filter positions that are far enough away
        distant_positions = [
            pos for pos in valid_positions 
            if calculate_distance(pos, avoid_coord) >= MIN_SPAWN_DISTANCE
        ]
        
        # If we have distant positions, choose from them
        if distant_positions:
            return random.choice(distant_positions)
    
    # Just pick a random valid position if we don't need to avoid anything
    # or if no valid distant positions were found
    if valid_positions:
        return random.choice(valid_positions)
    
    # Ultimate fallback: use a spawn point or create one
    print("Warning: No valid positions found. Using fallback position.")
    if maze_level.spawn_points:
        return maze_level.spawn_points[0]
    else:
        raise ValueError("No valid spawn positions available!")


def check_ghost_pacman_collision(ghost: Ghost, pacman: Player) -> bool:
    # Method 1: Use built-in rect collision with a small inflation
    # Create temporary copies of the rects with slightly smaller size
    ghost_rect = ghost.rect.center
    pacman_rect = pacman.rect.center
    
   
    # Method 2: Distance-based collision as a backup
    ghost_center = ghost.rect.center
    pacman_center = pacman.rect.center
    
    # Calculate distance between centers
    dx = ghost_center[0] - pacman_center[0]
    dy = ghost_center[1] - pacman_center[1]
    distance = (dx**2 + dy**2)**0.5
    
    # Very strict threshold - require almost exact overlap
    collision_threshold = min(ghost.rect.width, pacman.rect.width) / 3.0
    
    if distance <= collision_threshold:
        print(f"Distance-based collision: {distance:.2f} <= {collision_threshold:.2f}")
        return True
    
    # No collision detected
    return False


def set_up_blinky(
        ghost_group: pg.sprite.Group,
        spawn_point: MazeCoord,
        path_dispatcher: PathDispatcher,
    ) -> Ghost:
    # Create Blinky with A* pathfinding
    blinky = Ghost(
        initial_position=spawn_point,
        speed=BASE_SPEED,
        ghost_type="blinky",  # Specifically the red ghost
        ghost_group=ghost_group,
        path_dispatcher=path_dispatcher,
    )
    
    return blinky


def run_level():
    """
    Run the maze level with Blinky using A* pathfinding.
    """
    # pygame setup
    pg.init()
    screen_sizes = ARBITARY_SCREEN_SIZES
    screen = pg.display.set_mode(screen_sizes)
    pg.display.set_caption("Blinky with A* Search - Random Spawns")
    clock = pg.time.Clock()

    # maze level setup
    maze_level = set_up_level(screen=screen, level=LEVEL)

    # Ensure we have at least one spawn point for fallback
    if not maze_level.spawn_points:
        print("Warning: No spawn points found. Adding default spawn point.")
        if hasattr(maze_level, 'maze_layout') and hasattr(maze_level.maze_layout, 'nodes'):
            maze_level.spawn_points = [maze_level.maze_layout.nodes[0]]
        else:
            print("Error: Cannot create default spawn point. Game may crash.")
    
    # Get random spawn point for Pacman
    pacman_spawn = get_random_spawn_point(maze_level)
    pacman_position = pacman_spawn.rect.topleft
    pacman = Player(initial_position=pacman_position, speed=BASE_SPEED)
    pacman_group = pg.sprite.GroupSingle(pacman)

    # Setup path dispatcher with A* pathfinding algorithm
    path_dispatcher = PathDispatcher(
        maze_layout=maze_level.maze_layout,
        player=pacman,
        pathfinder=a_star_pathfinder,  # Using A* for intelligent chasing
    )
    
    # Get random spawn point for Blinky, away from Pacman
    ghost_spawn = get_random_spawn_point(maze_level, avoid_coord=pacman_spawn)
    print(f"Pacman spawned at {pacman_spawn.rect.center}")
    print(f"Blinky spawned at {ghost_spawn.rect.center}")
    
    # Set up Blinky with the random spawn point
    blinky = set_up_blinky(
        ghost_group=maze_level.ghosts,
        spawn_point=ghost_spawn,
        path_dispatcher=path_dispatcher,
    )

    # Game state variables
    game_over = False
    font = pg.font.Font(None, 36)  # Default font, size 36
    small_font = pg.font.Font(None, 24)  # Smaller font for instructions
    
    # Game start time for tracking survival duration
    start_time = time.time()
    survival_time = 0

    # Track ghost movement time
    last_move_time = time.time()
    stuck_time_limit = 5  # Seconds before ghost is considered stuck
    
    # Game loop
    while True:
        # Handle events
        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                sys.exit()
            
            # Handle restart when game is over
            if game_over and event.type == pg.KEYDOWN:
                if event.key == pg.K_r:  # Press 'R' to restart
                    return run_level()  # Restart the level
                elif event.key == pg.K_ESCAPE:  # Press ESC to exit
                    pg.quit()
                    sys.exit()

        # Get delta time in milliseconds
        delta_time = clock.tick(60)
        
        # Update game state only if game is not over
        if not game_over:
            # Update survival time
            survival_time = time.time() - start_time
            # Update Pacman
            pacman.update(survival_time)
            
            # Update ghost pathfinding
            path_dispatcher.update(dt=survival_time)

            # If the ghost hasn't moved for too long, consider it stuck
            if time.time() - last_move_time > stuck_time_limit:
                print("Ghost is stuck!")
                game_over = True
                print(f"Game Over: Ghost got stuck after {survival_time:.1f} seconds!")
                break
            
            # Update last move time if ghost has moved
            last_move_time = time.time()  # Update the last move time when ghost moves
            
            # Check for collision between Blinky and Pacman
            if check_ghost_pacman_collision(blinky, pacman):
                game_over = True
                print(f"Game Over: Blinky caught Pacman after {survival_time:.1f} seconds!")
                break
        
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Update and render maze level
        render_maze_level(maze_level=maze_level, screen=screen, dt=delta_time)
        
        # Draw Pacman
        pacman_group.draw(screen)
        
        # Display timer in top-left corner if game is running
        if not game_over:
            timer_text = small_font.render(f"Time: {survival_time:.1f}s", True, (255, 255, 255))
            screen.blit(timer_text, (10, 10))
            
        
        # Display game over screen if needed
        if game_over:
            print("Game Over!")
            break
        
        # Display game
        pg.display.flip()


if __name__ == "__main__":
    run_level()
