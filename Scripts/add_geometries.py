#!/usr/bin/env python3
"""
Add Simple Geometries to Generated Database

Creates placeholder box geometries for visualization in Blender.
Each element gets a simple 1m cube at its position for now.

Usage:
    python3 add_geometries.py <database_path>
"""

import sys
import sqlite3
import struct
from pathlib import Path


def create_box_mesh(x, y, z, width=1.0, height=1.0, depth=1.0):
    """
    Create a simple box mesh as a binary blob.

    Returns tessellated mesh data in a simple format:
    - 4 bytes: vertex count
    - 4 bytes: face count
    - Vertices: count * (3 floats for x,y,z)
    - Faces: count * (3 ints for triangle indices)
    """
    # Box vertices (8 corners)
    hw, hh, hd = width/2, height/2, depth/2
    vertices = [
        (x-hw, y-hd, z-hh),  # 0: front-bottom-left
        (x+hw, y-hd, z-hh),  # 1: front-bottom-right
        (x+hw, y+hd, z-hh),  # 2: back-bottom-right
        (x-hw, y+hd, z-hh),  # 3: back-bottom-left
        (x-hw, y-hd, z+hh),  # 4: front-top-left
        (x+hw, y-hd, z+hh),  # 5: front-top-right
        (x+hw, y+hd, z+hh),  # 6: back-top-right
        (x-hw, y+hd, z+hh),  # 7: back-top-left
    ]

    # Box faces (12 triangles, 2 per face)
    faces = [
        # Bottom
        (0, 1, 2), (0, 2, 3),
        # Top
        (4, 6, 5), (4, 7, 6),
        # Front
        (0, 5, 1), (0, 4, 5),
        # Back
        (3, 2, 6), (3, 6, 7),
        # Left
        (0, 3, 7), (0, 7, 4),
        # Right
        (1, 5, 6), (1, 6, 2),
    ]

    # Pack into binary format
    data = bytearray()

    # Header: vertex count, face count
    data.extend(struct.pack('I', len(vertices)))
    data.extend(struct.pack('I', len(faces)))

    # Vertices (x, y, z as floats)
    for vx, vy, vz in vertices:
        data.extend(struct.pack('fff', vx, vy, vz))

    # Faces (indices as ints)
    for f0, f1, f2 in faces:
        data.extend(struct.pack('III', f0, f1, f2))

    return bytes(data)


def get_element_size(ifc_class, entity_count_in_layer=1):
    """Estimate reasonable size for element based on IFC class."""
    # Size heuristics (width, height, depth in meters)
    # Realistic building element sizes for visualization
    sizes = {
        'IfcWall': (0.2, 3.0, 0.15),          # 200mm thick, 3m tall, 150mm wide segment
        'IfcWindow': (1.2, 1.5, 0.1),         # 1.2m wide, 1.5m tall, 100mm frame
        'IfcDoor': (1.0, 2.1, 0.05),          # 1m wide, 2.1m tall, 50mm thick
        'IfcColumn': (0.4, 3.0, 0.4),         # 400mm × 400mm, 3m tall
        'IfcBeam': (0.3, 0.5, 2.0),           # 300mm wide, 500mm deep, 2m span
        'IfcSlab': (3.0, 3.0, 0.2),           # 3m × 3m area, 200mm thick
        'IfcFurniture': (0.6, 0.6, 0.8),      # Chair/desk size
        'IfcPipeSegment': (0.1, 0.1, 1.0),    # 100mm diameter, 1m segment
        'IfcDuctSegment': (0.4, 0.3, 1.0),    # 400×300mm duct, 1m segment
        'IfcLightFixture': (0.3, 0.3, 0.1),   # 300mm × 300mm fixture
        'IfcFireSuppressionTerminal': (0.1, 0.1, 0.1),  # Sprinkler head
        'IfcAirTerminal': (0.4, 0.4, 0.2),    # Diffuser
        'IfcBuildingElementProxy': (0.5, 0.5, 0.5),  # Generic 500mm cube
    }

    return sizes.get(ifc_class, (0.5, 0.5, 0.5))  # Default 500mm cube


