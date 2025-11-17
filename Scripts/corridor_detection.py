#!/usr/bin/env python3
"""
Corridor Detection Engine for Master Template Charting System.

Analyzes wall patterns to identify corridors, extract centerlines,
and classify corridor types for intelligent MEP routing.
"""

import sqlite3
import math
from typing import List, Tuple, Dict
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Wall:
    """Represents a wall segment."""
    guid: str
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    length: float
    angle: float  # 0-360 degrees

    def midpoint(self) -> Tuple[float, float]:
        """Get wall midpoint."""
        return ((self.start_x + self.end_x) / 2, (self.start_y + self.end_y) / 2)


@dataclass
class Corridor:
    """Represents a detected corridor."""
    corridor_id: int
    corridor_type: str  # 'main', 'secondary', 'cross'
    centerline_points: List[Tuple[float, float]]
    width: float
    length: float
    direction: str  # 'horizontal', 'vertical', 'diagonal'
    angle: float  # Primary direction angle
    wall_pairs: List[Tuple[str, str]]  # Pairs of parallel walls

    def get_trunk_routing_points(self, segment_length: float = 5.0) -> List[Tuple[float, float]]:
        """
        Get evenly-spaced points along corridor centerline for trunk line routing.

        Args:
            segment_length: Target distance between routing points (meters)

        Returns:
            List of (x, y) coordinates for trunk line segments
        """
        if len(self.centerline_points) < 2:
            return self.centerline_points

        routing_points = [self.centerline_points[0]]

        for i in range(1, len(self.centerline_points)):
            start = self.centerline_points[i-1]
            end = self.centerline_points[i]

            dx = end[0] - start[0]
            dy = end[1] - start[1]
            seg_length = math.sqrt(dx*dx + dy*dy)

            if seg_length > 0:
                # Add intermediate points if segment is long
                num_segments = max(1, int(seg_length / segment_length))
                for j in range(1, num_segments + 1):
                    t = j / num_segments
                    point = (start[0] + dx * t, start[1] + dy * t)
                    routing_points.append(point)

        return routing_points


