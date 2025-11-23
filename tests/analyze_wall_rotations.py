#!/usr/bin/env python3
"""
Analyze wall rotations from the database WITHOUT Blender.
This will show us the rotation issue directly from the geometry data.
"""

import sqlite3
import struct
import math
from pathlib import Path

DB_PATH = Path(__file__).parent / "Terminal1_MainBuilding_FILTERED.db"

def unpack_vertices(vertices_blob):
    """Unpack vertices blob into list of (x,y,z) tuples"""
    num_floats = len(vertices_blob) // 4
    floats = struct.unpack(f'{num_floats}f', vertices_blob)
    verts = [(floats[i], floats[i+1], floats[i+2])
             for i in range(0, len(floats), 3)]
    return verts

def calculate_wall_angle(verts):
    """
    Calculate wall rotation angle from its vertices.
    Assumes wall is an extruded rectangle (8 vertices).
    Returns angle in degrees from X-axis.
    """
    if len(verts) < 8:
        return None

    # For a box/rectangle, get bottom face edge (first 4 vertices form bottom)
    # Edge direction: from vertex 0 to vertex 1
    v0 = verts[0]
    v1 = verts[1]

    # Calculate angle in XY plane
    dx = v1[0] - v0[0]
    dy = v1[1] - v0[1]

    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)

    return angle_deg

def main():
    print("\n" + "="*70)
    print("ANALYZING WALL ROTATION ANGLES FROM DATABASE")
    print("="*70 + "\n")

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Query walls
    query = """
        SELECT
            m.guid,
            t.center_x,
            t.center_y,
            t.center_z,
            bg.vertices
        FROM elements_meta m
        JOIN element_transforms t ON m.guid = t.guid
        JOIN base_geometries bg ON m.guid = bg.guid
        WHERE m.ifc_class = 'IfcWall'
        AND bg.vertices IS NOT NULL
        ORDER BY t.center_x, t.center_y
        LIMIT 30
    """

    cursor.execute(query)
    walls = cursor.fetchall()

    print(f"Analyzing {len(walls)} walls...\n")

    angles = []
    angle_counts = {}

    print(f"{'#':<4} {'Center Position':<30} {'Angle':<10} {'Orientation'}")
    print("-"*70)

    for idx, (guid, cx, cy, cz, verts_blob) in enumerate(walls, 1):
        verts = unpack_vertices(verts_blob)
        angle = calculate_wall_angle(verts)

        if angle is not None:
            angles.append(angle)

            # Round to nearest degree for grouping
            rounded = round(angle)
            angle_counts[rounded] = angle_counts.get(rounded, 0) + 1

            # Determine orientation
            abs_angle = abs(angle) % 180
            if abs_angle < 22.5 or abs_angle > 157.5:
                orientation = "Horizontal (E-W)"
            elif 67.5 < abs_angle < 112.5:
                orientation = "Vertical (N-S)"
            else:
                orientation = "Diagonal"

            print(f"{idx:<4} ({cx:7.2f}, {cy:7.2f}, {cz:5.2f})  "
                  f"{angle:7.1f}°  {orientation}")

    conn.close()

    # Summary statistics
    print("\n" + "="*70)
    print("ROTATION ANALYSIS SUMMARY")
    print("="*70 + "\n")

    if angles:
        print(f"Total walls analyzed: {len(angles)}")
        print(f"Unique angles (rounded): {len(angle_counts)}")
        print(f"Min angle: {min(angles):.1f}°")
        print(f"Max angle: {max(angles):.1f}°")
        print(f"Mean angle: {sum(angles)/len(angles):.1f}°")

        print("\nAngle distribution:")
        for angle in sorted(angle_counts.keys()):
            count = angle_counts[angle]
            bar = "█" * (count // 2)
            print(f"  {angle:4.0f}°: {count:3d} walls {bar}")

        print("\n" + "-"*70)

        if len(angle_counts) == 1:
            print("⚠️  ISSUE CONFIRMED: ALL WALLS HAVE THE SAME ROTATION ANGLE!")
            print("\nThis is the problem shown in the screenshot:")
            print("  - Current: All walls point the same direction")
            print("  - Expected: Walls at different angles forming building layout")
            print("\nFIX NEEDED: Extract actual wall angles from DXF polylines")
        elif len(angle_counts) <= 3:
            print("⚠️  LIMITED ROTATION DIVERSITY")
            print(f"Only {len(angle_counts)} unique angles detected.")
            print("Most buildings have walls at many different angles.")
        else:
            print("✅ GOOD: Walls have diverse rotation angles")
            print("This suggests the rotation data is being extracted correctly.")

    else:
        print("No wall angles could be calculated.")

    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
