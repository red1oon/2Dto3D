#!/usr/bin/env python3
"""
Spatial Awareness Module - Phase 2
===================================
Provides wall detection, room detection, and spatial relationship logic
needed for intelligent object rotation and placement.

This enables:
- wall_normal rotation (objects face perpendicular to wall)
- room_entrance rotation (toilets face entrance)
- Spatial validation (clearance checking)

Author: DeepSeek Integration Team
Date: 2025-11-23
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Wall:
    """Represents a wall segment"""
    start: np.ndarray  # (x, y) start point
    end: np.ndarray    # (x, y) end point
    normal: np.ndarray  # Unit normal vector pointing into room
    name: str = ""

    def length(self) -> float:
        """Get wall length"""
        return np.linalg.norm(self.end - self.start)

    def midpoint(self) -> np.ndarray:
        """Get wall midpoint"""
        return (self.start + self.end) / 2

    def distance_to_point(self, point: np.ndarray) -> float:
        """
        Calculate minimum distance from point to wall segment

        Args:
            point: (x, y) coordinates

        Returns:
            Minimum distance to wall
        """
        # Vector from start to end
        wall_vec = self.end - self.start
        wall_length = np.linalg.norm(wall_vec)

        if wall_length == 0:
            return np.linalg.norm(point - self.start)

        # Normalize wall vector
        wall_dir = wall_vec / wall_length

        # Vector from start to point
        to_point = point - self.start

        # Project onto wall
        projection_length = np.dot(to_point, wall_dir)

        # Clamp to wall segment
        projection_length = np.clip(projection_length, 0, wall_length)

        # Closest point on wall
        closest_point = self.start + projection_length * wall_dir

        # Distance
        return np.linalg.norm(point - closest_point)

    def get_rotation_to_normal(self) -> float:
        """Get rotation angle to face perpendicular to wall (radians)"""
        return np.arctan2(self.normal[1], self.normal[0])


@dataclass
class Room:
    """Represents a room polygon"""
    name: str
    vertices: List[np.ndarray]  # List of (x, y) vertices in CCW order
    walls: List[Wall]
    entrance_location: Optional[np.ndarray] = None  # (x, y) of entrance

    def contains_point(self, point: np.ndarray) -> bool:
        """
        Check if point is inside room using ray casting algorithm

        Args:
            point: (x, y) coordinates

        Returns:
            True if point is inside room
        """
        x, y = point[0], point[1]
        n = len(self.vertices)
        inside = False

        p1 = self.vertices[0]
        for i in range(1, n + 1):
            p2 = self.vertices[i % n]

            if y > min(p1[1], p2[1]):
                if y <= max(p1[1], p2[1]):
                    if x <= max(p1[0], p2[0]):
                        if p1[1] != p2[1]:
                            xinters = (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1]) + p1[0]

                        if p1[0] == p2[0] or x <= xinters:
                            inside = not inside

            p1 = p2

        return inside

    def get_bounding_box(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get room bounding box (min, max)"""
        vertices_array = np.array(self.vertices)
        return vertices_array.min(axis=0), vertices_array.max(axis=0)


class SpatialContext:
    """
    Manages spatial relationships in a building

    Provides wall detection, room detection, and spatial queries
    for intelligent object placement.
    """

    def __init__(self):
        self.walls: List[Wall] = []
        self.rooms: List[Room] = []

    def add_wall(self, start: List[float], end: List[float], name: str = ""):
        """
        Add a wall segment

        Args:
            start: [x, y] start coordinates
            end: [x, y] end coordinates
            name: Optional wall name
        """
        start_np = np.array(start)
        end_np = np.array(end)

        # Calculate normal (perpendicular to wall, pointing "inward")
        wall_vec = end_np - start_np
        # Rotate 90 degrees counter-clockwise for left-hand normal
        normal = np.array([-wall_vec[1], wall_vec[0]])
        normal = normal / np.linalg.norm(normal)  # Normalize

        wall = Wall(
            start=start_np,
            end=end_np,
            normal=normal,
            name=name
        )

        self.walls.append(wall)

    def add_room(self, name: str, vertices: List[List[float]], entrance: Optional[List[float]] = None):
        """
        Add a room

        Args:
            name: Room name
            vertices: List of [x, y] vertices in counter-clockwise order
            entrance: Optional [x, y] entrance location
        """
        vertices_np = [np.array(v) for v in vertices]

        # Create walls from vertices
        walls = []
        n = len(vertices_np)
        for i in range(n):
            start = vertices_np[i]
            end = vertices_np[(i + 1) % n]

            # Calculate normal pointing into room
            wall_vec = end - start
            normal = np.array([-wall_vec[1], wall_vec[0]])
            normal = normal / np.linalg.norm(normal)

            walls.append(Wall(
                start=start,
                end=end,
                normal=normal,
                name=f"{name}_wall_{i}"
            ))

        entrance_np = np.array(entrance) if entrance else None

        room = Room(
            name=name,
            vertices=vertices_np,
            walls=walls,
            entrance_location=entrance_np
        )

        self.rooms.append(room)

    def find_nearest_wall(self, position: np.ndarray, max_distance: float = 2.0) -> Optional[Wall]:
        """
        Find nearest wall to a position

        Args:
            position: (x, y, z) position (z is ignored)
            max_distance: Maximum search distance

        Returns:
            Nearest Wall object, or None if no wall within max_distance
        """
        point_2d = position[:2]  # Get x, y only

        nearest_wall = None
        nearest_distance = float('inf')

        for wall in self.walls:
            distance = wall.distance_to_point(point_2d)

            if distance < nearest_distance and distance <= max_distance:
                nearest_distance = distance
                nearest_wall = wall

        return nearest_wall

    def find_containing_room(self, position: np.ndarray) -> Optional[Room]:
        """
        Find which room contains a position

        Args:
            position: (x, y, z) position (z is ignored)

        Returns:
            Room object containing the point, or None
        """
        point_2d = position[:2]

        for room in self.rooms:
            if room.contains_point(point_2d):
                return room

        return None

    def calculate_wall_normal_rotation(self, wall: Wall, flip: bool = False) -> float:
        """
        Calculate rotation to face perpendicular to wall

        Args:
            wall: Wall object
            flip: If True, face opposite direction

        Returns:
            Rotation angle in radians (Z-axis rotation)
        """
        rotation = wall.get_rotation_to_normal()

        if flip:
            rotation += np.pi

        return rotation

    def calculate_room_entrance_rotation(self, room: Room, object_position: np.ndarray) -> float:
        """
        Calculate rotation to face room entrance

        Args:
            room: Room object
            object_position: (x, y, z) position of object

        Returns:
            Rotation angle in radians (Z-axis rotation)
        """
        if room.entrance_location is None:
            # Fallback: face towards room center
            room_center = np.mean(room.vertices, axis=0)
            direction = room_center - object_position[:2]
        else:
            # Face towards entrance
            direction = room.entrance_location - object_position[:2]

        # Calculate angle
        rotation = np.arctan2(direction[1], direction[0])

        return rotation


