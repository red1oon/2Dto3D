#!/usr/bin/env python3
"""
Generate Simple POC Database for Viewport Validation
=====================================================

Creates a minimal database with known, simple geometry:
- 1 box (10m x 5m x 3m) at origin
- 4 columns (0.5m diameter, 3m height) at corners
- 1 beam (10m long) connecting two columns

This allows easy visual verification that audit matches viewport.
"""

import sqlite3
import struct
import uuid
import math
from pathlib import Path
from datetime import datetime

# Output path
OUTPUT_DIR = Path(__file__).parent.parent / "DatabaseFiles"
OUTPUT_DB = OUTPUT_DIR / "POC_Validation.db"

# =============================================================================
# GEOMETRY HELPERS
# =============================================================================

def pack_vertices(vertices):
    return struct.pack(f'<{len(vertices)*3}f', *[c for v in vertices for c in v])

def pack_faces(faces):
    return struct.pack(f'<{len(faces)*3}I', *[i for f in faces for i in f])

def make_box(cx, cy, cz, width, depth, height):
    """Create box vertices and faces at world position."""
    hx, hy = width/2, depth/2
    vertices = [
        (cx-hx, cy-hy, cz), (cx+hx, cy-hy, cz), (cx+hx, cy+hy, cz), (cx-hx, cy+hy, cz),
        (cx-hx, cy-hy, cz+height), (cx+hx, cy-hy, cz+height),
        (cx+hx, cy+hy, cz+height), (cx-hx, cy+hy, cz+height),
    ]
    faces = [
        (0, 1, 2), (0, 2, 3),  # Bottom
        (4, 7, 6), (4, 6, 5),  # Top
        (0, 4, 5), (0, 5, 1),  # Front
        (2, 6, 7), (2, 7, 3),  # Back
        (0, 3, 7), (0, 7, 4),  # Left
        (1, 5, 6), (1, 6, 2),  # Right
    ]
    return vertices, faces

