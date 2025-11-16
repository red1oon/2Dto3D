#!/usr/bin/env python3
"""
Extract Wall Rotation Angles from DXF

This script:
1. Reads the source DXF file
2. Extracts actual polyline/line geometry for walls
3. Calculates rotation angle for each wall
4. Updates element_transforms table with rotation_z column

Usage:
    python3 extract_wall_angles.py
"""

import sys
import sqlite3
import math
from pathlib import Path
from typing import Dict, Tuple, Optional

try:
    import ezdxf
except ImportError:
    print("❌ ERROR: ezdxf not installed")
    print("Install: pip install ezdxf")
    sys.exit(1)

# Paths
DXF_PATH = Path(__file__).parent.parent / "SourceFiles/TERMINAL1DXF/01 ARCHITECT/2. BANGUNAN TERMINAL 1.dxf"
DB_PATH = Path(__file__).parent.parent / "Terminal1_MainBuilding_FILTERED.db"

# Spatial filter (same as extraction)
SPATIAL_FILTER = {
    'min_x': -1615047.11,
    'max_x': -1540489.36,
    'min_y': 256575.57,
    'max_y': 309442.97
}

def is_within_spatial_filter(x: float, y: float) -> bool:
    """Check if point is within spatial filter bounding box"""
    return (SPATIAL_FILTER['min_x'] <= x <= SPATIAL_FILTER['max_x'] and
            SPATIAL_FILTER['min_y'] <= y <= SPATIAL_FILTER['max_y'])

