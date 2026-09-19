"""
3D A* Path Planning Algorithm for SwarmIQ.
Calculates global collision-free waypoints for the swarm leader through 3D obstacle fields.
Includes obstacle voxelization, A* graph search, and line-of-sight waypoint pruning (string pulling).
"""

from typing import List, Tuple, Set, Optional, Dict
import heapq
import numpy as np

from app.simulation.environment import Obstacle
from app.models.schemas import ObstacleType
from app.core.config import settings


class Node3D:
    __slots__ = ("x", "y", "z", "g", "h", "f", "parent")

    def __init__(self, x: int, y: int, z: int, g: float = 0.0, h: float = 0.0, parent=None):
        self.x = x
        self.y = y
        self.z = z
        self.g = g
        self.h = h
        self.f = g + h
        self.parent = parent

    def __lt__(self, other: "Node3D") -> bool:
        return self.f < other.f

    @property
    def coord(self) -> Tuple[int, int, int]:
        return (self.x, self.y, self.z)


class AStarPlanner:
    def __init__(
        self,
        grid_resolution: float = 3.0,  # meters per grid cell
        safety_margin: float = 2.5,  # obstacle inflation radius
    ):
        self.resolution = grid_resolution
        self.safety_margin = safety_margin

        # Grid bounds
        self.min_bounds = np.array([settings.bounds_x[0], settings.bounds_y[0], settings.bounds_z[0]])
        self.max_bounds = np.array([settings.bounds_x[1], settings.bounds_y[1], settings.bounds_z[1]])

    def world_to_grid(self, world_pos: np.ndarray) -> Tuple[int, int, int]:
        grid_coords = np.floor((world_pos - self.min_bounds) / self.resolution).astype(int)
        return int(grid_coords[0]), int(grid_coords[1]), int(grid_coords[2])

    def grid_to_world(self, grid_coord: Tuple[int, int, int]) -> np.ndarray:
        return self.min_bounds + (np.array(grid_coord, dtype=np.float64) + 0.5) * self.resolution

    def is_point_in_obstacle(self, point: np.ndarray, obstacles: List[Obstacle]) -> bool:
        """Check if 3D point penetrates any obstacle (with safety margin inflation)."""
        for obs in obstacles:
            if obs.type == ObstacleType.SPHERE:
                radius = obs.size[0] + self.safety_margin
                if np.linalg.norm(point - obs.position) <= radius:
                    return True

            elif obs.type == ObstacleType.CYLINDER:
                radius = obs.size[0] + self.safety_margin
                height = obs.size[1]
                # Check height
                if obs.position[1] <= point[1] <= obs.position[1] + height:
                    # Check radial distance in XZ plane
                    horizontal_dist = np.hypot(point[0] - obs.position[0], point[2] - obs.position[2])
                    if horizontal_dist <= radius:
                        return True

            elif obs.type == ObstacleType.BOX:
                half_size = obs.size / 2.0 + self.safety_margin
                diff = np.abs(point - obs.position)
                if np.all(diff <= half_size):
                    return True
        return False

    def plan_path(
        self,
        start_pos: np.ndarray,
        goal_pos: np.ndarray,
        obstacles: List[Obstacle],
        max_iterations: int = 5000,
    ) -> List[np.ndarray]:
        """
        Execute 3D A* search from start_pos to goal_pos.
        Returns pruned list of 3D waypoints.
        """
        # If line of sight directly to goal without obstacle intersection, return direct path
        if self._line_of_sight(start_pos, goal_pos, obstacles):
            return [np.copy(goal_pos)]

        start_grid = self.world_to_grid(start_pos)
        goal_grid = self.world_to_grid(goal_pos)

        open_set: List[Node3D] = []
        open_dict: Dict[Tuple[int, int, int], float] = {}
        closed_set: Set[Tuple[int, int, int]] = set()

        h_start = np.linalg.norm(np.array(start_grid) - np.array(goal_grid)) * self.resolution
        start_node = Node3D(start_grid[0], start_grid[1], start_grid[2], g=0.0, h=h_start)
        heapq.heappush(open_set, start_node)
        open_dict[start_grid] = start_node.g

        # 26-connectivity 3D neighborhood deltas
        deltas = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    if dx == 0 and dy == 0 and dz == 0:
                        continue
                    cost = np.sqrt(dx * dx + dy * dy + dz * dz) * self.resolution
                    deltas.append((dx, dy, dz, cost))

        iterations = 0
        best_node = start_node
        min_h = h_start

        while open_set and iterations < max_iterations:
            iterations += 1
            current = heapq.heappop(open_set)
            curr_coord = current.coord

            if curr_coord in closed_set:
                continue
            closed_set.add(curr_coord)

            # Check if goal grid reached
            if curr_coord == goal_grid or np.linalg.norm(np.array(curr_coord) - np.array(goal_grid)) <= 1.5:
                raw_path = self._reconstruct_path(current)
                return self._prune_waypoints(raw_path, obstacles, goal_pos)

            # Track closest node in case max_iterations reached
            if current.h < min_h:
                min_h = current.h
                best_node = current

            for dx, dy, dz, step_cost in deltas:
                neighbor_coord = (current.x + dx, current.y + dy, current.z + dz)

                if neighbor_coord in closed_set:
                    continue

                world_neighbor = self.grid_to_world(neighbor_coord)

                # Boundary check
                if (
                    world_neighbor[0] < self.min_bounds[0]
                    or world_neighbor[0] > self.max_bounds[0]
                    or world_neighbor[1] < self.min_bounds[1]
                    or world_neighbor[1] > self.max_bounds[1]
                    or world_neighbor[2] < self.min_bounds[2]
                    or world_neighbor[2] > self.max_bounds[2]
                ):
                    continue

                # Obstacle check
                if self.is_point_in_obstacle(world_neighbor, obstacles):
                    continue

                tentative_g = current.g + step_cost

                if neighbor_coord in open_dict and tentative_g >= open_dict[neighbor_coord]:
                    continue

                h_val = np.linalg.norm(np.array(neighbor_coord) - np.array(goal_grid)) * self.resolution
                neighbor_node = Node3D(
                    neighbor_coord[0],
                    neighbor_coord[1],
                    neighbor_coord[2],
                    g=tentative_g,
                    h=h_val,
                    parent=current,
                )
                open_dict[neighbor_coord] = tentative_g
                heapq.heappush(open_set, neighbor_node)

        # Fallback if no full path: reconstruct to closest best node or return goal
        raw_path = self._reconstruct_path(best_node)
        return self._prune_waypoints(raw_path, obstacles, goal_pos)

    def _reconstruct_path(self, node: Node3D) -> List[np.ndarray]:
        path = []
        curr: Optional[Node3D] = node
        while curr is not None:
            path.append(self.grid_to_world(curr.coord))
            curr = curr.parent
        path.reverse()
        return path

    def _line_of_sight(self, p1: np.ndarray, p2: np.ndarray, obstacles: List[Obstacle]) -> bool:
        """Check if straight line segment between p1 and p2 is collision free."""
        dist = float(np.linalg.norm(p2 - p1))
        if dist < 1e-3:
            return True
        # Dynamic sample density: at least every 1.2 meters to ensure no obstacle is skipped
        num_samples = max(20, int(dist / 1.2))
        for alpha in np.linspace(0.0, 1.0, num_samples):
            test_pt = p1 + alpha * (p2 - p1)
            if self.is_point_in_obstacle(test_pt, obstacles):
                return False
        return True

    def _prune_waypoints(
        self, raw_path: List[np.ndarray], obstacles: List[Obstacle], final_goal: np.ndarray
    ) -> List[np.ndarray]:
        """String pulling: eliminate redundant colinear or line-of-sight waypoints."""
        if not raw_path:
            return [np.copy(final_goal)]

        pruned = [raw_path[0]]
        current_idx = 0

        while current_idx < len(raw_path) - 1:
            # Greedily search furthest visible waypoint ahead
            next_idx = current_idx + 1
            for lookahead_idx in range(len(raw_path) - 1, current_idx, -1):
                if self._line_of_sight(raw_path[current_idx], raw_path[lookahead_idx], obstacles):
                    next_idx = lookahead_idx
                    break
            pruned.append(raw_path[next_idx])
            current_idx = next_idx

        # Ensure destination is the terminal waypoint
        if np.linalg.norm(pruned[-1] - final_goal) > 1.0:
            pruned.append(np.copy(final_goal))

        return pruned
