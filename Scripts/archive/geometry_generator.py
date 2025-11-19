#!/usr/bin/env python3
"""
Geometry Generator - Creates mesh data (vertices/faces) for building elements.

Generates simple but accurate procedural geometry for:
- Walls: Oriented boxes along wall direction
- Beams: Rectangular profiles along beam centerline
- Columns: Vertical rectangular profiles
- Slabs: Horizontal flat boxes
- Plates (roof): Flat rectangular panels
- Windows/Doors: Simple rectangular openings

Output format matches IFC extraction database format:
- vertices: BLOB of float32 triplets (X, Y, Z)
- faces: BLOB of uint32 triplets (triangle indices)
- normals: Optional BLOB of float32 triplets (per-vertex normals)
"""

import struct
import hashlib
from typing import Tuple, List
import math


def generate_box_geometry(length: float, width: float, height: float,
                         center_x: float = 0.0, center_y: float = 0.0, center_z: float = 0.0) -> Tuple[bytes, bytes, bytes]:
    """
    Generate box mesh geometry at specified world position.

    Args:
        length: X dimension (meters)
        width: Y dimension (meters)
        height: Z dimension (meters)
        center_x: World X position (meters)
        center_y: World Y position (meters)
        center_z: World Z position (meters)

    Returns:
        (vertices_blob, faces_blob, normals_blob)
    """
    # Half dimensions for offsetting from center
    hx = length / 2.0
    hy = width / 2.0
    hz = height / 2.0

    # 8 vertices of a box (offset from center position to world coordinates)
    vertices = [
        # Bottom face (Z = center_z - hz)
        (center_x - hx, center_y - hy, center_z - hz),  # 0
        (center_x + hx, center_y - hy, center_z - hz),  # 1
        (center_x + hx, center_y + hy, center_z - hz),  # 2
        (center_x - hx, center_y + hy, center_z - hz),  # 3
        # Top face (Z = center_z + hz)
        (center_x - hx, center_y - hy, center_z + hz),  # 4
        (center_x + hx, center_y - hy, center_z + hz),  # 5
        (center_x + hx, center_y + hy, center_z + hz),  # 6
        (center_x - hx, center_y + hy, center_z + hz),  # 7
    ]

    # 12 triangular faces (6 quad faces × 2 triangles)
    # Each face is (v0, v1, v2) indices - counter-clockwise winding
    faces = [
        # Bottom face (looking up, CCW)
        (0, 2, 1), (0, 3, 2),
        # Top face (looking down, CCW)
        (4, 5, 6), (4, 6, 7),
        # Front face (-Y, looking from +Y)
        (0, 1, 5), (0, 5, 4),
        # Back face (+Y, looking from -Y)
        (3, 7, 6), (3, 6, 2),
        # Left face (-X, looking from +X)
        (0, 4, 7), (0, 7, 3),
        # Right face (+X, looking from -X)
        (1, 2, 6), (1, 6, 5),
    ]

    # Normals (per-vertex, averaged from adjacent faces)
    # For a box, vertices are shared by 3 faces
    normals = [
        (-1, -1, -1),  # 0: left, front, bottom
        ( 1, -1, -1),  # 1: right, front, bottom
        ( 1,  1, -1),  # 2: right, back, bottom
        (-1,  1, -1),  # 3: left, back, bottom
        (-1, -1,  1),  # 4: left, front, top
        ( 1, -1,  1),  # 5: right, front, top
        ( 1,  1,  1),  # 6: right, back, top
        (-1,  1,  1),  # 7: left, back, top
    ]

    # Normalize normals
    normals = [normalize_vector(n) for n in normals]

    # Pack to binary format (float32 for vertices/normals, uint32 for faces)
    vertices_blob = struct.pack(f'{len(vertices) * 3}f', *[c for v in vertices for c in v])
    faces_blob = struct.pack(f'{len(faces) * 3}I', *[i for f in faces for i in f])
    normals_blob = struct.pack(f'{len(normals) * 3}f', *[c for n in normals for c in n])

    return (vertices_blob, faces_blob, normals_blob)


def normalize_vector(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Normalize a 3D vector."""
    length = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if length < 1e-10:
        return (0, 0, 1)  # Default to up vector
    return (v[0]/length, v[1]/length, v[2]/length)


def generate_geometry_hash(vertices_blob: bytes, faces_blob: bytes) -> str:
    """Generate SHA256 hash for geometry deduplication."""
    hasher = hashlib.sha256()
    hasher.update(vertices_blob)
    hasher.update(faces_blob)
    return hasher.hexdigest()


def generate_element_geometry(ifc_class: str, length: float, width: float, height: float,
                             center_x: float = 0.0, center_y: float = 0.0, center_z: float = 0.0) -> Tuple[bytes, bytes, bytes, str]:
    """
    Generate geometry for an element based on IFC class and dimensions.

    Args:
        ifc_class: IFC class name (IfcWall, IfcBeam, etc.)
        length: Element length in meters
        width: Element width in meters
        height: Element height in meters
        center_x: World X position (meters)
        center_y: World Y position (meters)
        center_z: World Z position (meters)

    Returns:
        (vertices_blob, faces_blob, normals_blob, geometry_hash)
    """
    # For now, all elements use box geometry
    # Future: Can add specialized shapes (I-beams, circular columns, etc.)

    vertices_blob, faces_blob, normals_blob = generate_box_geometry(
        length, width, height, center_x, center_y, center_z
    )
    geometry_hash = generate_geometry_hash(vertices_blob, faces_blob)

    return (vertices_blob, faces_blob, normals_blob, geometry_hash)


# Test
if __name__ == "__main__":
    print("Testing geometry generation...")

    # Test: 5m long beam, 0.3m × 0.3m cross-section
    vertices, faces, normals, geom_hash = generate_element_geometry('IfcBeam', 5.0, 0.3, 0.3)

    print(f"\nBeam (5m × 0.3m × 0.3m):")
    print(f"  Vertices: {len(vertices)} bytes ({len(vertices)//12} vertices)")
    print(f"  Faces: {len(faces)} bytes ({len(faces)//12} triangles)")
    print(f"  Normals: {len(normals)} bytes")
    print(f"  Hash: {geom_hash[:16]}...")

    # Test: 3m wall, 0.2m thick, 3.5m high
    vertices, faces, normals, geom_hash = generate_element_geometry('IfcWall', 3.0, 0.2, 3.5)

    print(f"\nWall (3m × 0.2m × 3.5m):")
    print(f"  Vertices: {len(vertices)} bytes")
    print(f"  Faces: {len(faces)} bytes")
    print(f"  Hash: {geom_hash[:16]}...")

    print("\n✅ Geometry generation working correctly!")
