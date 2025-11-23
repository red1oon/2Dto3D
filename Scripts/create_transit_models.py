#!/usr/bin/env python3
"""
Create simple parametric 3D models for transit fixtures not found in free libraries.

These are basic but recognizable shapes that can be added to the geometry library.
"""

import numpy as np
import struct
import hashlib
import sqlite3
from pathlib import Path

# Output paths
LIBRARY_DB = Path("/home/red1/Documents/bonsai/2Dto3D/DatabaseFiles/geometry_library.db")
OBJ_OUTPUT = Path("/home/red1/Documents/bonsai/2Dto3D/SourceFiles/3D_Library/generated")

def create_box(width, depth, height, center=(0, 0, 0)):
    """Create a simple box mesh centered at origin."""
    w, d, h = width/2, depth/2, height/2
    cx, cy, cz = center

    vertices = np.array([
        # Bottom face
        [cx-w, cy-d, cz], [cx+w, cy-d, cz], [cx+w, cy+d, cz], [cx-w, cy+d, cz],
        # Top face
        [cx-w, cy-d, cz+h*2], [cx+w, cy-d, cz+h*2], [cx+w, cy+d, cz+h*2], [cx-w, cy+d, cz+h*2],
    ], dtype=np.float32)

    faces = np.array([
        # Bottom
        [0, 2, 1], [0, 3, 2],
        # Top
        [4, 5, 6], [4, 6, 7],
        # Front
        [0, 1, 5], [0, 5, 4],
        # Back
        [2, 3, 7], [2, 7, 6],
        # Left
        [0, 4, 7], [0, 7, 3],
        # Right
        [1, 2, 6], [1, 6, 5],
    ], dtype=np.int32)

    return vertices, faces

def create_cylinder(radius, height, segments=16, center=(0, 0, 0)):
    """Create a cylinder mesh."""
    cx, cy, cz = center
    vertices = []
    faces = []

    # Bottom center
    vertices.append([cx, cy, cz])
    # Top center
    vertices.append([cx, cy, cz + height])

    # Circle vertices
    for i in range(segments):
        angle = 2 * np.pi * i / segments
        x = cx + radius * np.cos(angle)
        y = cy + radius * np.sin(angle)
        vertices.append([x, y, cz])           # Bottom
        vertices.append([x, y, cz + height])  # Top

    # Bottom face
    for i in range(segments):
        i1 = 2 + i * 2
        i2 = 2 + ((i + 1) % segments) * 2
        faces.append([0, i2, i1])

    # Top face
    for i in range(segments):
        i1 = 3 + i * 2
        i2 = 3 + ((i + 1) % segments) * 2
        faces.append([1, i1, i2])

    # Side faces
    for i in range(segments):
        b1 = 2 + i * 2
        t1 = 3 + i * 2
        b2 = 2 + ((i + 1) % segments) * 2
        t2 = 3 + ((i + 1) % segments) * 2
        faces.append([b1, b2, t2])
        faces.append([b1, t2, t1])

    return np.array(vertices, dtype=np.float32), np.array(faces, dtype=np.int32)

def merge_meshes(mesh_list):
    """Merge multiple meshes into one."""
    all_vertices = []
    all_faces = []
    vertex_offset = 0

    for vertices, faces in mesh_list:
        all_vertices.append(vertices)
        all_faces.append(faces + vertex_offset)
        vertex_offset += len(vertices)

    return np.vstack(all_vertices), np.vstack(all_faces)

# =============================================================================
# Transit Fixture Models
# =============================================================================

def create_life_jacket_cabinet():
    """Life jacket storage cabinet - wall mounted box with handle."""
    # Main cabinet body
    cabinet = create_box(0.6, 0.3, 1.2)

    # Handle (small cylinder on front)
    handle_v, handle_f = create_cylinder(0.02, 0.15, 8, center=(0, -0.15, 0.6))

    vertices, faces = merge_meshes([cabinet, (handle_v, handle_f)])
    return vertices, faces, "life_jacket_cabinet"

def create_usb_charging_station():
    """USB charging kiosk - vertical pillar with port panel."""
    # Main pillar
    pillar = create_box(0.4, 0.3, 1.2)

    # Port panel (recessed area)
    panel = create_box(0.3, 0.05, 0.4, center=(0, -0.125, 0.7))

    vertices, faces = merge_meshes([pillar, panel])
    return vertices, faces, "usb_charging_station"

def create_luggage_scale():
    """Luggage weighing scale - platform with display pole."""
    # Platform base
    platform = create_box(0.8, 0.6, 0.1)

    # Display pole
    pole_v, pole_f = create_cylinder(0.03, 1.0, 8, center=(0.3, 0, 0.1))

    # Display screen
    screen = create_box(0.2, 0.05, 0.15, center=(0.3, -0.05, 1.0))

    vertices, faces = merge_meshes([platform, (pole_v, pole_f), screen])
    return vertices, faces, "luggage_scale"

