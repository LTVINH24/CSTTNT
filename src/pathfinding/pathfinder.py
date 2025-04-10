"""path provider interface"""
from typing import Protocol, Optional, runtime_checkable
from dataclasses import dataclass
from weakref import WeakSet
from concurrent.futures import ThreadPoolExecutor

import pygame as pg

from src.maze import (
  MazeCoord, MazeNode, MazeLayout,
  rect_to_maze_coords, find_path_containing_coord, path_through_new_location
)

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
    PathListener is a protocol that defines the structure for objects
    capable of listening for path updates from a PathDispatcher.
    It provides attributes and methods to manage and respond to path changes.
    
    Attributes:
        path (list[MazeNode]):
            The current path being followed by the listener.
        new_path (list[MazeNode]):
            A placeholder for a newly requested path. Defaults to an empty list.
        waiting_for_path (bool):
            A flag indicating whether the listener is waiting for a new path. Defaults to False.

        halt_current_and_request_new_path (() -> tuple[MazeNode, Optional[MazeNode]]):
            Halts the current path and requests a new one.
            
            Returns the location of the listener 
            after the path is halted, which can be either a single node or a tuple of two nodes.

            If this is a tuple of one node, it means that the listening object
            is standing on a node. If this is a tuple of two nodes,
            it means that the listening object is currently moving
            from the first node to the second node.
    """
    path: list[MazeNode]
    new_path: list[MazeNode] = []
    waiting_for_path: bool = False

    def halt_current_and_request_new_path(self) -> tuple[MazeNode, Optional[MazeNode]]:
        """
        Halt the current path and request a new one.

        Returns:
            tuple[MazeNode, Optional[MazeNode]]: The location of the listener
                after the path is halted.

                If this is a tuple of one node, it means that the listening object
                is standing on a node.

                If this is a tuple of two nodes, it means that the listening object
                is currently moving from the first node to the second node.
        """

def rect_to_path_location(
        rect: pg.Rect,
        maze_dict: dict[MazeCoord, MazeNode],
        maze_shape: tuple[int, int]
    ) -> tuple[MazeNode, MazeNode | None] | None:
    """
    Convert the Pacman's position to a location in the maze.

    Args:
        _pacman_rect (pg.Rect): The rect representing the Pacman's position.

    Returns:
        out (tuple[MazeNode, Optional[MazeNode]]): The location of the Pacman in the maze.
    """
    current_coord = rect_to_maze_coords(rect)
    return find_path_containing_coord(
        current_coord=current_coord,
        maze_dict=maze_dict,
        maze_shape=maze_shape,
    )

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
        maze_layout: MazeLayout,
        player: pg.sprite.Sprite,
        pathfinder: Pathfinder,
    ):
        # TODO: Use proper locking mechanism if you need to modify the graph
        self.maze_layout = maze_layout

        self.player = player
        self.pathfinder = pathfinder
        self.listeners: WeakSet[PathListener] = WeakSet()
        self.executor = ThreadPoolExecutor(max_workers=WORKERS)

        self.player_position_update_interval = PLAYER_POSITION_UPDATE_INTERVAL
        if self.player.rect is None:
            raise ValueError("Player should have the `rect` attribute.")
        current_player_location = rect_to_path_location(
            self.player.rect, self.maze_layout.maze_dict, self.maze_layout.maze_shape
        )
        if current_player_location is None:
            raise ValueError("Player should be in a valid location.")
        # Class invariant: current_player_location is not None
        self.previous_player_location = current_player_location

    def register_listener(self, listener: PathListener) -> None:
        """
        Register a listener for a user.

        Args:
            listener (PathListener): The listener to be registered.
        """
        self.listeners.add(listener)

    def receive_request_for(
            self,
            listener: PathListener,
            start_location: tuple[MazeNode, Optional[MazeNode]],
            ) -> None:
        """
        Receive a request for a path from the listener.

        This method should be called by the listener (holding the reference to this class instance)
        to request a new path.

        The pathfinding result will be set to the `new_path` attribute of the listener.

        Args:
            listener (PathListener): The listener requesting the path.
            start_node (MazeNode): The starting node for the path.
        """
        def _pathfinding_task() -> None:
            """
            Task to compute the pathfinding result.
            """
            path_result = self.pathfinder(
                self.maze_layout.maze_graph,  # The maze graph
                start_location,  # Starting location
                self.previous_player_location,  # Target location
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

        This method should be called periodically to check for player position updates.

        Args:
            dt (int): The time delta since the last update in milliseconds.
        """
        if self.player_position_update_interval <= 0:
            # Reset the interval
            self.player_position_update_interval = PLAYER_POSITION_UPDATE_INTERVAL

            # Check if the player is in a new location
            new_location = rect_to_path_location(
                self.player.rect, self.maze_layout.maze_dict, self.maze_layout.maze_shape
            )
            if new_location is None:
                print("Warning: Player should be in a valid location.")
                return
            if new_location != self.previous_player_location:
                self.previous_player_location = new_location
                for listener in self.listeners:
                    pass_through_path = path_through_new_location(
                        checking_path=listener.path,
                        location=new_location,
                    )
                    if pass_through_path is None:
                        listener.halt_current_and_request_new_path()
                    else:
                        listener.new_path = pass_through_path
        else:
            # Decrease the interval
            self.player_position_update_interval -= dt

