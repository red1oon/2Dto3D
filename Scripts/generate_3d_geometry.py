#!/usr/bin/env python3
"""
3D Geometry Generator for 2D-to-3D Conversion
==============================================

Generates parametric 3D mesh geometry from 2D DXF element positions and metadata.

This script:
1. Reads element positions and metadata from filtered database
2. Generates 3D meshes based on IFC class (walls, doors, windows, columns)
3. Populates base_geometries table with mesh data
4. Creates element_geometry view for Bonsai loading

Usage:
    python3 generate_3d_geometry.py Terminal1_MainBuilding_FILTERED.db

Geometry Rules:
- Walls: Extruded rectangles (length from DXF, default thickness 200mm, height 3m)
- Doors: Parametric door (default 900x2100mm)
- Windows: Parametric window (default 1200x1500mm)
- Columns: Cylinders or rectangular profiles (default 400mm diameter)
- Equipment: Simple boxes (default 1x1x1m)
"""

import sys
import sqlite3
import struct
import hashlib
import math
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# ============================================================================
# GEOMETRY GENERATION PARAMETERS
# ============================================================================

# Default dimensions (in meters)
DEFAULT_WALL_THICKNESS = 0.2  # 200mm
DEFAULT_WALL_HEIGHT = 3.0     # 3m floor-to-ceiling
DEFAULT_DOOR_WIDTH = 0.9      # 900mm
DEFAULT_DOOR_HEIGHT = 2.1     # 2100mm
DEFAULT_WINDOW_WIDTH = 1.2    # 1200mm
DEFAULT_WINDOW_HEIGHT = 1.5   # 1500mm
DEFAULT_COLUMN_DIAMETER = 0.4 # 400mm
DEFAULT_COLUMN_HEIGHT = 3.5   # 3.5m
DEFAULT_EQUIPMENT_SIZE = 1.0  # 1m cube

# Mesh detail levels
COLUMN_SEGMENTS = 12  # Number of segments for cylindrical columns
BOX_SEGMENTS = 1      # Simple box (cube)

# ============================================================================
# GEOMETRY PACKING UTILITIES (from extract_tessellation_to_db_v2.py)
# ============================================================================

def pack_vertices(vertices: List[Tuple[float, float, float]]) -> bytes:
    """Pack list of (x,y,z) tuples into binary BLOB."""
    return struct.pack(f'<{len(vertices)*3}f', *[coord for v in vertices for coord in v])

def pack_faces(faces: List[Tuple[int, int, int]]) -> bytes:
    """Pack list of (i1,i2,i3) tuples into binary BLOB."""
    return struct.pack(f'<{len(faces)*3}I', *[idx for face in faces for idx in face])

def pack_normals(normals: List[Tuple[float, float, float]]) -> bytes:
    """Pack list of normal vectors into binary BLOB."""
    return struct.pack(f'<{len(normals)*3}f', *[coord for n in normals for coord in n])

def compute_hash(vertices_blob: bytes, faces_blob: bytes) -> str:
    """Compute SHA256 hash of geometry for deduplication."""
    hasher = hashlib.sha256()
    hasher.update(vertices_blob)
    hasher.update(faces_blob)
    return hasher.hexdigest()

