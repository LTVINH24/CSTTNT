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
    Class representing a level in the maze.

    Attributes:
        level (int): The level number.
        description (str): Description of the level.
    """
    level: int
    maze_layout: MazeLayout
    spawn_points: list[MazeCoord]

    ghosts: pg.sprite.Group = field(default_factory=pg.sprite.Group)

def set_up_level(
        screen: pg.Surface,
        level: int,
        ) -> MazeLevel:
    """
    Set up the maze level.

    Args:
        level (int): The level to set up.

    Returns:
        None
    """
    _maze_layout = load_maze(f"level{level}.txt")
    _maze_layout = build_maze(
        _maze_layout,
        screen_sizes=screen.get_size(),
    )
    _spawn_points = _maze_layout.points_of_interest[MazePart.SPAWN_POINT]

    return MazeLevel(
        level=level,
        maze_layout=_maze_layout,
        spawn_points=sorted(_spawn_points, key=lambda x: (x.x, x.y)),
    )

def render_maze_level(
        maze_level: MazeLevel,
        screen: pg.Surface,
        dt: int, # delta time in milliseconds, the same as `pg.Clock.tick` return value
        ) -> None:
    """
    Update the maze level along with its ghosts.

    The player update logic should be handled in the main game loop **else where**.

    Args:
        mazeLevel (MazeLevel): The maze level to update.

    Returns:
        None
    """
    maze_level.ghosts.update(dt)
    maze_level.maze_layout.draw_surface(
        screen=screen,
        center_to_offset=screen.get_rect().center,
    )
    maze_level.ghosts.draw(screen)
