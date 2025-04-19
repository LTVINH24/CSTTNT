"""path provider interface"""
from typing import Protocol, Optional, runtime_checkable, ClassVar
from dataclasses import dataclass
from weakref import WeakSet
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from functools import partial

import time

import pygame as pg

from src.maze import (
  MazeCoord, MazeNode, MazeLayout,
  rect_to_maze_coords, find_path_containing_coord, path_through_new_location
)
from src.constant import FPS

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

class CooldownTracker:
    """
    CooldownTracker is a utility class that helps manage cooldown periods in milliseconds.
    It is used to track the state of a cooldown timer and determine if it has expired.

    Attributes:
        cooldown_time (float): The duration of the cooldown period in milliseconds.
        last_update_time (float): The timestamp (in milliseconds) of the last reset.
        state (CooldownState): The current state of the cooldown tracker.
    Methods:
        __init__(cooldown_time: float = 1 * MILLISECOND) -> None:
            Initializes the CooldownTracker with a specified cooldown time.
        reset() -> None:
            Resets the cooldown timer to the current time.
        is_expired() -> bool:
            Checks if the cooldown has expired.
        pause() -> None:
            Pauses the cooldown tracker.
        is_paused() -> bool:
            Checks if the cooldown tracker is paused.
        deactivate() -> None:
            Deactivates the cooldown tracker.
        is_active() -> bool:
            Checks if the cooldown tracker is active (not deactivated).
    """
    class CooldownState(Enum):
        """
        Enum representing the state of the cooldown tracker.
        """
        DEACTIVATED = 0
        RUNNING = 1
        PAUSED = 2
    MILLISECOND: float = 1

    def __init__(self, cooldown_time: float = 1 * MILLISECOND) -> None:
        self.cooldown_time = cooldown_time
        self.last_update_time = time.time() * 1000
        self.state = CooldownTracker.CooldownState.DEACTIVATED

    def reset(self) -> None:
        """
        Reset the cooldown timer to the current time.
        """
        self.state = CooldownTracker.CooldownState.RUNNING
        self.last_update_time = time.time() * 1000

    def is_expired(self) -> bool:
        """
        Check if the cooldown is expired.

        Returns:
            bool: True if the cooldown is active, False otherwise.
        """
        return self.state == CooldownTracker.CooldownState.RUNNING and \
            time.time() * 1000 > self.last_update_time + self.cooldown_time

    def pause(self) -> None:
        """
        Pause the cooldown tracker.
        """
        self.state = CooldownTracker.CooldownState.PAUSED

    def is_paused(self) -> bool:
        """
        Check if the cooldown tracker is paused.

        Returns:
            bool: True if the cooldown tracker is paused, False otherwise.
        """
        return self.state == CooldownTracker.CooldownState.PAUSED

    def deactivate(self) -> None:
        """
        Deactivate the cooldown tracker.
        """
        self.state = CooldownTracker.CooldownState.DEACTIVATED

    def is_active(self) -> bool:
        """
        Check if the cooldown tracker is active (not deactivated).

        Returns:
            bool: True if the cooldown tracker is not deactivated, False otherwise.
        """
        return self.state != CooldownTracker.CooldownState.DEACTIVATED

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

    # Cooldown = 10 Frames
    DEFAULT_WAIT_TIME_FOR_CONFLICT_RESOLUTION: ClassVar[int] = 1000 // FPS * 10
    conflict_cooldown_tracker = CooldownTracker(
        DEFAULT_WAIT_TIME_FOR_CONFLICT_RESOLUTION
        )

    def is_waiting_for_path_conflict_resolution(self) -> bool:
        """
        Check if the listener is waiting for path conflict resolution.

        Returns:
            bool: True if the listener is waiting for path conflict resolution, False otherwise.
        """
        return self.conflict_cooldown_tracker.is_active()

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
PLAYER_POSITION_UPDATE_INTERVAL = 500  # milliseconds
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
        pathfinder: Pathfinder = None, # existing only for backward compatibility
    ):
        # XXX: Use proper locking mechanism if you need to modify the graph
        self.maze_layout = maze_layout

        self.player = player
        self.path_finder: Pathfinder = pathfinder or empty_path_finder
        self.listeners: WeakSet[PathListener] = WeakSet()
        self.executor = ThreadPoolExecutor(max_workers=WORKERS)

        self.player_position_update_interval = PLAYER_POSITION_UPDATE_INTERVAL
        if self.player.rect is None:
            raise ValueError("Player should have the `rect` attribute.")
        current_player_location = rect_to_path_location(
            self.player.rect, self.maze_layout.maze_dict, self.maze_layout.maze_shape()
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
            *,
            # keyword-only argument: backward compatibility
            path_finder: Pathfinder = None,
            forced_request: bool = False,
            blocking_edges: list[tuple[MazeNode, MazeNode]] = [],
            callback: callable = None,
            ) -> None:
        """
        Receive a request for a path from the listener.

        This method should be called by the listener (holding the reference to this class instance)
        to request a new path.

        The pathfinding result will be set to the `new_path` attribute of the listener.

        Args:
            listener (PathListener): The listener requesting the path.
            start_node (MazeNode): The starting node for the path.
            forced_request (bool): If True, forces the pathfinding even if the listener
                is already waiting for a path.
                Defaults to False.
        """
        if not forced_request and listener.waiting_for_path:
            # The listener is already waiting for a path
            return

        # Submit the pathfinding task to the executor.
        listener.waiting_for_path = True

        # Resolve trivial path
        if start_location == self.previous_player_location:
            # The listen is already at the target location
            # Note that listener.waiting_for_path should be keeping True here
            return
        if start_location[1] is None and start_location[0] in self.previous_player_location:
            # Can't happened if self.previous_player_location is of length 1
            listener.new_path = [
                start_location[0],
                self.previous_player_location[0] \
                    if self.previous_player_location[0] != start_location[0] \
                    else self.previous_player_location[1],
                ]
            listener.waiting_for_path = False
            return

        # Check if the pathfinder is callable, only for backward compatibility
        if path_finder is None:
            path_finder = self.path_finder

        sending_maze_graph = self.maze_layout.maze_graph
        if blocking_edges:
            starting_edges = [
                blocking_edge[0] for blocking_edge in blocking_edges
                ]
            new_maze_graph = []
            # Block the edges in the maze graph
            for node in sending_maze_graph:
                if node not in starting_edges:
                    new_maze_graph.append(node)
                    continue
                new_maze_graph.append(
                    MazeNode(
                        pos=node.pos,
                        neighbors={
                            k: v for k, v in node.neighbors.items() \
                              if (node, v[0]) not in blocking_edges
                        }
                    )
                )

        def _pathfinding_task() -> None:
            """
            Task to compute the pathfinding result.
            """
            path_result = path_finder(
                sending_maze_graph,  # The maze graph
                start_location,  # Starting location
                self.previous_player_location,  # Target location
            )
            if callback is not None:
                # Call the callback function if provided
                callback()
            listener.new_path = path_result.path
            listener.waiting_for_path = False
            # Return None

        # XXX: Enable/Disable multithreading for pathfinding here.
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
                self.player.rect, self.maze_layout.maze_dict, self.maze_layout.maze_shape()
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

    def handle_path_conflict_between(
        self,
        reporting_listener: PathListener,
        conflicting_listeners: list[PathListener],
        ) -> None:
        """
        Handle path conflicts between the reporting listener and the conflicting listeners.
        """
        if not reporting_listener.conflict_cooldown_tracker.is_active():
            # Try to solve itself
            reporter_edge = reporting_listener.path[:2]
            if len(reporter_edge) <= 1:
                raise ValueError(
                    "How a listener that isn't even moving have path conflict with others?"
                    )
            self.receive_request_for(
                    listener=reporting_listener,
                    start_location=tuple(reporter_edge.reverse()),
                    forced_request=True,
                    blocking_edges=[tuple(reporter_edge)],
                    # If they are still in conflict after receiving a new path, go below
                    callback=reporting_listener.conflict_cooldown_tracker.reset,
                )
            return
        if reporting_listener.conflict_cooldown_tracker.is_paused():
            # The reporting listener is waiting for conflict resolution
            return
        if not reporting_listener.conflict_cooldown_tracker.is_expired():
            # The time waiting to resolve conflict is still in cooldown
            return

        # The reporting listener is currently resolving a conflict
        # Pause the cooldown tracker for the reporting listener
        reporting_listener.conflict_cooldown_tracker.pause()

        conflict_resolved_for_reporter = False
        for conflicting_listener in conflicting_listeners:
            if conflicting_listener.conflict_cooldown_tracker.is_paused():
                # Either the conflicting listener is handle the conflict with another one
                # or it failed to resolve the conflict in its last handle_path_conflict call
                continue

            def release_blocking(
                reporting_listener: PathListener,
                conflicting_listener: PathListener = None,
            ) -> None:
                """
                Release the blocking for the reporting and the conflicting listener if specified.
                """
                # Resume the cooldown tracker for both listeners
                reporting_listener.conflict_cooldown_tracker.deactivate()
                if conflicting_listener is not None:
                    conflicting_listener.conflict_cooldown_tracker.deactivate()

            # Start checking for path conflict
            reporter_edge = reporting_listener.path[:2]
            reportee_edge = conflicting_listener.path[:2]
            if len(reporter_edge) <= 1:
                raise ValueError(
                    "How a not-moving reporting listener can be in conflict with a moving one?"
                    )
            if len(reportee_edge) <= 1:
                # The reporting listener is moving and the conflicting one is not
                # Lemme find the other way if possible

                self.receive_request_for(
                    listener=reporting_listener,
                    start_location=tuple(reporter_edge.reverse()),
                    forced_request=True,
                    blocking_edges=[tuple(reporter_edge)],
                    callback=partial(
                        release_blocking,
                        reporting_listener=reporting_listener,
                    ),
                )
                return

            # len(reporter_edge) == 2 and len(reportee_edge) == 2:
            # Both listeners are moving

            self.receive_request_for(
                listener=reportee_edge,
                start_location=tuple(reportee_edge.reverse()),
                forced_request=True,
                blocking_edges=[tuple(reporter_edge)],
                callback=partial(
                    release_blocking,
                    reporting_listener=reporting_listener,
                    conflicting_listener=conflicting_listener,
                ),
            )
            return
            # End for loop
        if not conflict_resolved_for_reporter:
            # No path conflict was resolved for the reporting listener
            reporting_listener.conflict_cooldown_tracker.pause()