def compute_face_normal(v0: Tuple[float, float, float],
                       v1: Tuple[float, float, float],
                       v2: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Compute face normal using cross product."""
    # Edge vectors
    e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
    e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])

    # Cross product
    nx = e1[1] * e2[2] - e1[2] * e2[1]
    ny = e1[2] * e2[0] - e1[0] * e2[2]
    nz = e1[0] * e2[1] - e1[1] * e2[0]

    # Normalize
    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length > 0:
        return (nx/length, ny/length, nz/length)
    return (0, 0, 1)  # Default up normal

# ============================================================================
# GEOMETRY TRANSFORMATION UTILITIES
# ============================================================================

def rotate_vertices_z(vertices: List[Tuple[float, float, float]], angle_rad: float) -> List[Tuple[float, float, float]]:
    """
    Rotate vertices around Z-axis.

    Args:
        vertices: List of (x, y, z) tuples
        angle_rad: Rotation angle in radians

    Returns:
        Rotated vertices
    """
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    rotated = []
    for x, y, z in vertices:
        # Rotation matrix around Z-axis:
        # | cos  -sin  0 |   | x |
        # | sin   cos  0 | × | y |
        # |  0     0   1 |   | z |
        new_x = x * cos_a - y * sin_a
        new_y = x * sin_a + y * cos_a
        new_z = z
        rotated.append((new_x, new_y, new_z))

    return rotated

def translate_vertices(vertices: List[Tuple[float, float, float]],
                      dx: float, dy: float, dz: float) -> List[Tuple[float, float, float]]:
    """
    Translate vertices by offset.

    Args:
        vertices: List of (x, y, z) tuples
        dx, dy, dz: Translation offsets

    Returns:
        Translated vertices
    """
    return [(x + dx, y + dy, z + dz) for x, y, z in vertices]

# ============================================================================
# PARAMETRIC GEOMETRY GENERATORS
# ============================================================================

def generate_box_geometry(width: float, depth: float, height: float,
                         center_x: float = 0, center_y: float = 0, center_z: float = 0
                        ) -> Tuple[List[Tuple], List[Tuple], List[Tuple]]:
    """
    Generate box geometry (walls, equipment, etc.).

    Returns: (vertices, faces, normals)
    """
    # Calculate half-dimensions
    hx, hy, hz = width/2, depth/2, height/2

    # 8 vertices of box (centered at origin, then offset to center position)
    vertices = [
        (center_x - hx, center_y - hy, center_z - hz),  # 0: bottom-left-front
        (center_x + hx, center_y - hy, center_z - hz),  # 1: bottom-right-front
        (center_x + hx, center_y + hy, center_z - hz),  # 2: bottom-right-back
        (center_x - hx, center_y + hy, center_z - hz),  # 3: bottom-left-back
        (center_x - hx, center_y - hy, center_z + hz),  # 4: top-left-front
        (center_x + hx, center_y - hy, center_z + hz),  # 5: top-right-front
        (center_x + hx, center_y + hy, center_z + hz),  # 6: top-right-back
        (center_x - hx, center_y + hy, center_z + hz),  # 7: top-left-back
    ]

    # 12 triangular faces (2 per box face)
    faces = [
        # Bottom (z-)
        (0, 1, 2), (0, 2, 3),
        # Top (z+)
        (4, 7, 6), (4, 6, 5),
        # Front (y-)
        (0, 4, 5), (0, 5, 1),
        # Back (y+)
        (2, 6, 7), (2, 7, 3),
        # Left (x-)
        (0, 3, 7), (0, 7, 4),
        # Right (x+)
        (1, 5, 6), (1, 6, 2),
    ]

    # Compute normals for each face
    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normal = compute_face_normal(v0, v1, v2)
        normals.append(normal)

    return vertices, faces, normals

def generate_cylinder_geometry(radius: float, height: float, segments: int = 12,
                               center_x: float = 0, center_y: float = 0, center_z: float = 0
                              ) -> Tuple[List[Tuple], List[Tuple], List[Tuple]]:
    """
    Generate cylinder geometry (columns).

    Returns: (vertices, faces, normals)
    """
    vertices = []

    # Bottom cap center
    vertices.append((center_x, center_y, center_z))

    # Bottom cap vertices
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        vertices.append((x, y, center_z))

    # Top cap center
    vertices.append((center_x, center_y, center_z + height))

    # Top cap vertices
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        vertices.append((x, y, center_z + height))

    # Generate faces
    faces = []

    # Bottom cap triangles
    for i in range(segments):
        next_i = (i + 1) % segments
        faces.append((0, i + 1, next_i + 1))

    # Side quads (as 2 triangles each)
    for i in range(segments):
        next_i = (i + 1) % segments
        bottom_curr = i + 1
        bottom_next = next_i + 1
        top_curr = segments + 2 + i
        top_next = segments + 2 + next_i

        # Two triangles per quad
        faces.append((bottom_curr, top_curr, top_next))
        faces.append((bottom_curr, top_next, bottom_next))

    # Top cap triangles
    top_center = segments + 1
    for i in range(segments):
        next_i = (i + 1) % segments
        curr = segments + 2 + i
        next_v = segments + 2 + next_i
        faces.append((top_center, next_v, curr))

    # Compute normals
    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normal = compute_face_normal(v0, v1, v2)
        normals.append(normal)

    return vertices, faces, normals

def generate_wall_geometry(center_x: float, center_y: float, center_z: float,
                          thickness: float = DEFAULT_WALL_THICKNESS,
                          length: float = 1.0,
                          height: float = DEFAULT_WALL_HEIGHT
                         ) -> Tuple[List[Tuple], List[Tuple], List[Tuple]]:
    """
    Generate wall geometry (extruded rectangle).
    Wall extends along X-axis, thickness along Y-axis.
    """
    return generate_box_geometry(length, thickness, height, center_x, center_y, center_z + height/2)

def generate_door_geometry(center_x: float, center_y: float, center_z: float,
                          width: float = DEFAULT_DOOR_WIDTH,
                          height: float = DEFAULT_DOOR_HEIGHT
                         ) -> Tuple[List[Tuple], List[Tuple], List[Tuple]]:
    """Generate door geometry (simple rectangular panel)."""
    thickness = 0.05  # 50mm door thickness
    return generate_box_geometry(width, thickness, height, center_x, center_y, center_z + height/2)

def generate_window_geometry(center_x: float, center_y: float, center_z: float,
                            width: float = DEFAULT_WINDOW_WIDTH,
                            height: float = DEFAULT_WINDOW_HEIGHT
                           ) -> Tuple[List[Tuple], List[Tuple], List[Tuple]]:
    """Generate window geometry (simple rectangular frame)."""
    thickness = 0.1  # 100mm window thickness
    # Windows typically start 1m above floor
    z_offset = 1.0 + height/2
    return generate_box_geometry(width, thickness, height, center_x, center_y, center_z + z_offset)

def generate_column_geometry(center_x: float, center_y: float, center_z: float,
                            diameter: float = DEFAULT_COLUMN_DIAMETER,
                            height: float = DEFAULT_COLUMN_HEIGHT
                           ) -> Tuple[List[Tuple], List[Tuple], List[Tuple]]:
    """Generate column geometry (cylinder)."""
    return generate_cylinder_geometry(diameter/2, height, COLUMN_SEGMENTS, center_x, center_y, center_z)

def generate_element_geometry(ifc_class: str, center_x: float, center_y: float, center_z: float,
                             dimensions: Optional[Dict[str, float]] = None
                             ) -> Optional[Tuple[List[Tuple], List[Tuple], List[Tuple]]]:
    """
    Generate geometry for an element based on IFC class and actual dimensions.

    Args:
        ifc_class: IFC class name
        center_x, center_y, center_z: Element position
        dimensions: Dict with actual dimensions from DXF (length, width, height, diameter)

    Returns: (vertices, faces, normals) or None if unsupported
    """
    dims = dimensions or {}

    if ifc_class == "IfcWall":
        # Use actual wall length from DXF polyline, or default to 1m
        length = dims.get('length', 1.0)
        width = dims.get('width', DEFAULT_WALL_THICKNESS)
        height = dims.get('height', DEFAULT_WALL_HEIGHT)
        # Clamp to reasonable ranges (0.1m to 50m)
        length = max(0.1, min(length, 50.0))
        width = max(0.1, min(width, 1.0))
        return generate_wall_geometry(center_x, center_y, center_z, width, length, height)

    elif ifc_class == "IfcDoor":
        # Use actual door dimensions from DXF block, or defaults
        width = dims.get('width', DEFAULT_DOOR_WIDTH)
        height = dims.get('height', DEFAULT_DOOR_HEIGHT)
        # Clamp to reasonable ranges (0.5m to 3m)
        width = max(0.5, min(width, 3.0))
        height = max(1.8, min(height, 3.0))
        return generate_door_geometry(center_x, center_y, center_z, width, height)

    elif ifc_class == "IfcWindow":
        # Use actual window dimensions from DXF block, or defaults
        width = dims.get('width', DEFAULT_WINDOW_WIDTH)
        height = dims.get('height', DEFAULT_WINDOW_HEIGHT)
        # Clamp to reasonable ranges (0.3m to 5m)
        width = max(0.3, min(width, 5.0))
        height = max(0.3, min(height, 3.0))
        return generate_window_geometry(center_x, center_y, center_z, width, height)

    elif ifc_class == "IfcColumn":
        # Use actual column diameter from DXF circle, or default
        diameter = dims.get('diameter', DEFAULT_COLUMN_DIAMETER)
        height = dims.get('height', DEFAULT_COLUMN_HEIGHT)
        # Clamp to reasonable ranges (0.2m to 2m diameter)
        diameter = max(0.2, min(diameter, 2.0))
        return generate_column_geometry(center_x, center_y, center_z, diameter, height)

    elif ifc_class == "IfcBuildingElementProxy":
        # Generic equipment/proxy - use box with measured dimensions if available
        length = dims.get('length', DEFAULT_EQUIPMENT_SIZE)
        width = dims.get('width', DEFAULT_EQUIPMENT_SIZE)
        height = dims.get('height', DEFAULT_EQUIPMENT_SIZE)
        return generate_box_geometry(length, width, height, center_x, center_y,
                                    center_z + height/2)
    else:
        # Other elements - simple 0.5m cube (or measured size)
        size = dims.get('length', 0.5) if dims else 0.5
        size = max(0.1, min(size, 2.0))  # Clamp
        return generate_box_geometry(size, size, size, center_x, center_y, center_z + size/2)

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def populate_geometry_tables(db_path: str, limit: Optional[int] = None):
    """
    Populate base_geometries table with generated 3D meshes.

    Args:
        db_path: Path to database file
        limit: Maximum elements to process (None = all)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all elements with positions, dimensions, and rotation
    print("Reading elements from database...")
    query = """
        SELECT m.guid, m.ifc_class, m.discipline, t.center_x, t.center_y, t.center_z,
               COALESCE(t.rotation_z, 0.0) as rotation_z, m.dimensions
        FROM elements_meta m
        JOIN element_transforms t ON m.guid = t.guid
        ORDER BY m.ifc_class, m.guid
    """
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    elements = cursor.fetchall()

    print(f"Found {len(elements)} elements to process")

    # Statistics
    stats = {
        'total': len(elements),
        'processed': 0,
        'skipped': 0,
        'by_class': {},
        'with_dimensions': 0,
        'without_dimensions': 0
    }

    # Process each element
    for guid, ifc_class, discipline, center_x, center_y, center_z, rotation_z, dimensions_json in elements:
        # Track by class
        if ifc_class not in stats['by_class']:
            stats['by_class'][ifc_class] = 0

        # Parse dimensions JSON if available
        dimensions = None
        if dimensions_json:
            try:
                dimensions = json.loads(dimensions_json)
                stats['with_dimensions'] += 1
            except:
                pass  # Invalid JSON, use defaults

        if not dimensions:
            stats['without_dimensions'] += 1

        # Generate geometry with actual dimensions (at origin, unrotated)
        result = generate_element_geometry(ifc_class, 0, 0, 0, dimensions)

        if result is None:
            stats['skipped'] += 1
            continue

        vertices, faces, normals = result

        # Apply rotation and translation to vertices
        if rotation_z != 0:
            vertices = rotate_vertices_z(vertices, rotation_z)

        # Translate to final position
        vertices = translate_vertices(vertices, center_x, center_y, center_z)

        # Pack into binary blobs
        vertices_blob = pack_vertices(vertices)
        faces_blob = pack_faces(faces)
        normals_blob = pack_normals(normals)

        # Compute geometry hash
        geom_hash = compute_hash(vertices_blob, faces_blob)

        # Insert into base_geometries (or ignore if duplicate hash)
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO base_geometries (guid, geometry_hash, vertices, faces, normals)
                VALUES (?, ?, ?, ?, ?)
            """, (guid, geom_hash, vertices_blob, faces_blob, normals_blob))

            stats['processed'] += 1
            stats['by_class'][ifc_class] += 1

            if stats['processed'] % 100 == 0:
                print(f"  Processed {stats['processed']}/{len(elements)} elements...")
                conn.commit()

        except Exception as e:
            print(f"ERROR processing {guid} ({ifc_class}): {e}")
            stats['skipped'] += 1

    # Final commit
    conn.commit()

    # Print statistics
    print("\n" + "="*60)
    print("GEOMETRY GENERATION COMPLETE")
    print("="*60)
    print(f"Total elements:     {stats['total']}")
    print(f"Processed:          {stats['processed']}")
    print(f"Skipped:            {stats['skipped']}")
    print(f"\nDimension Coverage:")
    print(f"  With dimensions:  {stats['with_dimensions']} ({stats['with_dimensions']/stats['total']*100:.1f}%)")
    print(f"  Using defaults:   {stats['without_dimensions']} ({stats['without_dimensions']/stats['total']*100:.1f}%)")
    print("\nBy IFC Class:")
    for ifc_class, count in sorted(stats['by_class'].items(), key=lambda x: -x[1]):
        print(f"  {ifc_class:30} {count:5} elements")

    # Verify geometry table
    cursor.execute("SELECT COUNT(*) FROM base_geometries")
    geom_count = cursor.fetchone()[0]
    print(f"\nGeometry entries in database: {geom_count}")

    conn.close()

# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_3d_geometry.py <database_path> [limit]")
        print("\nExample:")
        print("  python3 generate_3d_geometry.py Terminal1_MainBuilding_FILTERED.db")
        print("  python3 generate_3d_geometry.py Terminal1_MainBuilding_FILTERED.db 100  # Test first 100")
        sys.exit(1)

    db_path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if not Path(db_path).exists():
        print(f"ERROR: Database not found: {db_path}")
        sys.exit(1)

    print(f"Generating 3D geometry for: {db_path}")
    if limit:
        print(f"Processing limit: {limit} elements")

    populate_geometry_tables(db_path, limit)

    print("\n✅ Geometry generation complete!")
    print(f"\nNext step: Test 'Full Load' in Blender with database:")
    print(f"  {db_path}")

if __name__ == "__main__":
    main()