def add_geometries_to_database(db_path):
    """Add placeholder box geometries to all elements."""
    db_path = Path(db_path)

    if not db_path.exists():
        print(f"❌ Error: Database not found: {db_path}")
        return False

    print(f"📂 Opening database: {db_path.name}")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # base_geometries table should already exist from dxf_to_database.py
    # Check and create if missing
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='base_geometries'")
    if not cursor.fetchone():
        print("💾 Creating base_geometries table...")
        cursor.execute("""
            CREATE TABLE base_geometries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guid TEXT UNIQUE,
                geometry_hash TEXT,
                vertices BLOB,
                faces BLOB,
                normals BLOB
            )
        """)
        cursor.execute("CREATE INDEX idx_geometries_guid ON base_geometries(guid)")
    else:
        # Clear existing geometries for regeneration
        print("⚠️  Clearing existing geometries...")
        cursor.execute("DELETE FROM base_geometries")

    # Get all elements with positions and IFC classes
    print("🎯 Fetching element positions...")
    cursor.execute("""
        SELECT
            m.guid,
            m.ifc_class,
            t.center_x,
            t.center_y,
            t.center_z
        FROM elements_meta m
        JOIN element_transforms t ON m.guid = t.guid
    """)

    elements = cursor.fetchall()
    print(f"✅ Found {len(elements)} elements")

    # Generate geometries
    print("🔨 Generating box geometries...")
    inserted = 0

    for guid, ifc_class, x, y, z in elements:
        # Get appropriate size for this element type
        width, height, depth = get_element_size(ifc_class)

        # Create box mesh
        geometry_blob = create_box_mesh(x, y, z, width, height, depth)

        # Calculate bounding box
        hw, hh, hd = width/2, height/2, depth/2
        bbox_min_x, bbox_min_y, bbox_min_z = x-hw, y-hd, z-hh
        bbox_max_x, bbox_max_y, bbox_max_z = x+hw, y+hd, z+hh

        # Insert geometry into base_geometries
        # element_geometry is a VIEW of this table, so only insert here
        cursor.execute("""
            INSERT INTO base_geometries
            (guid, geometry_hash, vertices, faces, normals)
            VALUES (?, ?, ?, ?, ?)
        """, (guid, f"hash_{guid[:8]}", geometry_blob, geometry_blob, None))

        inserted += 1

        if inserted % 1000 == 0:
            print(f"  Progress: {inserted}/{len(elements)} ({inserted/len(elements)*100:.1f}%)")

    conn.commit()

    # Update R-tree with actual geometry bounding boxes
    print("\n🗺️  Updating R-tree spatial index with actual geometry sizes...")
    cursor.execute("DELETE FROM elements_rtree")

    for guid, ifc_class, x, y, z in elements:
        # Get element ID
        cursor.execute("SELECT id FROM elements_meta WHERE guid = ?", (guid,))
        elem_id = cursor.fetchone()[0]

        # Get appropriate size for this element type
        width, height, depth = get_element_size(ifc_class)

        # Calculate bounding box (same as geometry)
        hw, hh, hd = width/2, height/2, depth/2
        bbox_min_x, bbox_min_y, bbox_min_z = x-hw, y-hd, z-hh
        bbox_max_x, bbox_max_y, bbox_max_z = x+hw, y+hd, z+hh

        # Update R-tree with actual bbox (in meters, not placeholder 1m)
        cursor.execute("""
            INSERT INTO elements_rtree (id, minX, maxX, minY, maxY, minZ, maxZ)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (elem_id, bbox_min_x, bbox_max_x, bbox_min_y, bbox_max_y, bbox_min_z, bbox_max_z))

    conn.commit()
    print(f"   ✅ Updated {len(elements)} R-tree entries with actual geometry sizes")

    # Add spatial_structure table (simplified for now)
    print("\n🏗️  Creating spatial_structure table...")
    cursor.execute("DROP TABLE IF EXISTS spatial_structure")
    cursor.execute("""
        CREATE TABLE spatial_structure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guid TEXT UNIQUE NOT NULL,
            parent_guid TEXT,
            name TEXT,
            storey TEXT,
            elevation REAL
        )
    """)

    # Create simple building structure
    building_guid = "building-0001"
    storey_guid = "storey-ground"

    cursor.execute("""
        INSERT INTO spatial_structure (guid, parent_guid, name, storey, elevation)
        VALUES (?, NULL, ?, NULL, ?)
    """, (building_guid, "Terminal 1", 0.0))

    cursor.execute("""
        INSERT INTO spatial_structure (guid, parent_guid, name, storey, elevation)
        VALUES (?, ?, ?, ?, ?)
    """, (storey_guid, building_guid, "Ground Floor", "Ground", 0.0))

    # Link all elements to ground floor
    cursor.execute("""
        INSERT INTO spatial_structure (guid, parent_guid, name, storey, elevation)
        SELECT guid, ?, element_name, 'Ground', 0.0
        FROM elements_meta
    """, (storey_guid,))

    conn.commit()
    conn.close()

    print(f"\n✅ Successfully added geometries to {inserted} elements")
    print(f"📊 Database stats:")
    print(f"   - Elements: {len(elements)}")
    print(f"   - Geometries: {inserted}")
    print(f"   - Building structure: 1 building + 1 storey")

    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 add_geometries.py <database_path>")
        print("\nExample:")
        print("  python3 add_geometries.py Generated_Terminal1_SAMPLE.db")
        sys.exit(1)

    db_path = sys.argv[1]
    success = add_geometries_to_database(db_path)

    if success:
        print("\n🎉 Database ready for Blender!")
        print("\nNext step:")
        print("  1. Open Blender with Bonsai")
        print("  2. Run the import script")
        print("  3. Elements should appear in 3D viewport")
    else:
        print("\n❌ Failed to add geometries")
        sys.exit(1)


if __name__ == '__main__':
    main()
