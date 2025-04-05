"""path provider interface"""
from typing import Protocol, Optional, runtime_checkable
from dataclasses import dataclass
from weakref import WeakSet
from concurrent.futures import ThreadPoolExecutor

import pygame as pg

from src.maze import MazeNode, MazeLayout

@dataclass
class PathfindingResult:
    """
    Encapsulates the results of a pathfinding operation.

    Attributes:
        path (list[MazeNode]):
            The sequence of nodes representing the path from the start to the goal.
        expanded_nodes (list[MazeNode]):
            The list of nodes that were expanded during the pathfinding process.
"""
    path: list[MazeNode]
    expanded_nodes: list[MazeNode]

# pylint: disable=too-few-public-methods
@runtime_checkable
class Pathfinder(Protocol):
    """
    Pathfinder is a protocol that defines a callable interface for pathfinding in a maze.

    This callable is expected to take a graph representation of a maze, a starting location, 
    and a target location, and return a PathfindingResult.

    Parameters:
        maze_graph (list[MazeNode]): A list of MazeNode objects representing the graph of the maze.
        start_location (tuple[MazeNode, Optional[MazeNode]]):
            A tuple representing the starting location. 
            The tuple should have a maximum length of 2.
        target_location (tuple[MazeNode, Optional[MazeNode]]):
            A tuple representing the target location. 
            The tuple should have a maximum length of 2.
    Returns:
        PathfindingResult:
            The result of the pathfinding operation, encapsulating the 
            necessary information about the computed path.
    """
    def __call__(
        self,
        maze_graph: list[MazeNode],
        start_location: tuple[MazeNode, Optional[MazeNode]], # max-length = 2
        target_location: tuple[MazeNode, Optional[MazeNode]], # max-length = 2
        ) -> PathfindingResult:
        return PathfindingResult([], [])

def empty_path_finder(
    _maze_graph: list[MazeNode],
    _start_location: tuple[MazeNode, Optional[MazeNode]], # max-length = 2
    _target_location: tuple[MazeNode, Optional[MazeNode]], # max-length = 2
) -> PathfindingResult:
    """
    Empty pathfinder function that returns an empty pathfinding result.
    """
    return PathfindingResult([], [])

class PathListener(Protocol):
    """
    Protocol for objects that can listen for path updates from the PathDispatcher.

    Methods:
        on_new_path(path: list[MazeNode]) -> None:
            Called when a new path is provided by the PathDispatcher.
    """
    path: list[MazeNode]
    new_path: list[MazeNode] = []
    waiting_for_path: bool = False

    def halt_current_and_request_new_path(self) -> tuple[MazeNode, Optional[MazeNode]]:
        """
        Halt the current path and request a new one.

        Returns the location of the listener after the path is halted.
        """

def pacman_rect_to_location(
        _pacman_rect: pg.Rect,
    ) -> tuple[MazeNode, Optional[MazeNode]]:
    """
    Convert the Pacman's position to a location in the maze.

    Args:
        pacman_position (MazeNode): The Pacman's position in the maze.
        maze_layout (MazeLayout): The maze layout.

    Returns:
        tuple[MazeNode, Optional[MazeNode]]: The location of the Pacman in the maze.
    """
    # TODO: Implement the conversion logic
    return (MazeNode(), None)