def create_weather_display():
    """Weather monitoring display - wall-mounted screen."""
    # Screen frame
    frame = create_box(2.0, 0.1, 1.0)

    # Screen surface (slightly recessed)
    screen = create_box(1.8, 0.05, 0.8, center=(0, -0.025, 0.1))

    vertices, faces = merge_meshes([frame, screen])
    return vertices, faces, "weather_display"

def create_currency_exchange_booth():
    """Currency exchange booth - small enclosed counter."""
    # Main booth structure
    booth = create_box(2.5, 2.0, 2.8)

    # Counter window opening (represented as recessed panel)
    window = create_box(1.0, 0.1, 0.8, center=(0, -0.95, 1.2))

    # Counter surface
    counter = create_box(1.2, 0.4, 0.05, center=(0, -0.8, 1.0))

    vertices, faces = merge_meshes([booth, window, counter])
    return vertices, faces, "currency_exchange_booth"

def create_retractable_stanchion():
    """Queue barrier post with retractable belt cassette."""
    # Post base (circular)
    base_v, base_f = create_cylinder(0.15, 0.03, 16)

    # Main post
    post_v, post_f = create_cylinder(0.025, 1.0, 12, center=(0, 0, 0.03))

    # Belt cassette (box at top)
    cassette = create_box(0.08, 0.08, 0.1, center=(0, 0, 0.95))

    vertices, faces = merge_meshes([(base_v, base_f), (post_v, post_f), cassette])
    return vertices, faces, "retractable_stanchion"

def create_atm_kiosk():
    """ATM machine - freestanding kiosk."""
    # Main body
    body = create_box(0.6, 0.7, 1.5)

    # Screen area (recessed)
    screen = create_box(0.4, 0.05, 0.3, center=(0, -0.325, 1.1))

    # Keypad area
    keypad = create_box(0.25, 0.1, 0.15, center=(0, -0.3, 0.7))

    vertices, faces = merge_meshes([body, screen, keypad])
    return vertices, faces, "atm_kiosk"

def create_info_kiosk():
    """Information kiosk with touchscreen."""
    # Pedestal base
    base_v, base_f = create_cylinder(0.2, 0.1, 16)

    # Stem
    stem_v, stem_f = create_cylinder(0.05, 1.0, 12, center=(0, 0, 0.1))

    # Screen (angled)
    screen = create_box(0.5, 0.05, 0.4, center=(0, -0.05, 1.1))

    vertices, faces = merge_meshes([(base_v, base_f), (stem_v, stem_f), screen])
    return vertices, faces, "info_kiosk"

def create_ceiling_fan():
    """Detailed ceiling fan with 5 blades - high polygon for impressive visuals."""
    meshes = []

    # Mounting rod (hangs down from ceiling)
    rod_v, rod_f = create_cylinder(0.02, 0.4, 12, center=(0, 0, 0))
    meshes.append((rod_v, rod_f))

    # Motor housing - detailed cylinder (32 segments for smooth appearance)
    housing_v, housing_f = create_cylinder(0.12, 0.15, 32, center=(0, 0, -0.15))
    meshes.append((housing_v, housing_f))

    # Motor cap (bottom dome-like)
    cap_v, cap_f = create_cylinder(0.08, 0.05, 24, center=(0, 0, -0.3))
    meshes.append((cap_v, cap_f))

    # 5 fan blades with detailed geometry
    num_blades = 5
    blade_length = 0.6
    blade_width = 0.12
    blade_thickness = 0.015

    for i in range(num_blades):
        angle = 2 * np.pi * i / num_blades

        # Create blade as angled box
        # Blade extends outward from motor
        blade_verts = []
        blade_faces = []

        # Inner edge (near motor)
        inner_radius = 0.1
        outer_radius = inner_radius + blade_length

        # Blade has 8 vertices per section, multiple sections for detail
        sections = 8  # More sections = smoother blade

        for s in range(sections + 1):
            t = s / sections
            r = inner_radius + t * blade_length

            # Blade twist angle (fans have twisted blades)
            twist = t * 0.3  # Radians

            # 4 corners at this section
            hw = blade_width / 2 * (1 - t * 0.3)  # Taper toward tip
            ht = blade_thickness / 2

            # Rotate by blade angle and twist
            cos_a = np.cos(angle + twist)
            sin_a = np.sin(angle + twist)

            # Local coords -> world coords
            x_base = r * np.cos(angle)
            y_base = r * np.sin(angle)

            # Perpendicular to blade direction
            perp_x = -np.sin(angle)
            perp_y = np.cos(angle)

            # Add 4 vertices for this section
            z_base = -0.22  # At motor level
            blade_verts.extend([
                [x_base + perp_x * hw, y_base + perp_y * hw, z_base - ht],  # Bottom-left
                [x_base + perp_x * hw, y_base + perp_y * hw, z_base + ht],  # Top-left
                [x_base - perp_x * hw, y_base - perp_y * hw, z_base + ht],  # Top-right
                [x_base - perp_x * hw, y_base - perp_y * hw, z_base - ht],  # Bottom-right
            ])

        # Create faces between sections
        for s in range(sections):
            base = len(blade_verts) - (sections + 1) * 4 + s * 4
            next_base = base + 4

            # Front face
            blade_faces.append([base + 0, next_base + 0, next_base + 1])
            blade_faces.append([base + 0, next_base + 1, base + 1])

            # Back face
            blade_faces.append([base + 2, next_base + 2, next_base + 3])
            blade_faces.append([base + 2, next_base + 3, base + 3])

            # Top face
            blade_faces.append([base + 1, next_base + 1, next_base + 2])
            blade_faces.append([base + 1, next_base + 2, base + 2])

            # Bottom face
            blade_faces.append([base + 0, base + 3, next_base + 3])
            blade_faces.append([base + 0, next_base + 3, next_base + 0])

        # Cap ends
        # Inner cap
        base = len(blade_verts) - (sections + 1) * 4
        blade_faces.append([base + 0, base + 1, base + 2])
        blade_faces.append([base + 0, base + 2, base + 3])

        # Outer cap (tip)
        tip = len(blade_verts) - 4
        blade_faces.append([tip + 0, tip + 3, tip + 2])
        blade_faces.append([tip + 0, tip + 2, tip + 1])

        meshes.append((np.array(blade_verts, dtype=np.float32),
                      np.array(blade_faces, dtype=np.int32)))

    vertices, faces = merge_meshes(meshes)
    return vertices, faces, "ceiling_fan"