class CorridorDetector:
    """Detects corridors from wall patterns in the database."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.walls: List[Wall] = []
        self.corridors: List[Corridor] = []

    def load_walls(self):
        """Load all walls from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all walls with their positions
        cursor.execute("""
            SELECT
                em.guid,
                et.center_x,
                et.center_y,
                et.center_z,
                et.length,
                COALESCE(et.rotation_z, 0) as rotation_z
            FROM elements_meta em
            JOIN element_transforms et ON em.guid = et.guid
            WHERE em.ifc_class = 'IfcWall'
            ORDER BY et.center_x, et.center_y
        """)

        for row in cursor.fetchall():
            guid, cx, cy, cz, length, rotation_z = row

            # Convert rotation to angle (assuming rotation_z is in radians)
            angle = math.degrees(rotation_z) % 360

            # Calculate wall endpoints based on center, length, and rotation
            half_len = length / 2
            rad = math.radians(rotation_z)

            start_x = cx - half_len * math.cos(rad)
            start_y = cy - half_len * math.sin(rad)
            end_x = cx + half_len * math.cos(rad)
            end_y = cy + half_len * math.sin(rad)

            wall = Wall(
                guid=guid,
                start_x=start_x,
                start_y=start_y,
                end_x=end_x,
                end_y=end_y,
                length=length,
                angle=angle
            )
            self.walls.append(wall)

        conn.close()
        print(f"Loaded {len(self.walls)} walls from database")

    def find_parallel_walls(self, angle_tolerance: float = 5.0) -> Dict[int, List[Wall]]:
        """
        Group walls by similar angles (parallel walls).

        Args:
            angle_tolerance: Maximum angle difference to consider walls parallel (degrees)

        Returns:
            Dictionary mapping angle groups to lists of parallel walls
        """
        angle_groups = defaultdict(list)

        for wall in self.walls:
            # Normalize angle to 0-180 (since parallel walls can face opposite directions)
            normalized_angle = wall.angle % 180

            # Round to nearest tolerance degree for grouping
            angle_key = round(normalized_angle / angle_tolerance) * angle_tolerance
            angle_groups[angle_key].append(wall)

        # Filter groups with at least 2 walls (potential corridor candidates)
        parallel_groups = {k: v for k, v in angle_groups.items() if len(v) >= 2}

        print(f"Found {len(parallel_groups)} groups of parallel walls")
        for angle, walls in parallel_groups.items():
            print(f"  Angle {angle:.1f}°: {len(walls)} walls")

        return parallel_groups

    def detect_corridor_pairs(self, parallel_walls: List[Wall], max_width: float = 8.0, min_width: float = 1.5) -> List[Tuple[Wall, Wall, float]]:
        """
        Detect pairs of parallel walls that form corridors.

        Args:
            parallel_walls: List of parallel walls
            max_width: Maximum corridor width (meters)
            min_width: Minimum corridor width (meters)

        Returns:
            List of (wall1, wall2, width) tuples representing corridor pairs
        """
        corridor_pairs = []

        # Check each pair of parallel walls
        for i, wall1 in enumerate(parallel_walls):
            for wall2 in parallel_walls[i+1:]:
                # Calculate perpendicular distance between parallel walls
                # Use midpoints for distance calculation
                mid1 = wall1.midpoint()
                mid2 = wall2.midpoint()

                # Calculate perpendicular distance
                # For simplicity, use Euclidean distance (more accurate calculation would project)
                distance = math.sqrt((mid2[0] - mid1[0])**2 + (mid2[1] - mid1[1])**2)

                # Check if walls are within corridor width range
                if min_width <= distance <= max_width:
                    # Check if walls have significant overlap (corridor candidates)
                    # Project walls onto their common axis to check overlap
                    if self._check_wall_overlap(wall1, wall2):
                        corridor_pairs.append((wall1, wall2, distance))

        return corridor_pairs

    def _check_wall_overlap(self, wall1: Wall, wall2: Wall, min_overlap: float = 2.0) -> bool:
        """
        Check if two parallel walls have significant overlap.

        Args:
            wall1, wall2: Walls to check
            min_overlap: Minimum overlap length required (meters)

        Returns:
            True if walls overlap sufficiently
        """
        # For simplicity, check if walls are aligned in the perpendicular direction
        # More accurate implementation would project walls onto common axis

        # Check X-axis overlap for vertical corridors
        if abs(wall1.angle - 90) < 45 or abs(wall1.angle - 270) < 45:
            # Vertical walls - check Y overlap
            wall1_min_y = min(wall1.start_y, wall1.end_y)
            wall1_max_y = max(wall1.start_y, wall1.end_y)
            wall2_min_y = min(wall2.start_y, wall2.end_y)
            wall2_max_y = max(wall2.start_y, wall2.end_y)

            overlap = min(wall1_max_y, wall2_max_y) - max(wall1_min_y, wall2_min_y)
        else:
            # Horizontal walls - check X overlap
            wall1_min_x = min(wall1.start_x, wall1.end_x)
            wall1_max_x = max(wall1.start_x, wall1.end_x)
            wall2_min_x = min(wall2.start_x, wall2.end_x)
            wall2_max_x = max(wall2.start_x, wall2.end_x)

            overlap = min(wall1_max_x, wall2_max_x) - max(wall1_min_x, wall2_min_x)

        return overlap >= min_overlap

    def create_corridor_centerlines(self, corridor_pairs: List[Tuple[Wall, Wall, float]]) -> List[Corridor]:
        """
        Create corridor objects with centerlines from wall pairs.

        Args:
            corridor_pairs: List of (wall1, wall2, width) tuples

        Returns:
            List of Corridor objects
        """
        corridors = []

        for idx, (wall1, wall2, width) in enumerate(corridor_pairs, start=1):
            # Calculate centerline points (midpoints between wall pairs)
            mid1_wall1 = wall1.midpoint()
            mid1_wall2 = wall2.midpoint()

            centerline_mid = (
                (mid1_wall1[0] + mid1_wall2[0]) / 2,
                (mid1_wall1[1] + mid1_wall2[1]) / 2
            )

            # Create centerline as series of points
            # For now, use wall endpoints to define corridor extents
            start_point = (
                (wall1.start_x + wall2.start_x) / 2,
                (wall1.start_y + wall2.start_y) / 2
            )
            end_point = (
                (wall1.end_x + wall2.end_x) / 2,
                (wall1.end_y + wall2.end_y) / 2
            )

            centerline_points = [start_point, centerline_mid, end_point]

            # Calculate corridor length
            corridor_length = math.sqrt(
                (end_point[0] - start_point[0])**2 +
                (end_point[1] - start_point[1])**2
            )

            # Determine corridor direction
            angle = wall1.angle
            if abs(angle) < 45 or abs(angle - 180) < 45:
                direction = 'horizontal'
            elif abs(angle - 90) < 45 or abs(angle - 270) < 45:
                direction = 'vertical'
            else:
                direction = 'diagonal'

            # Classify corridor type (heuristic based on length and width)
            if corridor_length > 20.0 and width > 3.0:
                corridor_type = 'main'
            elif corridor_length > 10.0:
                corridor_type = 'secondary'
            else:
                corridor_type = 'cross'

            corridor = Corridor(
                corridor_id=idx,
                corridor_type=corridor_type,
                centerline_points=centerline_points,
                width=width,
                length=corridor_length,
                direction=direction,
                angle=angle,
                wall_pairs=[(wall1.guid, wall2.guid)]
            )

            corridors.append(corridor)

        return corridors

    def detect_corridors(self) -> List[Corridor]:
        """
        Main corridor detection workflow.

        Returns:
            List of detected Corridor objects
        """
        print("="*80)
        print("CORRIDOR DETECTION - Master Template Charting System")
        print("="*80)

        # Step 1: Load walls
        self.load_walls()

        if len(self.walls) < 4:
            print("ERROR: Not enough walls to detect corridors (need at least 4)")
            return []

        # Step 2: Find parallel walls
        parallel_groups = self.find_parallel_walls(angle_tolerance=5.0)

        # Step 3: Detect corridor pairs from each group
        all_corridor_pairs = []
        for angle, walls in parallel_groups.items():
            pairs = self.detect_corridor_pairs(walls, max_width=8.0, min_width=1.5)
            all_corridor_pairs.extend(pairs)

        print(f"\nFound {len(all_corridor_pairs)} potential corridor pairs")

        # Step 4: Create corridor objects with centerlines
        self.corridors = self.create_corridor_centerlines(all_corridor_pairs)

        # Summary
        print(f"\n{'='*80}")
        print(f"CORRIDOR DETECTION SUMMARY")
        print(f"{'='*80}")
        print(f"Total corridors detected: {len(self.corridors)}")

        main_corridors = [c for c in self.corridors if c.corridor_type == 'main']
        secondary_corridors = [c for c in self.corridors if c.corridor_type == 'secondary']
        cross_corridors = [c for c in self.corridors if c.corridor_type == 'cross']

        print(f"  Main corridors:      {len(main_corridors)}")
        print(f"  Secondary corridors: {len(secondary_corridors)}")
        print(f"  Cross corridors:     {len(cross_corridors)}")

        for corridor in self.corridors:
            print(f"\nCorridor #{corridor.corridor_id} ({corridor.corridor_type}):")
            print(f"  Width: {corridor.width:.2f}m")
            print(f"  Length: {corridor.length:.2f}m")
            print(f"  Direction: {corridor.direction} ({corridor.angle:.1f}°)")
            print(f"  Centerline points: {len(corridor.centerline_points)}")

        print(f"{'='*80}\n")

        return self.corridors


def main():
    """Test corridor detection."""
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: python3 corridor_detection.py <database_path>")
        sys.exit(1)

    db_path = sys.argv[1]
    if not Path(db_path).exists():
        print(f"ERROR: Database not found: {db_path}")
        sys.exit(1)

    detector = CorridorDetector(db_path)
    corridors = detector.detect_corridors()

    print(f"\n✅ Detected {len(corridors)} corridors")
    print("✅ Ready for intelligent routing!")


if __name__ == "__main__":
    main()