WORKERS = 4
PLAYER_POSITION_UPDATE_INTERVAL = 2000  # milliseconds
class PathDispatcher:
    """
    The PathDispatcher class is responsible for managing pathfinding requests and updates
    in a maze-like environment. It interacts with a maze graph, a player, and a pathfinding
    algorithm to compute paths and notify registered listeners of path updates.
    Attributes:
        maze_graph (list[MazeNode]): The graph representation of the maze.
        player (pg.sprite.Sprite): The player object whose position is tracked.
        pathfinder (Pathfinder): The pathfinding algorithm used to compute paths.
        listeners (WeakSet[PathListener]): A set of listeners to notify about path updates.
        executor (ThreadPoolExecutor): A thread pool executor for handling pathfinding tasks.
        player_position_update_interval (int): The interval for checking player position updates.
        previous_player_location (tuple): The last known location of the player.
    Methods:
        __init__(maze_graph, player, pathfinder):
            Initializes the PathDispatcher with the maze graph, player, and pathfinder.
        register_listener(listener):
            Registers a listener to be notified of path updates.
        receive_request_for(listener, start_location):
            Receives a request for a path from the listener and set pathfinding result later.
            ***Should be called by the listeners while they are holding the reference
            of this object.***
        update(dt):
            Checks if the player's position has changed and updates paths if necessary.
    """
    def __init__(
        self,
        # TODO: Use proper locking mechanism if you need to modify the graph
        maze_graph: list[MazeNode],
        player: pg.sprite.Sprite,
        pathfinder: Pathfinder,
    ):
        self.maze_graph = maze_graph
        self.player = player
        self.pathfinder = pathfinder
        self.listeners: WeakSet[PathListener] = WeakSet()
        self.executor = ThreadPoolExecutor(max_workers=WORKERS)

        self.player_position_update_interval = PLAYER_POSITION_UPDATE_INTERVAL
        self.previous_player_location = pacman_rect_to_location(self.player.rect)

    def register_listener(self, listener: PathListener) -> None:
        """
        Register a listener for a user.

        Args:
            user (object): The user to register.
            listener (PathListener): The listener to notify when a new path is forced.
        """
        self.listeners.add(listener)

    def receive_request_for(
            self,
            listener: PathListener,
            start_location: tuple[MazeNode, Optional[MazeNode]],
            ) -> None:
        """
        Receive a request for a path from the listener.
        This method is called by the listener to request a new path.

        The pathfinding result will be set to the `new_path` attribute of the listener.

        Args:
            user (object): The user requesting the path.
            start_node (MazeNode): The starting node for the path.
        """
        def _pathfinding_task() -> None:
            """
            Task to compute the pathfinding result.
            """
            path_result = self.pathfinder(
                self.maze_graph,
                start_location,  # Starting location (max-length = 2)
                pacman_rect_to_location(self.player.rect),  # Pacman's location (max-length = 2)
            )
            listener.new_path = path_result.path
            listener.waiting_for_path = False
            # Return None
        # Submit the pathfinding task to the executor.
        listener.waiting_for_path = True

        # TODO: Enable/Disable multithreading for pathfinding here.
        self.executor.submit(_pathfinding_task)

        # _pathfinding_task()

    def update(self, dt: int) -> None:
        """
        Check if the player is in a new location and update the path if necessary.
        """
        if self.player_position_update_interval <= 0:
            # Reset the interval
            self.player_position_update_interval = PLAYER_POSITION_UPDATE_INTERVAL

            # Check if the player is in a new location
            player_location = pacman_rect_to_location(self.player.rect)
            if player_location != self.previous_player_location:
                for listener in self.listeners:
                    # TODO: Check if the listener's current path overlaps ...
                    # TODO: with the player's new location. If not, request a new path.
                    listener.halt_current_and_request_new_path()
        else:
            # Decrease the interval
            self.player_position_update_interval -= dt

def build_path_dispatcher(
    maze_layout: MazeLayout,
    player: pg.sprite.Sprite,
    pathfinder: Pathfinder = empty_path_finder,
) -> PathDispatcher:
    """
    Build a PathDispatcher for the given maze layout.

    Args:
        maze_layout (MazeLayout): The maze layout to build the dispatcher for.
        pathfinder (Pathfinder, optional):
            The pathfinding algorithm to use. Defaults to empty_path_finder.

    Returns:
        PathDispatcher: The built PathDispatcher.
    """
    return PathDispatcher(
        maze_graph=maze_layout.maze_graph,
        player=player,
        pathfinder=pathfinder,
    )
