#!/usr/bin/env python3
"""
Parametric Shape Library for 2D-to-3D Conversion
Modular shape generators for GUI integration with Mini Bonsai Tree

Each function returns: (vertices, faces, normals)
- vertices: List of (x, y, z) tuples
- faces: List of (v0, v1, v2) triangle tuples (vertex indices)
- normals: List of (nx, ny, nz) tuples (one per face)

Coordinate system: X=width, Y=depth/thickness, Z=height
All shapes centered at origin (0, 0, 0)

Usage in GUI:
    from shape_library import generate_chair, generate_sprinkler
    vertices, faces, normals = generate_chair(style='office')
"""

import math
from typing import List, Tuple, Optional

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def compute_face_normal(v0: Tuple[float, float, float],
                       v1: Tuple[float, float, float],
                       v2: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Compute face normal from 3 vertices using cross product."""
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


def create_cylinder_vertices(radius: float, height: float, segments: int = 12,
                            center_x: float = 0, center_y: float = 0, center_z: float = 0
                            ) -> Tuple[List[Tuple], List[Tuple], List[Tuple]]:
    """Create cylinder geometry (used by multiple shapes)."""
    vertices = []

    # Bottom center
    vertices.append((center_x, center_y, center_z))

    # Bottom ring
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        vertices.append((x, y, center_z))

    # Top center
    vertices.append((center_x, center_y, center_z + height))

    # Top ring
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        vertices.append((x, y, center_z + height))

    # Generate faces
    faces = []

    # Bottom cap
    for i in range(segments):
        next_i = (i + 1) % segments
        faces.append((0, i + 1, next_i + 1))

    # Side faces
    for i in range(segments):
        next_i = (i + 1) % segments
        bottom_i = i + 1
        bottom_next = next_i + 1
        top_i = segments + 2 + i
        top_next = segments + 2 + next_i

        # Two triangles per quad
        faces.append((bottom_i, top_i, top_next))
        faces.append((bottom_i, top_next, bottom_next))

    # Top cap
    top_center = segments + 1
    for i in range(segments):
        next_i = (i + 1) % segments
        top_i = segments + 2 + i
        top_next = segments + 2 + next_i
        faces.append((top_center, top_next, top_i))

    # Calculate normals
    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normals.append(compute_face_normal(v0, v1, v2))

    return vertices, faces, normals


def create_box_vertices(width: float, depth: float, height: float,
                       center_x: float = 0, center_y: float = 0, center_z: float = 0
                       ) -> Tuple[List[Tuple], List[Tuple], List[Tuple]]:
    """Create box geometry (used by multiple shapes)."""
    hw, hd, hh = width/2, depth/2, height/2
    cx, cy, cz = center_x, center_y, center_z

    vertices = [
        (cx - hw, cy - hd, cz - hh), (cx + hw, cy - hd, cz - hh),
        (cx + hw, cy + hd, cz - hh), (cx - hw, cy + hd, cz - hh),
        (cx - hw, cy - hd, cz + hh), (cx + hw, cy - hd, cz + hh),
        (cx + hw, cy + hd, cz + hh), (cx - hw, cy + hd, cz + hh),
    ]

    faces = [
        (0, 1, 2), (0, 2, 3),  # Bottom
        (4, 6, 5), (4, 7, 6),  # Top
        (0, 4, 5), (0, 5, 1),  # Front
        (2, 6, 7), (2, 7, 3),  # Back
        (0, 3, 7), (0, 7, 4),  # Left
        (1, 5, 6), (1, 6, 2),  # Right
    ]

    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normals.append(compute_face_normal(v0, v1, v2))

    return vertices, faces, normals


# ============================================================================
# FURNITURE
# ============================================================================

def generate_chair(style: str = 'office', seat_height: float = 0.45) -> Tuple[List, List, List]:
    """
    Generate chair geometry.

    Args:
        style: 'office', 'dining', 'stool'
        seat_height: Height of seat from floor (0.45m typical)

    Returns: (vertices, faces, normals)
    """
    vertices = []
    faces = []

    if style == 'office':
        # Seat
        seat_verts, seat_faces, _ = create_box_vertices(0.5, 0.5, 0.05, 0, 0, seat_height)
        vertices.extend(seat_verts)
        faces.extend(seat_faces)

        # Backrest
        offset = len(vertices)
        back_verts, back_faces, _ = create_box_vertices(0.5, 0.05, 0.4, 0, -0.22, seat_height + 0.2)
        vertices.extend(back_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in back_faces])

        # Central post (cylinder)
        offset = len(vertices)
        post_verts, post_faces, _ = create_cylinder_vertices(0.05, seat_height, 8, 0, 0, 0)
        vertices.extend(post_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in post_faces])

        # Star base (5 legs)
        for i in range(5):
            angle = 2 * math.pi * i / 5
            x = 0.25 * math.cos(angle)
            y = 0.25 * math.sin(angle)
            offset = len(vertices)
            leg_verts, leg_faces, _ = create_box_vertices(0.3, 0.05, 0.02, x/2, y/2, 0.01)
            vertices.extend(leg_verts)
            faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in leg_faces])

    elif style == 'dining':
        # Seat
        seat_verts, seat_faces, _ = create_box_vertices(0.45, 0.45, 0.04, 0, 0, seat_height)
        vertices.extend(seat_verts)
        faces.extend(seat_faces)

        # Backrest
        offset = len(vertices)
        back_verts, back_faces, _ = create_box_vertices(0.45, 0.03, 0.5, 0, -0.21, seat_height + 0.25)
        vertices.extend(back_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in back_faces])

        # 4 legs
        leg_positions = [(-0.18, -0.18), (0.18, -0.18), (0.18, 0.18), (-0.18, 0.18)]
        for x, y in leg_positions:
            offset = len(vertices)
            leg_verts, leg_faces, _ = create_cylinder_vertices(0.02, seat_height, 6, x, y, 0)
            vertices.extend(leg_verts)
            faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in leg_faces])

    else:  # stool
        # Seat
        seat_verts, seat_faces, _ = create_cylinder_vertices(0.18, 0.04, 12, 0, 0, seat_height)
        vertices.extend(seat_verts)
        faces.extend(seat_faces)

        # Central post
        offset = len(vertices)
        post_verts, post_faces, _ = create_cylinder_vertices(0.04, seat_height, 8, 0, 0, 0)
        vertices.extend(post_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in post_faces])

        # Footrest ring
        offset = len(vertices)
        ring_verts, ring_faces, _ = create_cylinder_vertices(0.15, 0.02, 12, 0, 0, 0.25)
        vertices.extend(ring_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in ring_faces])

    # Calculate normals
    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normals.append(compute_face_normal(v0, v1, v2))

    return vertices, faces, normals


def generate_table(seats: int = 4, shape: str = 'rectangular') -> Tuple[List, List, List]:
    """
    Generate table geometry.

    Args:
        seats: Number of seats (2, 4, 6, 8)
        shape: 'rectangular', 'circular', 'square'

    Returns: (vertices, faces, normals)
    """
    vertices = []
    faces = []
    table_height = 0.75  # Standard table height

    if shape == 'rectangular':
        # Tabletop
        if seats <= 4:
            width, depth = 1.2, 0.8
        elif seats <= 6:
            width, depth = 1.8, 0.9
        else:
            width, depth = 2.4, 1.0

        top_verts, top_faces, _ = create_box_vertices(width, depth, 0.04, 0, 0, table_height)
        vertices.extend(top_verts)
        faces.extend(top_faces)

        # 4 legs at corners
        leg_x, leg_y = width/2 - 0.1, depth/2 - 0.1
        leg_positions = [(-leg_x, -leg_y), (leg_x, -leg_y), (leg_x, leg_y), (-leg_x, leg_y)]

        for x, y in leg_positions:
            offset = len(vertices)
            leg_verts, leg_faces, _ = create_box_vertices(0.08, 0.08, table_height - 0.02, x, y, (table_height - 0.02)/2)
            vertices.extend(leg_verts)
            faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in leg_faces])

    elif shape == 'circular':
        # Round tabletop
        radius = 0.5 if seats <= 4 else 0.7
        top_verts, top_faces, _ = create_cylinder_vertices(radius, 0.04, 24, 0, 0, table_height)
        vertices.extend(top_verts)
        faces.extend(top_faces)

        # Central pedestal
        offset = len(vertices)
        pedestal_verts, pedestal_faces, _ = create_cylinder_vertices(0.15, table_height - 0.04, 12, 0, 0, 0)
        vertices.extend(pedestal_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in pedestal_faces])

        # Circular base
        offset = len(vertices)
        base_verts, base_faces, _ = create_cylinder_vertices(0.4, 0.05, 16, 0, 0, 0)
        vertices.extend(base_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in base_faces])

    else:  # square
        size = 0.9 if seats <= 4 else 1.2
        top_verts, top_faces, _ = create_box_vertices(size, size, 0.04, 0, 0, table_height)
        vertices.extend(top_verts)
        faces.extend(top_faces)

        # 4 legs
        leg_offset = size/2 - 0.1
        leg_positions = [(-leg_offset, -leg_offset), (leg_offset, -leg_offset),
                        (leg_offset, leg_offset), (-leg_offset, leg_offset)]

        for x, y in leg_positions:
            offset = len(vertices)
            leg_verts, leg_faces, _ = create_cylinder_vertices(0.04, table_height - 0.04, 8, x, y, 0)
            vertices.extend(leg_verts)
            faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in leg_faces])

    # Calculate normals
    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normals.append(compute_face_normal(v0, v1, v2))

    return vertices, faces, normals


# ============================================================================
# LIGHTING FIXTURES
# ============================================================================

def generate_light_fixture(fixture_type: str = 'pendant',
                          mounting_height: float = 2.6) -> Tuple[List, List, List]:
    """
    Generate lighting fixture geometry.

    Args:
        fixture_type: 'pendant', 'recessed', 'track', 'wall_sconce', 'floor_lamp'
        mounting_height: Height from floor (default ceiling height)

    Returns: (vertices, faces, normals)
    """
    vertices = []
    faces = []

    if fixture_type == 'pendant':
        # Ceiling mount
        mount_verts, mount_faces, _ = create_cylinder_vertices(0.05, 0.02, 8, 0, 0, mounting_height)
        vertices.extend(mount_verts)
        faces.extend(mount_faces)

        # Cord/chain
        offset = len(vertices)
        cord_verts, cord_faces, _ = create_cylinder_vertices(0.005, 0.5, 6, 0, 0, mounting_height - 0.5)
        vertices.extend(cord_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in cord_faces])

        # Shade (inverted cone-like shape using cylinder)
        offset = len(vertices)
        shade_verts, shade_faces, _ = create_cylinder_vertices(0.15, 0.25, 12, 0, 0, mounting_height - 0.75)
        vertices.extend(shade_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in shade_faces])

        # Bulb housing
        offset = len(vertices)
        bulb_verts, bulb_faces, _ = create_cylinder_vertices(0.03, 0.08, 8, 0, 0, mounting_height - 0.83)
        vertices.extend(bulb_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in bulb_faces])

    elif fixture_type == 'recessed':
        # Trim ring
        trim_verts, trim_faces, _ = create_cylinder_vertices(0.12, 0.02, 16, 0, 0, mounting_height - 0.01)
        vertices.extend(trim_verts)
        faces.extend(trim_faces)

        # Recessed housing (visible part)
        offset = len(vertices)
        housing_verts, housing_faces, _ = create_cylinder_vertices(0.10, 0.15, 12, 0, 0, mounting_height - 0.16)
        vertices.extend(housing_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in housing_faces])

    elif fixture_type == 'track':
        # Track rail
        track_verts, track_faces, _ = create_box_vertices(2.0, 0.05, 0.04, 0, 0, mounting_height - 0.02)
        vertices.extend(track_verts)
        faces.extend(track_faces)

        # 3 spotlights along track
        for x in [-0.6, 0, 0.6]:
            offset = len(vertices)
            spot_verts, spot_faces, _ = create_cylinder_vertices(0.05, 0.15, 8, x, 0, mounting_height - 0.17)
            vertices.extend(spot_verts)
            faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in spot_faces])

    elif fixture_type == 'wall_sconce':
        # Wall mount plate
        plate_verts, plate_faces, _ = create_cylinder_vertices(0.08, 0.02, 12, 0, -0.05, 2.0)
        vertices.extend(plate_verts)
        faces.extend(plate_faces)

        # Shade/diffuser
        offset = len(vertices)
        shade_verts, shade_faces, _ = create_box_vertices(0.15, 0.12, 0.25, 0, 0.06, 2.0)
        vertices.extend(shade_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in shade_faces])

    else:  # floor_lamp
        # Base
        base_verts, base_faces, _ = create_cylinder_vertices(0.15, 0.03, 12, 0, 0, 0)
        vertices.extend(base_verts)
        faces.extend(base_faces)

        # Pole
        offset = len(vertices)
        pole_verts, pole_faces, _ = create_cylinder_vertices(0.015, 1.6, 8, 0, 0, 0.03)
        vertices.extend(pole_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in pole_faces])

        # Shade
        offset = len(vertices)
        shade_verts, shade_faces, _ = create_cylinder_vertices(0.2, 0.3, 12, 0, 0, 1.63)
        vertices.extend(shade_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in shade_faces])

    # Calculate normals
    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normals.append(compute_face_normal(v0, v1, v2))

    return vertices, faces, normals


# ============================================================================
# FIRE PROTECTION
# ============================================================================

def generate_sprinkler(sprinkler_type: str = 'head',
                      ceiling_height: float = 3.0) -> Tuple[List, List, List]:
    """
    Generate fire sprinkler geometry.

    Args:
        sprinkler_type: 'head', 'pipe', 'standpipe'
        ceiling_height: Height to ceiling

    Returns: (vertices, faces, normals)
    """
    vertices = []
    faces = []

    if sprinkler_type == 'head':
        # Ceiling mount
        mount_verts, mount_faces, _ = create_cylinder_vertices(0.015, 0.02, 8, 0, 0, ceiling_height - 0.02)
        vertices.extend(mount_verts)
        faces.extend(mount_faces)

        # Threaded connection
        offset = len(vertices)
        thread_verts, thread_faces, _ = create_cylinder_vertices(0.012, 0.03, 6, 0, 0, ceiling_height - 0.05)
        vertices.extend(thread_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in thread_faces])

        # Sprinkler body
        offset = len(vertices)
        body_verts, body_faces, _ = create_cylinder_vertices(0.02, 0.04, 8, 0, 0, ceiling_height - 0.09)
        vertices.extend(body_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in body_faces])

        # Deflector plate (thin disk)
        offset = len(vertices)
        plate_verts, plate_faces, _ = create_cylinder_vertices(0.06, 0.002, 12, 0, 0, ceiling_height - 0.095)
        vertices.extend(plate_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in plate_faces])

    elif sprinkler_type == 'pipe':
        # Horizontal pipe (typically runs along ceiling)
        pipe_verts, pipe_faces, _ = create_cylinder_vertices(0.025, 3.0, 8, 0, 0, ceiling_height - 0.15)
        # Rotate to horizontal (this is simplified - actual rotation would be in transform)
        vertices.extend(pipe_verts)
        faces.extend(pipe_faces)

    else:  # standpipe
        # Vertical standpipe with valve
        pipe_verts, pipe_faces, _ = create_cylinder_vertices(0.05, 1.5, 10, 0, 0, 0)
        vertices.extend(pipe_verts)
        faces.extend(pipe_faces)

        # Valve body
        offset = len(vertices)
        valve_verts, valve_faces, _ = create_box_vertices(0.15, 0.12, 0.2, 0.08, 0, 1.2)
        vertices.extend(valve_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in valve_faces])

        # Hose connection
        offset = len(vertices)
        connection_verts, connection_faces, _ = create_cylinder_vertices(0.035, 0.08, 8, 0.15, 0, 1.2)
        vertices.extend(connection_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in connection_faces])

    # Calculate normals
    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normals.append(compute_face_normal(v0, v1, v2))

    return vertices, faces, normals


def generate_fire_extinguisher() -> Tuple[List, List, List]:
    """Generate wall-mounted fire extinguisher."""
    vertices = []
    faces = []

    # Wall bracket
    bracket_verts, bracket_faces, _ = create_box_vertices(0.15, 0.05, 0.7, 0, -0.05, 0.8)
    vertices.extend(bracket_verts)
    faces.extend(bracket_faces)

    # Cylinder body
    offset = len(vertices)
    body_verts, body_faces, _ = create_cylinder_vertices(0.08, 0.5, 12, 0, 0.04, 0.6)
    vertices.extend(body_verts)
    faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in body_faces])

    # Nozzle assembly (small cylinder + hose)
    offset = len(vertices)
    nozzle_verts, nozzle_faces, _ = create_cylinder_vertices(0.015, 0.25, 6, 0.05, 0.04, 0.85)
    vertices.extend(nozzle_verts)
    faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in nozzle_faces])

    # Calculate normals
    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normals.append(compute_face_normal(v0, v1, v2))

    return vertices, faces, normals


# ============================================================================
# PLUMBING FIXTURES
# ============================================================================

def generate_toilet() -> Tuple[List, List, List]:
    """Generate toilet fixture."""
    vertices = []
    faces = []

    # Base (bowl) - simplified as cylinder
    bowl_verts, bowl_faces, _ = create_cylinder_vertices(0.18, 0.15, 12, 0, 0, 0)
    vertices.extend(bowl_verts)
    faces.extend(bowl_faces)

    # Seat/lid (thin cylinder)
    offset = len(vertices)
    seat_verts, seat_faces, _ = create_cylinder_vertices(0.20, 0.02, 16, 0, 0, 0.15)
    vertices.extend(seat_verts)
    faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in seat_faces])

    # Tank (box at back)
    offset = len(vertices)
    tank_verts, tank_faces, _ = create_box_vertices(0.4, 0.18, 0.35, 0, -0.18, 0.35)
    vertices.extend(tank_verts)
    faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in tank_faces])

    # Calculate normals
    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normals.append(compute_face_normal(v0, v1, v2))

    return vertices, faces, normals


def generate_sink(sink_type: str = 'wall') -> Tuple[List, List, List]:
    """
    Generate sink fixture.

    Args:
        sink_type: 'wall', 'pedestal', 'counter'
    """
    vertices = []
    faces = []

    if sink_type == 'wall':
        # Basin
        basin_verts, basin_faces, _ = create_box_vertices(0.5, 0.4, 0.15, 0, 0, 0.85)
        vertices.extend(basin_verts)
        faces.extend(basin_faces)

        # Faucet
        offset = len(vertices)
        faucet_verts, faucet_faces, _ = create_cylinder_vertices(0.02, 0.25, 8, 0, -0.15, 0.925)
        vertices.extend(faucet_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in faucet_faces])

    elif sink_type == 'pedestal':
        # Basin
        basin_verts, basin_faces, _ = create_cylinder_vertices(0.25, 0.15, 16, 0, 0, 0.80)
        vertices.extend(basin_verts)
        faces.extend(basin_faces)

        # Pedestal
        offset = len(vertices)
        pedestal_verts, pedestal_faces, _ = create_cylinder_vertices(0.15, 0.80, 12, 0, 0, 0)
        vertices.extend(pedestal_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in pedestal_faces])

        # Faucet
        offset = len(vertices)
        faucet_verts, faucet_faces, _ = create_cylinder_vertices(0.02, 0.25, 8, 0, -0.15, 0.875)
        vertices.extend(faucet_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in faucet_faces])

    else:  # counter
        # Basin (undermount style)
        basin_verts, basin_faces, _ = create_cylinder_vertices(0.2, 0.12, 16, 0, 0, 0.88)
        vertices.extend(basin_verts)
        faces.extend(basin_faces)

        # Faucet
        offset = len(vertices)
        faucet_verts, faucet_faces, _ = create_cylinder_vertices(0.015, 0.20, 8, 0, -0.12, 0.94)
        vertices.extend(faucet_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in faucet_faces])

    # Calculate normals
    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normals.append(compute_face_normal(v0, v1, v2))

    return vertices, faces, normals


# ============================================================================
# EQUIPMENT
# ============================================================================

def generate_hvac_unit(unit_type: str = 'diffuser') -> Tuple[List, List, List]:
    """
    Generate HVAC equipment.

    Args:
        unit_type: 'diffuser', 'ahu', 'fcu', 'exhaust_fan'
    """
    vertices = []
    faces = []

    if unit_type == 'diffuser':
        # Ceiling diffuser (square grille)
        grille_verts, grille_faces, _ = create_box_vertices(0.6, 0.6, 0.08, 0, 0, 2.92)
        vertices.extend(grille_verts)
        faces.extend(grille_faces)

        # Central core
        offset = len(vertices)
        core_verts, core_faces, _ = create_box_vertices(0.4, 0.4, 0.15, 0, 0, 2.845)
        vertices.extend(core_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in core_faces])

    elif unit_type == 'ahu':
        # Large air handling unit (rooftop)
        unit_verts, unit_faces, _ = create_box_vertices(3.0, 1.5, 1.8, 0, 0, 0.9)
        vertices.extend(unit_verts)
        faces.extend(unit_faces)

        # Access panel
        offset = len(vertices)
        panel_verts, panel_faces, _ = create_box_vertices(0.8, 0.05, 1.2, 1.5, 0, 1.5)
        vertices.extend(panel_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in panel_faces])

    elif unit_type == 'fcu':
        # Fan coil unit (ceiling mounted)
        unit_verts, unit_faces, _ = create_box_vertices(1.2, 0.6, 0.3, 0, 0, 2.85)
        vertices.extend(unit_verts)
        faces.extend(unit_faces)

    else:  # exhaust_fan
        # Wall/ceiling mounted exhaust fan
        housing_verts, housing_faces, _ = create_box_vertices(0.4, 0.25, 0.4, 0, 0, 2.8)
        vertices.extend(housing_verts)
        faces.extend(housing_faces)

        # Fan grille
        offset = len(vertices)
        grille_verts, grille_faces, _ = create_cylinder_vertices(0.18, 0.02, 16, 0, -0.125, 2.8)
        vertices.extend(grille_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in grille_faces])

    # Calculate normals
    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normals.append(compute_face_normal(v0, v1, v2))

    return vertices, faces, normals


def generate_electrical_panel(panel_type: str = 'distribution') -> Tuple[List, List, List]:
    """
    Generate electrical panel.

    Args:
        panel_type: 'distribution', 'switchgear', 'transformer'
    """
    vertices = []
    faces = []

    if panel_type == 'distribution':
        # Wall-mounted distribution board
        panel_verts, panel_faces, _ = create_box_vertices(0.6, 0.15, 0.8, 0, -0.075, 1.5)
        vertices.extend(panel_verts)
        faces.extend(panel_faces)

        # Door/cover
        offset = len(vertices)
        door_verts, door_faces, _ = create_box_vertices(0.55, 0.02, 0.75, 0, 0.065, 1.5)
        vertices.extend(door_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in door_faces])

    elif panel_type == 'switchgear':
        # Large floor-standing switchgear
        cabinet_verts, cabinet_faces, _ = create_box_vertices(2.0, 0.8, 2.2, 0, 0, 1.1)
        vertices.extend(cabinet_verts)
        faces.extend(cabinet_faces)

    else:  # transformer
        # Pad-mounted transformer
        trans_verts, trans_faces, _ = create_box_vertices(1.5, 1.0, 1.5, 0, 0, 0.75)
        vertices.extend(trans_verts)
        faces.extend(trans_faces)

        # Cooling fins (simplified)
        offset = len(vertices)
        fins_verts, fins_faces, _ = create_box_vertices(1.6, 1.1, 1.2, 0, 0, 0.75)
        vertices.extend(fins_verts)
        faces.extend([(f[0]+offset, f[1]+offset, f[2]+offset) for f in fins_faces])

    # Calculate normals
    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        normals.append(compute_face_normal(v0, v1, v2))

    return vertices, faces, normals


# ============================================================================
# MAIN / TESTING
# ============================================================================

if __name__ == "__main__":
    """Test shape generators."""
    print("="*70)
    print("PARAMETRIC SHAPE LIBRARY - TEST")
    print("="*70)
    print()

    shapes_to_test = [
        ("Office Chair", lambda: generate_chair('office')),
        ("Dining Table (4 seats)", lambda: generate_table(4, 'rectangular')),
        ("Pendant Light", lambda: generate_light_fixture('pendant')),
        ("Sprinkler Head", lambda: generate_sprinkler('head')),
        ("Fire Extinguisher", lambda: generate_fire_extinguisher()),
        ("Toilet", lambda: generate_toilet()),
        ("Wall Sink", lambda: generate_sink('wall')),
        ("Ceiling Diffuser", lambda: generate_hvac_unit('diffuser')),
        ("Distribution Panel", lambda: generate_electrical_panel('distribution')),
    ]

    for name, generator in shapes_to_test:
        vertices, faces, normals = generator()
        print(f"✓ {name:30s} - {len(vertices):3d} vertices, {len(faces):3d} faces")

    print()
    print("="*70)
    print("All shape generators working correctly!")
    print("="*70)