def calculate_angle_from_points(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """
    Calculate rotation angle from two points (in radians).
    Returns angle from X-axis (0° = East, 90° = North)
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.atan2(dy, dx)

def get_coordinate_offset_from_db() -> Tuple[float, float, float, float]:
    """Get coordinate normalization parameters from database"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT offset_x, offset_y, offset_z, unit_scale FROM coordinate_metadata LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        return row
    else:
        print("⚠️  No coordinate metadata found, using defaults")
        return (0.0, 0.0, 0.0, 0.001)

def extract_wall_angles_from_dxf() -> Dict[Tuple[float, float], float]:
    """
    Extract wall positions and rotation angles from DXF.

    Returns:
        Dict mapping (center_x, center_y) → rotation_angle_radians
    """
    print("\n" + "="*70)
    print("EXTRACTING WALL ANGLES FROM DXF")
    print("="*70 + "\n")

    # Get coordinate transformation parameters
    offset_x, offset_y, offset_z, unit_scale = get_coordinate_offset_from_db()
    print(f"Using coordinate offset from database:")
    print(f"  Offset: ({offset_x:.2f}, {offset_y:.2f}, {offset_z:.2f}) mm")
    print(f"  Unit scale: {unit_scale} (mm to m)\n")

    print(f"Reading DXF: {DXF_PATH.name}")
    doc = ezdxf.readfile(str(DXF_PATH))
    msp = doc.modelspace()

    wall_angles = {}
    processed_entities = 0

    # Look for entities on wall layers (ARC-WALL, etc.)
    wall_layer_patterns = ['WALL', 'DINDING', 'ARC', 'ARCH']

    for entity in msp:
        layer = entity.dxf.layer.upper()

        # Skip if not a wall-related layer
        if not any(pattern in layer for pattern in wall_layer_patterns):
            continue

        # Extract geometry based on entity type
        points = []

        if entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            if is_within_spatial_filter(start.x, start.y):
                points = [(start.x, start.y), (end.x, end.y)]

        elif entity.dxftype() == 'POLYLINE':
            for vertex in entity.vertices:
                if hasattr(vertex, 'dxf') and hasattr(vertex.dxf, 'location'):
                    loc = vertex.dxf.location
                    if is_within_spatial_filter(loc.x, loc.y):
                        points.append((loc.x, loc.y))

        elif entity.dxftype() == 'LWPOLYLINE':
            for point in entity.get_points('xy'):
                if is_within_spatial_filter(point[0], point[1]):
                    points.append((point[0], point[1]))

        elif entity.dxftype() == 'INSERT':
            # Block insert - use insertion point
            insert_point = entity.dxf.insert
            if is_within_spatial_filter(insert_point.x, insert_point.y):
                # Use block rotation if available
                rotation_deg = getattr(entity.dxf, 'rotation', 0.0)
                rotation_rad = math.radians(rotation_deg)

                # Apply coordinate normalization
                center_x = (insert_point.x - offset_x) * unit_scale
                center_y = (insert_point.y - offset_y) * unit_scale

                wall_angles[(center_x, center_y)] = rotation_rad
                processed_entities += 1

        # Process line/polyline points
        if len(points) >= 2:
            # Calculate angle from first segment
            angle = calculate_angle_from_points(points[0], points[1])

            # Calculate center point (apply same transformation as DB extraction)
            raw_center_x = sum(p[0] for p in points) / len(points)
            raw_center_y = sum(p[1] for p in points) / len(points)

            # Apply coordinate normalization (same as dxf_to_database.py)
            center_x = (raw_center_x - offset_x) * unit_scale
            center_y = (raw_center_y - offset_y) * unit_scale

            wall_angles[(center_x, center_y)] = angle
            processed_entities += 1

    print(f"✅ Processed {processed_entities:,} wall entities")
    print(f"✅ Extracted {len(wall_angles):,} unique wall positions with angles\n")

    # Show angle distribution
    angle_deg_list = [math.degrees(a) % 360 for a in wall_angles.values()]
    if angle_deg_list:
        print("Angle distribution (degrees):")
        print(f"  Min: {min(angle_deg_list):.1f}°")
        print(f"  Max: {max(angle_deg_list):.1f}°")
        print(f"  Mean: {sum(angle_deg_list)/len(angle_deg_list):.1f}°")

        # Count angles in 45° bins
        bins = {0: 0, 45: 0, 90: 0, 135: 0, 180: 0, 225: 0, 270: 0, 315: 0}
        for angle in angle_deg_list:
            bin_key = min(bins.keys(), key=lambda k: abs(angle - k))
            bins[bin_key] += 1

        print("\n  Direction bins:")
        for deg, count in sorted(bins.items()):
            if count > 0:
                bar = "█" * (count // 5 or 1)
                print(f"    {deg:3d}°: {count:4d} walls {bar}")

    return wall_angles

def find_closest_wall(wall_angles: Dict, target_x: float, target_y: float,
                     max_distance: float = 2.0) -> Optional[float]:
    """
    Find the closest wall angle to a given position.

    Args:
        wall_angles: Dict of (x, y) → angle
        target_x, target_y: Target position (meters)
        max_distance: Maximum search radius (meters)

    Returns:
        Rotation angle in radians, or None if no match found
    """
    best_distance = max_distance
    best_angle = None

    for (wx, wy), angle in wall_angles.items():
        distance = math.sqrt((wx - target_x)**2 + (wy - target_y)**2)
        if distance < best_distance:
            best_distance = distance
            best_angle = angle

    return best_angle

def update_database_with_angles(wall_angles: Dict):
    """
    Update element_transforms table with rotation_z column.
    Match walls by proximity to DXF wall positions.
    """
    print("="*70)
    print("UPDATING DATABASE WITH ROTATION ANGLES")
    print("="*70 + "\n")

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Step 1: Add rotation_z column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE element_transforms ADD COLUMN rotation_z REAL DEFAULT 0.0")
        print("✅ Added rotation_z column to element_transforms")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("✅ rotation_z column already exists")
        else:
            raise

    # Step 2: Get all walls from database
    cursor.execute("""
        SELECT m.guid, t.center_x, t.center_y, m.ifc_class
        FROM elements_meta m
        JOIN element_transforms t ON m.guid = t.guid
        WHERE m.ifc_class IN ('IfcWall', 'IfcDoor', 'IfcWindow')
        ORDER BY m.ifc_class, t.center_x, t.center_y
    """)

    elements = cursor.fetchall()
    print(f"Found {len(elements):,} wall/door/window elements to update\n")

    # Step 3: Match elements to DXF walls and update rotation
    matched = 0
    unmatched = 0

    for guid, cx, cy, ifc_class in elements:
        # Find closest wall angle
        angle = find_closest_wall(wall_angles, cx, cy, max_distance=2.0)

        if angle is not None:
            cursor.execute("""
                UPDATE element_transforms
                SET rotation_z = ?
                WHERE guid = ?
            """, (angle, guid))
            matched += 1
        else:
            # Keep default 0.0 rotation
            unmatched += 1

    conn.commit()

    # Step 4: Verify updates
    cursor.execute("""
        SELECT COUNT(DISTINCT rotation_z) as unique_angles
        FROM element_transforms
        WHERE rotation_z IS NOT NULL
    """)
    unique_angles = cursor.fetchone()[0]

    print(f"✅ Matched: {matched:,} elements")
    print(f"⚠️  Unmatched: {unmatched:,} elements (will use 0° default)")
    print(f"✅ Unique rotation angles in database: {unique_angles}")

    # Show sample of updated data
    print("\nSample of updated rotations:")
    cursor.execute("""
        SELECT m.ifc_class, t.center_x, t.center_y, t.rotation_z
        FROM elements_meta m
        JOIN element_transforms t ON m.guid = t.guid
        WHERE m.ifc_class = 'IfcWall'
        AND t.rotation_z != 0
        ORDER BY RANDOM()
        LIMIT 10
    """)

    print(f"{'IFC Class':<20} {'Position (X, Y)':<25} {'Rotation'}")
    print("-"*70)
    for ifc_class, cx, cy, rot_z in cursor.fetchall():
        rot_deg = math.degrees(rot_z) % 360
        print(f"{ifc_class:<20} ({cx:7.2f}, {cy:7.2f})  {rot_deg:6.1f}°")

    conn.close()
    print("\n" + "="*70)
    print("DATABASE UPDATE COMPLETE")
    print("="*70 + "\n")

def main():
    if not DXF_PATH.exists():
        print(f"❌ DXF file not found: {DXF_PATH}")
        sys.exit(1)

    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        sys.exit(1)

    # Extract angles from DXF
    wall_angles = extract_wall_angles_from_dxf()

    if not wall_angles:
        print("❌ No wall angles extracted from DXF")
        sys.exit(1)

    # Update database
    update_database_with_angles(wall_angles)

    print("\n✅ SUCCESS! Wall rotation angles extracted and stored.")
    print("\nNext step: Run geometry generation script to apply rotations")
    print("  python3 Scripts/generate_3d_geometry.py Terminal1_MainBuilding_FILTERED.db")

if __name__ == "__main__":
    main()