def make_cylinder(cx, cy, cz, radius, height, segments=12):
    """Create cylinder vertices and faces at world position."""
    vertices = [(cx, cy, cz)]  # Bottom center
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        vertices.append((cx + radius * math.cos(angle),
                        cy + radius * math.sin(angle), cz))

    vertices.append((cx, cy, cz + height))  # Top center
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        vertices.append((cx + radius * math.cos(angle),
                        cy + radius * math.sin(angle), cz + height))

    faces = []
    # Bottom cap
    for i in range(segments):
        faces.append((0, 1 + (i + 1) % segments, 1 + i))
    # Top cap
    top_center = segments + 1
    for i in range(segments):
        faces.append((top_center, top_center + 1 + i, top_center + 1 + (i + 1) % segments))
    # Side faces
    for i in range(segments):
        b1 = 1 + i
        b2 = 1 + (i + 1) % segments
        t1 = top_center + 1 + i
        t2 = top_center + 1 + (i + 1) % segments
        faces.append((b1, b2, t2))
        faces.append((b1, t2, t1))

    return vertices, faces

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("POC VALIDATION DATABASE GENERATOR")
    print("=" * 70)

    # Clean up
    if OUTPUT_DB.exists():
        OUTPUT_DB.unlink()
        print(f"Deleted existing: {OUTPUT_DB.name}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(OUTPUT_DB))
    cursor = conn.cursor()

    # Create schema
    cursor.executescript("""
        CREATE TABLE base_geometries (
            geometry_hash TEXT PRIMARY KEY,
            vertices BLOB NOT NULL,
            faces BLOB NOT NULL,
            normals BLOB,
            vertex_count INTEGER NOT NULL,
            face_count INTEGER NOT NULL
        );

        CREATE TABLE element_instances (
            guid TEXT PRIMARY KEY,
            geometry_hash TEXT NOT NULL
        );

        CREATE TABLE elements_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guid TEXT UNIQUE NOT NULL,
            discipline TEXT NOT NULL,
            ifc_class TEXT NOT NULL,
            filepath TEXT,
            element_name TEXT,
            element_type TEXT,
            element_description TEXT,
            storey TEXT,
            material_name TEXT,
            material_rgba TEXT
        );

        CREATE TABLE element_transforms (
            guid TEXT PRIMARY KEY,
            center_x REAL NOT NULL,
            center_y REAL NOT NULL,
            center_z REAL NOT NULL,
            rotation_z REAL DEFAULT 0.0,
            length REAL
        );

        CREATE TABLE global_offset (
            offset_x REAL, offset_y REAL, offset_z REAL
        );

        CREATE VIEW element_geometry AS
        SELECT ei.guid, ei.geometry_hash, bg.vertices, bg.faces,
               bg.vertex_count, bg.face_count, bg.normals
        FROM element_instances ei
        JOIN base_geometries bg ON ei.geometry_hash = bg.geometry_hash;

        CREATE VIRTUAL TABLE elements_rtree USING rtree(
            id, minX, maxX, minY, maxY, minZ, maxZ
        );
    """)

    # ==========================================================================
    # CREATE KNOWN GEOMETRY
    # ==========================================================================

    elements = []

    # 1. Main building box: 10m x 5m x 3m at origin
    print("\nCreating elements:")
    print("  1. Box: 10m x 5m x 3m at (0, 0, 0)")
    box_verts, box_faces = make_box(0, 0, 0, 10, 5, 3)
    elements.append({
        'guid': str(uuid.uuid4()).replace('-', '')[:22],
        'ifc_class': 'IfcWall',
        'discipline': 'ARC',
        'storey': '1F',
        'vertices': box_verts,
        'faces': box_faces,
        'center': (0, 0, 1.5),
        'length': 10
    })

    # 2. Four columns at corners
    col_positions = [(-4, -2), (4, -2), (4, 2), (-4, 2)]
    for i, (cx, cy) in enumerate(col_positions):
        print(f"  {i+2}. Column: 0.5m dia x 3m at ({cx}, {cy}, 0)")
        cyl_verts, cyl_faces = make_cylinder(cx, cy, 0, 0.25, 3)
        elements.append({
            'guid': str(uuid.uuid4()).replace('-', '')[:22],
            'ifc_class': 'IfcColumn',
            'discipline': 'STR',
            'storey': '1F',
            'vertices': cyl_verts,
            'faces': cyl_faces,
            'center': (cx, cy, 1.5),
            'length': 0.5
        })

    # 3. Beam connecting front columns
    print("  6. Beam: 8m x 0.3m x 0.5m at (0, -2, 2.5)")
    beam_verts, beam_faces = make_box(0, -2, 2.5, 8, 0.3, 0.5)
    elements.append({
        'guid': str(uuid.uuid4()).replace('-', '')[:22],
        'ifc_class': 'IfcBeam',
        'discipline': 'STR',
        'storey': '1F',
        'vertices': beam_verts,
        'faces': beam_faces,
        'center': (0, -2, 2.75),
        'length': 8
    })

    # ==========================================================================
    # INSERT INTO DATABASE
    # ==========================================================================

    print("\nInserting into database...")

    for i, elem in enumerate(elements):
        guid = elem['guid']
        vertices = elem['vertices']
        faces = elem['faces']

        # Geometry hash
        v_blob = pack_vertices(vertices)
        f_blob = pack_faces(faces)
        geom_hash = f"poc_geom_{i}"

        # Insert geometry
        cursor.execute("""
            INSERT INTO base_geometries (geometry_hash, vertices, faces, vertex_count, face_count)
            VALUES (?, ?, ?, ?, ?)
        """, (geom_hash, v_blob, f_blob, len(vertices), len(faces)))

        # Insert instance
        cursor.execute("INSERT INTO element_instances VALUES (?, ?)", (guid, geom_hash))

        # Insert metadata
        cursor.execute("""
            INSERT INTO elements_meta (guid, discipline, ifc_class, storey)
            VALUES (?, ?, ?, ?)
        """, (guid, elem['discipline'], elem['ifc_class'], elem['storey']))

        # Insert transform
        cx, cy, cz = elem['center']
        cursor.execute("""
            INSERT INTO element_transforms (guid, center_x, center_y, center_z, length)
            VALUES (?, ?, ?, ?, ?)
        """, (guid, cx, cy, cz, elem['length']))

        # Insert rtree
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        zs = [v[2] for v in vertices]
        cursor.execute("""
            INSERT INTO elements_rtree VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (i+1, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

    # Global offset
    cursor.execute("INSERT INTO global_offset VALUES (0, 0, 0)")

    conn.commit()
    conn.close()

    # ==========================================================================
    # SUMMARY
    # ==========================================================================

    print("\n" + "=" * 70)
    print("POC DATABASE CREATED")
    print("=" * 70)
    print(f"Output: {OUTPUT_DB}")
    print(f"Elements: {len(elements)}")
    print("")
    print("EXPECTED METRICS (for validation):")
    print("-" * 70)
    print("  Bounding box: 10.5m x 5.0m x 3.0m")
    print("  Elements: 6 total")
    print("    IfcWall: 1 (10m x 5m x 3m box)")
    print("    IfcColumn: 4 (0.5m diameter cylinders)")
    print("    IfcBeam: 1 (8m x 0.3m x 0.5m)")
    print("  Total vertices: 8 + (4 x 26) + 8 = 120")
    print("  Total faces: 12 + (4 x 48) + 12 = 216")
    print("=" * 70)
    print("\nRun audit to verify: python3 audit_database.py", OUTPUT_DB)

if __name__ == "__main__":
    main()