def create_test_building() -> SpatialContext:
    """
    Create a test building layout for demonstration

    Simple rectangular building with 3 rooms:
    - Living room (left)
    - Bedroom (top right)
    - Bathroom (bottom right)
    """
    context = SpatialContext()

    # Living room (0, 0) to (6, 4)
    context.add_room(
        name="living_room",
        vertices=[
            [0, 0],
            [6, 0],
            [6, 4],
            [0, 4]
        ],
        entrance=[3, 0]  # Entrance on bottom wall
    )

    # Bedroom (6, 2) to (10, 6)
    context.add_room(
        name="bedroom",
        vertices=[
            [6, 2],
            [10, 2],
            [10, 6],
            [6, 6]
        ],
        entrance=[6, 4]  # Entrance on left wall
    )

    # Bathroom (6, 0) to (10, 2)
    context.add_room(
        name="bathroom",
        vertices=[
            [6, 0],
            [10, 0],
            [10, 2],
            [6, 2]
        ],
        entrance=[6, 1]  # Entrance on left wall
    )

    # Add some individual walls for testing
    context.add_wall([0, 0], [10, 0], "south_wall")
    context.add_wall([10, 0], [10, 6], "east_wall")
    context.add_wall([10, 6], [0, 6], "north_wall")
    context.add_wall([0, 6], [0, 0], "west_wall")

    return context


def demo_spatial_awareness():
    """Demonstrate spatial awareness functionality"""

    print("=" * 70)
    print("SPATIAL AWARENESS - Demonstration")
    print("=" * 70)
    print()

    # Create test building
    context = create_test_building()

    print(f"Created test building:")
    print(f"  Rooms: {len(context.rooms)}")
    print(f"  Walls: {len(context.walls)}")
    print()

    # Test points
    test_points = [
        ([2.0, 0.1, 0.0], "Door in living room (near south wall)"),
        ([2.5, 0.02, 0.0], "Switch in living room (on south wall)"),
        ([8.0, 1.0, 0.0], "Toilet in bathroom"),
        ([7.0, 5.0, 0.0], "Object in bedroom"),
    ]

    for position, description in test_points:
        pos_np = np.array(position)

        print(f"📍 {description}")
        print(f"   Position: {position}")

        # Find nearest wall
        wall = context.find_nearest_wall(pos_np)
        if wall:
            distance = wall.distance_to_point(pos_np[:2])
            rotation_deg = np.degrees(wall.get_rotation_to_normal())
            print(f"   Nearest wall: {wall.name} (distance: {distance:.3f}m)")
            print(f"   Wall normal rotation: {rotation_deg:.1f}°")

        # Find containing room
        room = context.find_containing_room(pos_np)
        if room:
            print(f"   Room: {room.name}")

            if room.entrance_location is not None:
                entrance_rotation_deg = np.degrees(
                    context.calculate_room_entrance_rotation(room, pos_np)
                )
                print(f"   Face entrance rotation: {entrance_rotation_deg:.1f}°")

        print()

    print("=" * 70)
    print("✅ SPATIAL AWARENESS DEMONSTRATION COMPLETE")
    print("=" * 70)
    print()
    print("Key Features:")
    print("- Wall detection with distance calculation")
    print("- Room containment checking")
    print("- Wall normal rotation calculation")
    print("- Room entrance rotation calculation")
    print()
    print("Next: Integrate with geometric rules engine for full placement")
    print()


if __name__ == "__main__":
    demo_spatial_awareness()
