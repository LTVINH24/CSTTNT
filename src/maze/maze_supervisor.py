""" SUPERVISOR FOR MAZE LEVELS """
from dataclasses import dataclass, field

import pygame as pg

from .maze_coord import MazeCoord
from .maze_builder import load_maze, build_maze
from .maze_layout import MazeLayout
from .maze_parts import MazePart

@dataclass
class MazeLevel:
    """
    Represents a level in the maze game, including its layout, spawn points, and entities.
    Attributes:
        level (int): The current level number.
        maze_layout (MazeLayout): The layout of the maze for this level.
        spawn_points (list[MazeCoord]): A list of coordinates where entities can spawn.
        ghosts (pg.sprite.Group): A group of ghost sprites present in the level.
        pacman (pg.sprite.Sprite | None): The Pacman sprite for this level, if present.
    """
    level: int
    maze_layout: MazeLayout
    spawn_points: list[MazeCoord]
    player_spawn_points: list[MazeCoord]

    ghosts: pg.sprite.Group = field(default_factory=pg.sprite.Group)

def set_up_level(
        screen: pg.Surface,
        level: int,
        ) -> MazeLevel:
    """
    Set up the maze level by loading and building the maze layout, and determining spawn points.
            
    Args:
        screen (pg.Surface): The screen surface to draw the maze on.
        level (int):
            The level number to set up.

            *There should be a corresponding maze file named `level{level}.txt`
            in the `assets/levels` folder.*

    Returns:
        MazeLevel: An object containing the maze layout, level number, and sorted spawn points.
    """
    _maze_layout = load_maze(
        level_file_name=f"level{level}.txt",
        interesting_parts=frozenset([
            MazePart.SPAWN_POINT,
            MazePart.PLAYER_SPAWN_POINT,
        ]),
        )
    _maze_layout = build_maze(
        _maze_layout,
        screen_sizes=screen.get_size(),
    )
    _spawn_points = _maze_layout.points_of_interest[MazePart.SPAWN_POINT]
    _player_spawn_points = _maze_layout.points_of_interest[MazePart.PLAYER_SPAWN_POINT]

    return MazeLevel(
        level=level,
        maze_layout=_maze_layout,
        spawn_points=sorted(_spawn_points),
        player_spawn_points=sorted(_player_spawn_points),
    )

def render_maze_level(
        maze_level: MazeLevel,
        screen: pg.Surface,
        dt: int, # delta time in milliseconds, the same as `pg.Clock.tick` return value
        ) -> None:
    """
    Render and update the maze level along with its ghosts.

    This function is responsible for updating the ghosts' positions and rendering
    the maze layout and ghosts on the provided screen surface.
    
    Note that the player's update logic should be handled separately
    in the main game loop.

    *(The player update logic should be handled in the main game loop **else where**.)*

    Args:
        maze_level (MazeLevel): The maze level to update and render.
        screen (pg.Surface): The Pygame surface on which the maze and ghosts will be drawn.
        dt (int): Delta time in milliseconds, typically the return value of `pg.Clock.tick`.

    Returns:
        None
    """
    maze_level.ghosts.update(dt)
    maze_level.maze_layout.draw_surface(
        screen=screen,
        center_to_offset=screen.get_rect().center,
    )
    maze_level.ghosts.draw(screen)
