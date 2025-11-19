#!/usr/bin/env python3
"""
Convert downloaded OBJ/FBX 3D models to geometry library format.

Reads models from SourceFiles/3D_Library/ and adds them to DatabaseFiles/geometry_library.db
"""

import numpy as np
import struct
import hashlib
import sqlite3
from pathlib import Path
import re

# Paths
SOURCE_DIR = Path("/home/red1/Documents/bonsai/2Dto3D/SourceFiles/3D_Library")
LIBRARY_DB = Path("/home/red1/Documents/bonsai/2Dto3D/DatabaseFiles/geometry_library.db")

# Fixture type mapping based on folder/file names
FIXTURE_TYPE_MAP = {
    'bicycle': 'bicycle_rack',
    'bike': 'bicycle_rack',
    'stanchion': 'queue_stanchion',
    'barrier': 'queue_stanchion',
    'queue': 'queue_stanchion',
    'vending': 'vending_machine',
    'ticket': 'ticket_booth',
    'booth': 'ticket_booth',
    'kiosk': 'info_kiosk',
    'signage': 'digital_signage',
    'display': 'digital_signage',
    'monitor': 'weather_display',
    'baggage': 'baggage_carousel',
    'carousel': 'baggage_carousel',
    'conveyor': 'baggage_carousel',
    'life': 'life_jacket',
    'vest': 'life_jacket',
    'jacket': 'life_jacket',
    'bench': 'airport_bench',
    'seating': 'airport_bench',
    'atm': 'atm_kiosk',
}

def parse_obj(filepath):
    """Parse OBJ file and extract vertices and faces."""
    vertices = []
    faces = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if not parts:
                continue

            if parts[0] == 'v' and len(parts) >= 4:
                # Vertex
                try:
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    vertices.append([x, y, z])
                except ValueError:
                    continue

            elif parts[0] == 'f':
                # Face - can be v, v/vt, v/vt/vn, or v//vn
                face_indices = []
                for part in parts[1:]:
                    # Extract vertex index (first number before any /)
                    idx = part.split('/')[0]
                    try:
                        # OBJ uses 1-based indexing
                        face_indices.append(int(idx) - 1)
                    except ValueError:
                        continue

                # Triangulate if needed (simple fan triangulation)
                if len(face_indices) >= 3:
                    for i in range(1, len(face_indices) - 1):
                        faces.append([face_indices[0], face_indices[i], face_indices[i+1]])

    return np.array(vertices, dtype=np.float32), np.array(faces, dtype=np.int32)

def center_and_normalize(vertices, target_size=1.0):
    """Center mesh at origin and normalize to target size."""
    if len(vertices) == 0:
        return vertices

    # Center at origin
    center = (vertices.max(axis=0) + vertices.min(axis=0)) / 2
    vertices = vertices - center

    # Normalize to target size
    max_extent = np.abs(vertices).max()
    if max_extent > 0:
        scale = target_size / max_extent
        vertices = vertices * scale

    return vertices

def infer_fixture_type(filepath):
    """Infer fixture type from file/folder name."""
    name = filepath.stem.lower()
    parent = filepath.parent.name.lower()

    # Check parent folder first, then filename
    for keyword, fixture_type in FIXTURE_TYPE_MAP.items():
        if keyword in parent or keyword in name:
            return fixture_type

    return 'other'

def add_to_library(vertices, faces, fixture_type, fixture_name, ifc_class="IfcFurniture"):
    """Add model to geometry library database."""
    # Pack geometry data
    v_blob = vertices.tobytes()
    f_blob = faces.tobytes()

    # Create geometry hash
    geom_hash = hashlib.md5(v_blob + f_blob).hexdigest()[:16]

    conn = sqlite3.connect(LIBRARY_DB)
    cursor = conn.cursor()

    # Insert geometry
    cursor.execute('''
        INSERT OR REPLACE INTO base_geometries
        (geometry_hash, vertices, faces, normals, vertex_count, face_count)
        VALUES (?, ?, ?, NULL, ?, ?)
    ''', (geom_hash, v_blob, f_blob, len(vertices), len(faces)))

    # Insert catalog entry
    cursor.execute('''
        INSERT OR REPLACE INTO fixture_catalog
        (geometry_hash, ifc_class, fixture_type, fixture_name, vertex_count, face_count)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (geom_hash, ifc_class, fixture_type, fixture_name, len(vertices), len(faces)))

    conn.commit()
    conn.close()

    return geom_hash

def convert_all_models():
    """Convert all OBJ files in source directory to library format."""
    print("=" * 60)
    print("3D MODEL TO LIBRARY CONVERTER")
    print("=" * 60)

    if not SOURCE_DIR.exists():
        print(f"\nSource directory not found: {SOURCE_DIR}")
        print("Creating directory structure...")
        SOURCE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"\nPlease download models to: {SOURCE_DIR}")
        return

    # Find all OBJ files
    obj_files = list(SOURCE_DIR.rglob("*.obj"))

    if not obj_files:
        print(f"\nNo OBJ files found in: {SOURCE_DIR}")
        print("\nExpected structure:")
        print("  SourceFiles/3D_Library/")
        print("    bicycle_stand/model.obj")
        print("    vending_machine/model.obj")
        print("    ...")
        return

    print(f"\nFound {len(obj_files)} OBJ files to convert\n")

    converted = 0
    failed = 0

    for obj_file in obj_files:
        print(f"Processing: {obj_file.relative_to(SOURCE_DIR)}")

        try:
            # Parse OBJ
            vertices, faces = parse_obj(obj_file)

            if len(vertices) == 0 or len(faces) == 0:
                print(f"  Warning: Empty mesh, skipping")
                failed += 1
                continue

            # Center and normalize
            vertices = center_and_normalize(vertices, target_size=1.0)

            # Infer fixture type
            fixture_type = infer_fixture_type(obj_file)
            fixture_name = obj_file.stem.replace('_', ' ').title()

            # Add to library
            geom_hash = add_to_library(vertices, faces, fixture_type, fixture_name)

            print(f"  Type: {fixture_type}")
            print(f"  Vertices: {len(vertices)}, Faces: {len(faces)}")
            print(f"  Hash: {geom_hash}")
            print()

            converted += 1

        except Exception as e:
            print(f"  Error: {e}")
            failed += 1

    print("=" * 60)
    print("CONVERSION COMPLETE")
    print("=" * 60)
    print(f"\nConverted: {converted}")
    print(f"Failed: {failed}")
    print(f"\nLibrary DB: {LIBRARY_DB}")

def show_library_summary():
    """Show current library contents."""
    if not LIBRARY_DB.exists():
        print("Library database not found")
        return

    conn = sqlite3.connect(LIBRARY_DB)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT fixture_type, COUNT(*) as count, SUM(vertex_count) as total_verts
        FROM fixture_catalog
        GROUP BY fixture_type
        ORDER BY count DESC
    ''')

    print("\n" + "=" * 60)
    print("GEOMETRY LIBRARY CONTENTS")
    print("=" * 60)

    total = 0
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} models ({row[2]} total vertices)")
        total += row[1]

    print(f"\nTotal fixture types: {total}")
    conn.close()

if __name__ == '__main__':
    convert_all_models()
    show_library_summary()
