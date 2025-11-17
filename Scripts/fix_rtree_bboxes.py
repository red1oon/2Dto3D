#!/usr/bin/env python3
"""
Fix R-tree Bounding Boxes from Actual Geometry
===============================================

Problem: elements_rtree populated with 1m placeholder cubes
Solution: Calculate ACTUAL bounding boxes from base_geometries vertices

This script:
1. Reads actual geometry from base_geometries table
2. Calculates tight bounding box for each element
3. Updates elements_rtree with correct dimensions

Expected result: Preview mode shows proper element shapes/sizes
"""

import sqlite3
import struct
import sys
from pathlib import Path


def unpack_vertices(blob):
    """
    Unpack binary vertex data to list of (x, y, z) tuples.
    Format: Little-endian floats, 3 per vertex (12 bytes each)
    """
    if not blob:
        return []

    num_floats = len(blob) // 4
    vertices = []

    for i in range(0, num_floats, 3):
        offset = i * 4
        x, y, z = struct.unpack('<fff', blob[offset:offset+12])
        vertices.append((x, y, z))

    return vertices


def calculate_bbox(vertices):
    """
    Calculate tight axis-aligned bounding box from vertices.

    Returns: (minX, maxX, minY, maxY, minZ, maxZ)
    """
    if not vertices:
        # Fallback to 1m cube if no vertices
        return (-0.5, 0.5, -0.5, 0.5, -0.5, 0.5)

    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]

    return (
        min(xs), max(xs),
        min(ys), max(ys),
        min(zs), max(zs)
    )


def fix_rtree_bboxes(db_path):
    """
    Recalculate and update rtree bounding boxes from actual geometry.
    """
    print("="*80)
    print("FIXING R-TREE BOUNDING BOXES")
    print("="*80)
    print(f"Database: {db_path}\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all elements with geometry
    print("Reading geometry data...")
    cursor.execute("""
        SELECT
            m.id,
            m.guid,
            m.ifc_class,
            bg.vertices
        FROM elements_meta m
        JOIN base_geometries bg ON m.guid = bg.guid
        ORDER BY m.id
    """)

    elements = cursor.fetchall()
    print(f"Found {len(elements)} elements with geometry\n")

    if not elements:
        print("ERROR: No geometry found in base_geometries table!")
        print("Run generate_3d_geometry.py first to create geometry.")
        conn.close()
        return False

    # Process each element
    print("Calculating tight bounding boxes...")
    updates = []
    stats = {
        'total': len(elements),
        'updated': 0,
        'failed': 0,
        'dimensions': {}
    }

    for element_id, guid, ifc_class, vertices_blob in elements:
        try:
            # Unpack vertices
            vertices = unpack_vertices(vertices_blob)

            if not vertices:
                print(f"  WARNING: {guid} ({ifc_class}) has no vertices!")
                stats['failed'] += 1
                continue

            # Calculate tight bbox
            minX, maxX, minY, maxY, minZ, maxZ = calculate_bbox(vertices)

            # Store for batch update
            updates.append((
                minX, maxX, minY, maxY, minZ, maxZ,
                element_id
            ))

            # Track statistics
            width = maxX - minX
            depth = maxY - minY
            height = maxZ - minZ

            key = f"{width:.2f}×{depth:.2f}×{height:.2f}"
            if key not in stats['dimensions']:
                stats['dimensions'][key] = {'count': 0, 'classes': set()}
            stats['dimensions'][key]['count'] += 1
            stats['dimensions'][key]['classes'].add(ifc_class)

            stats['updated'] += 1

            if stats['updated'] % 100 == 0:
                print(f"  Processed {stats['updated']}/{stats['total']} elements...")

        except Exception as e:
            print(f"  ERROR processing {guid} ({ifc_class}): {e}")
            stats['failed'] += 1

    # Batch update rtree
    print(f"\nUpdating R-tree with {len(updates)} bounding boxes...")
    cursor.executemany("""
        UPDATE elements_rtree
        SET minX = ?, maxX = ?,
            minY = ?, maxY = ?,
            minZ = ?, maxZ = ?
        WHERE id = ?
    """, updates)

    conn.commit()

    # Verify updates
    print("\nVerifying rtree updates...")
    cursor.execute("""
        SELECT
            m.ifc_class,
            ROUND(r.maxX - r.minX, 2) as width,
            ROUND(r.maxY - r.minY, 2) as depth,
            ROUND(r.maxZ - r.minZ, 2) as height,
            COUNT(*) as count
        FROM elements_rtree r
        JOIN elements_meta m ON r.id = m.id
        GROUP BY m.ifc_class, width, depth, height
        ORDER BY m.ifc_class, count DESC
        LIMIT 20
    """)

    print("\n" + "="*80)
    print("TOP 20 BBOX DIMENSIONS BY IFC CLASS")
    print("="*80)
    print(f"{'IFC Class':<30} {'Width':<8} {'Depth':<8} {'Height':<8} {'Count':<6}")
    print("-"*80)

    for ifc_class, width, depth, height, count in cursor.fetchall():
        print(f"{ifc_class:<30} {width:<8.2f} {depth:<8.2f} {height:<8.2f} {count:<6}")

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total elements:     {stats['total']}")
    print(f"Updated:            {stats['updated']}")
    print(f"Failed:             {stats['failed']}")
    print(f"Success rate:       {stats['updated']/stats['total']*100:.1f}%")

    print(f"\nUnique dimensions found: {len(stats['dimensions'])}")
    if len(stats['dimensions']) <= 10:
        print("\nAll dimensions:")
        for dim, info in sorted(stats['dimensions'].items(), key=lambda x: -x[1]['count']):
            classes = ', '.join(sorted(info['classes']))
            print(f"  {dim:20} ({info['count']:4} elements) - {classes}")
    else:
        print("\nTop 10 dimensions:")
        for dim, info in sorted(stats['dimensions'].items(), key=lambda x: -x[1]['count'])[:10]:
            classes = ', '.join(sorted(info['classes']))
            print(f"  {dim:20} ({info['count']:4} elements) - {classes}")

    conn.close()

    print("\n" + "="*80)
    print("✅ R-TREE BOUNDING BOXES UPDATED!")
    print("="*80)
    print("\nNext steps:")
    print("1. Open database in Blender (Preview mode)")
    print("2. Elements should now show actual shapes/sizes")
    print("3. Walls should be rectangles (not cubes)")
    print("4. Columns should be tall and narrow")
    print("="*80)

    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fix_rtree_bboxes.py <database_path>")
        print("\nExample:")
        print("  python3 fix_rtree_bboxes.py Terminal1_MainBuilding_FILTERED.db")
        sys.exit(1)

    db_path = Path(sys.argv[1])

    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        sys.exit(1)

    success = fix_rtree_bboxes(str(db_path))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
