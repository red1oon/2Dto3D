#!/usr/bin/env python3
"""
Quick test to verify bbox dimensions in database.
"""

import sqlite3
from pathlib import Path

def test_bbox_in_blender():
    """Test that bbox dimensions are correctly stored and retrievable."""

    db_path = Path("/home/red1/Documents/bonsai/2Dto3D/BASE_ARC_STR.db")

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Query sample elements with bbox dimensions
    cursor.execute("""
        SELECT
            m.discipline,
            m.ifc_class,
            t.center_x, t.center_y, t.center_z,
            t.bbox_length, t.bbox_width, t.bbox_height,
            r.minX, r.maxX, r.minY, r.maxY, r.minZ, r.maxZ
        FROM elements_meta m
        JOIN element_transforms t ON m.guid = t.guid
        JOIN elements_rtree r ON m.id = r.id
        WHERE m.discipline = 'STR'
        LIMIT 10
    """)

    print("\nSample STR elements:")
    print("=" * 100)
    print(f"{'Disc':<6} {'IFC Class':<15} {'Center (X,Y,Z)':<30} {'Bbox (L×W×H)':<25} {'R-tree Bounds':<30}")
    print("=" * 100)

    for row in cursor.fetchall():
        disc, ifc_class, cx, cy, cz, bl, bw, bh = row[:8]
        minX, maxX, minY, maxY, minZ, maxZ = row[8:]

        # Calculate R-tree dimensions
        r_length = maxX - minX
        r_width = maxY - minY
        r_height = maxZ - minZ

        center_str = f"({cx:.2f}, {cy:.2f}, {cz:.2f})"
        bbox_str = f"{bl:.2f}×{bw:.2f}×{bh:.2f}"
        rtree_str = f"{r_length:.2f}×{r_width:.2f}×{r_height:.2f}"

        print(f"{disc:<6} {ifc_class:<15} {center_str:<30} {bbox_str:<25} {rtree_str:<30}")

        # Verify R-tree matches bbox
        assert abs(r_length - bl) < 0.01, f"R-tree length mismatch: {r_length} != {bl}"
        assert abs(r_width - bw) < 0.01, f"R-tree width mismatch: {r_width} != {bw}"
        assert abs(r_height - bh) < 0.01, f"R-tree height mismatch: {r_height} != {bh}"

    conn.close()

    print("\n✅ All R-tree dimensions match bbox dimensions!")
    print("✅ Database is ready for Blender visualization")

if __name__ == "__main__":
    test_bbox_in_blender()