def create_bench_seating():
    """Airport-style bench seating (3-seater) with armrests."""
    meshes = []

    # Seat frame (long beam)
    seat_v, seat_f = create_box(1.8, 0.5, 0.08, center=(0, 0, 0.42))
    meshes.append((seat_v, seat_f))

    # Backrest
    back_v, back_f = create_box(1.8, 0.08, 0.4, center=(0, 0.21, 0.7))
    meshes.append((back_v, back_f))

    # Legs (4 corners)
    leg_positions = [(-0.8, -0.15), (0.8, -0.15), (-0.8, 0.15), (0.8, 0.15)]
    for lx, ly in leg_positions:
        leg_v, leg_f = create_box(0.04, 0.04, 0.42, center=(lx, ly, 0))
        meshes.append((leg_v, leg_f))

    # Armrests (4 dividers)
    arm_positions = [-0.9, -0.3, 0.3, 0.9]
    for ax in arm_positions:
        arm_v, arm_f = create_box(0.03, 0.4, 0.25, center=(ax, 0, 0.55))
        meshes.append((arm_v, arm_f))

    vertices, faces = merge_meshes(meshes)
    return vertices, faces, "bench_seating"

# =============================================================================
# Export Functions
# =============================================================================

def export_obj(vertices, faces, filepath):
    """Export mesh to OBJ format."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w') as f:
        f.write(f"# Transit fixture model\n")
        f.write(f"# Vertices: {len(vertices)}, Faces: {len(faces)}\n\n")

        for v in vertices:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

        f.write("\n")

        for face in faces:
            # OBJ uses 1-based indexing
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

    print(f"  Exported: {filepath}")

def add_to_library(vertices, faces, fixture_type, ifc_class="IfcFurniture"):
    """Add model to geometry library database."""
    if not LIBRARY_DB.exists():
        print(f"  Warning: Library DB not found at {LIBRARY_DB}")
        return

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
    ''', (geom_hash, ifc_class, fixture_type, fixture_type.replace('_', ' ').title(),
          len(vertices), len(faces)))

    conn.commit()
    conn.close()

    print(f"  Added to library: {fixture_type} ({len(vertices)} verts, {len(faces)} faces)")

def main():
    """Generate all transit fixture models."""
    print("=" * 60)
    print("TRANSIT FIXTURE MODEL GENERATOR")
    print("=" * 60)

    # Create output directory
    OBJ_OUTPUT.mkdir(parents=True, exist_ok=True)

    # Model generators
    generators = [
        create_life_jacket_cabinet,
        create_usb_charging_station,
        create_luggage_scale,
        create_weather_display,
        create_currency_exchange_booth,
        create_retractable_stanchion,
        create_atm_kiosk,
        create_info_kiosk,
        create_ceiling_fan,
        create_bench_seating,
    ]

    print(f"\nGenerating {len(generators)} transit fixture models...\n")

    for gen_func in generators:
        vertices, faces, fixture_type = gen_func()

        # Export to OBJ
        obj_path = OBJ_OUTPUT / f"{fixture_type}.obj"
        export_obj(vertices, faces, obj_path)

        # Add to library
        add_to_library(vertices, faces, fixture_type)

    print("\n" + "=" * 60)
    print("MODEL GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nOBJ files: {OBJ_OUTPUT}")
    print(f"Library DB: {LIBRARY_DB}")

if __name__ == '__main__':
    main()
