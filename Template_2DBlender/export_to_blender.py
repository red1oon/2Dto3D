#!/usr/bin/env python3
"""
Blender Export Tool - Visual Validation
========================================
Exports objects from library to Blender .blend file for visual verification.

This demonstrates that:
- Doors are NOT submerged (bottom at floor level)
- Switches at correct height (1.2m - MS 589)
- Outlets at correct height (0.3m - MS 589)
- Toilets on floor properly
- Basins at correct mounting height

Usage:
    blender --background --python export_to_blender.py

Author: DeepSeek Integration Team
Date: 2025-11-23
"""

import sys
import sqlite3
import struct
import numpy as np
from pathlib import Path

try:
    import bpy
    import bmesh
except ImportError:
    print("ERROR: This script must be run from within Blender!")
    print("Usage: blender --background --python export_to_blender.py")
    sys.exit(1)

DB_PATH = "/home/red1/Documents/bonsai/DeepSeek/Ifc_Object_Library.db"


def unpack_vertices(vertices_blob: bytes) -> np.ndarray:
    """Unpack vertex blob to numpy array"""
    if not vertices_blob:
        return np.array([])

    n_floats = len(vertices_blob) // 4
    vertices_flat = struct.unpack(f'<{n_floats}f', vertices_blob)
    return np.array(vertices_flat).reshape(-1, 3)


def unpack_faces(faces_blob: bytes) -> np.ndarray:
    """Unpack faces blob to numpy array"""
    if not faces_blob:
        return np.array([])

    n_indices = len(faces_blob) // 4
    faces_flat = struct.unpack(f'<{n_indices}I', faces_blob)
    return np.array(faces_flat).reshape(-1, 3)


def load_object_from_db(object_type: str):
    """Load object geometry and metadata from database"""

    if not Path(DB_PATH).exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get object with all metadata
    cursor.execute("""
        SELECT
            oc.catalog_id,
            oc.object_type,
            oc.object_name,
            oc.pivot_point,
            oc.origin_offset_x,
            oc.origin_offset_y,
            oc.origin_offset_z,
            oc.behavior_category,
            bg.vertices,
            bg.faces,
            pr.standard_height
        FROM object_catalog oc
        JOIN base_geometries bg ON oc.geometry_hash = bg.geometry_hash
        LEFT JOIN placement_rules pr ON oc.object_type = pr.object_type
        WHERE oc.object_type = ?
        LIMIT 1
    """, (object_type,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"Object type not found: {object_type}")

    (catalog_id, obj_type, obj_name, pivot_point,
     offset_x, offset_y, offset_z, behavior_cat,
     vertices_blob, faces_blob, standard_height) = row

    vertices = unpack_vertices(vertices_blob)
    faces = unpack_faces(faces_blob)

    # Apply pivot correction
    vertices_corrected = vertices + np.array([offset_x, offset_y, offset_z])

    return {
        'object_type': obj_type,
        'object_name': obj_name or f"{obj_type}_{catalog_id}",
        'pivot_point': pivot_point,
        'behavior_category': behavior_cat,
        'vertices': vertices_corrected,
        'faces': faces,
        'standard_height': standard_height
    }


def create_blender_object(obj_data, position, name_suffix=""):
    """Create Blender object from geometry data"""

    # Create mesh
    mesh_name = f"{obj_data['object_name']}{name_suffix}"
    mesh = bpy.data.meshes.new(mesh_name)
    obj = bpy.data.objects.new(mesh_name, mesh)

    # Link to scene
    bpy.context.collection.objects.link(obj)

    # Set geometry
    vertices = obj_data['vertices']
    faces = obj_data['faces']

    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    mesh.update()

    # Set position (apply placement rules)
    final_position = list(position)

    # Apply height rules for wall-mounted objects
    if obj_data['behavior_category'] == 'wall_mounted' and obj_data['standard_height']:
        final_position[2] = obj_data['standard_height']

    obj.location = final_position

    # Set material based on category
    mat = bpy.data.materials.new(name=f"Mat_{obj_data['object_type']}")
    mat.use_nodes = True

    # Color coding
    if obj_data['behavior_category'] == 'floor_mounted':
        mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.6, 0.4, 1.0)  # Beige
    elif obj_data['behavior_category'] == 'wall_mounted':
        mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.9, 0.9, 0.9, 1.0)  # White

    obj.data.materials.append(mat)

    return obj


def create_reference_grid():
    """Create reference grid and measurement helpers"""

    # Floor plane
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "Floor_Reference"

    mat = bpy.data.materials.new(name="Floor_Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.5, 0.5, 0.5, 1.0)
    floor.data.materials.append(mat)

    # Measurement reference - 1m cube at origin
    bpy.ops.mesh.primitive_cube_add(size=1, location=(5, 5, 0.5))
    cube = bpy.context.object
    cube.name = "1m_Reference_Cube"

    mat = bpy.data.materials.new(name="Reference_Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (1.0, 0.0, 0.0, 1.0)
    cube.data.materials.append(mat)

    # Height markers for MS 589 standards
    # 0.3m line (outlet height)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.3, location=(-2, 0, 0.15))
    marker_outlet = bpy.context.object
    marker_outlet.name = "MS589_Outlet_Height_0.3m"

    # 1.2m line (switch height)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=1.2, location=(-2, -1, 0.6))
    marker_switch = bpy.context.object
    marker_switch.name = "MS589_Switch_Height_1.2m"

    # 0.85m line (basin height)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.85, location=(-2, -2, 0.425))
    marker_basin = bpy.context.object
    marker_basin.name = "Basin_Height_0.85m"


def create_test_scene():
    """Create complete test scene with all 5 critical objects"""

    print("=" * 70)
    print("BLENDER EXPORT - Visual Validation")
    print("=" * 70)
    print()

    # Clear existing scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Create reference grid
    print("Creating reference grid and measurements...")
    create_reference_grid()

    # Test objects with positions
    test_objects = [
        {
            'object_type': 'door_single',
            'position': [0, 0, 0],
            'label': 'Door at Floor (should NOT be submerged!)'
        },
        {
            'object_type': 'switch_1gang',
            'position': [2, 0, 0],  # Height will be set to 1.2m by rules
            'label': 'Switch (should be at 1.2m height - MS 589)'
        },
        {
            'object_type': 'toilet',
            'position': [0, 2, 0],
            'label': 'Toilet on Floor'
        },
        {
            'object_type': 'outlet_3pin_ms589',
            'position': [2, 2, 0],  # Height will be set to 0.3m by rules
            'label': 'Outlet (should be at 0.3m height - MS 589)'
        },
        {
            'object_type': 'basin',
            'position': [0, 4, 0],  # Height will be set to 0.85m by rules
            'label': 'Basin (should be at 0.85m height)'
        }
    ]

    print("\nLoading and placing objects:")
    print("-" * 70)

    for test in test_objects:
        try:
            print(f"\n📦 {test['label']}")
            print(f"   Type: {test['object_type']}")
            print(f"   Position: {test['position']}")

            obj_data = load_object_from_db(test['object_type'])

            print(f"   Loaded: {obj_data['object_name']}")
            print(f"   Pivot: {obj_data['pivot_point']}")
            print(f"   Behavior: {obj_data['behavior_category']}")
            print(f"   Vertices: {len(obj_data['vertices'])}")

            blender_obj = create_blender_object(obj_data, test['position'])

            print(f"   ✅ Created in Blender at: {blender_obj.location}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Add camera
    bpy.ops.object.camera_add(location=(8, -8, 5))
    camera = bpy.context.object
    camera.rotation_euler = (np.radians(60), 0, np.radians(45))
    bpy.context.scene.camera = camera

    # Add light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    light = bpy.context.object
    light.data.energy = 2.0

    print()
    print("=" * 70)
    print("✅ SCENE CREATED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("Verification Points:")
    print("1. Door should have bottom AT floor level (Z=0), not submerged")
    print("2. Switch should be at 1.2m height (MS 589 standard)")
    print("3. Outlet should be at 0.3m height (MS 589 standard)")
    print("4. Toilet should sit ON floor (Z=0)")
    print("5. Basin should be at 0.85m height (standard rim height)")
    print()
    print("Reference objects:")
    print("- Red 1m cube at (5, 5, 0.5) for scale reference")
    print("- Height markers showing MS 589 standard heights")
    print()


def save_blend_file():
    """Save the scene to a .blend file"""
    output_path = "/home/red1/Documents/bonsai/DeepSeek/validation_test.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"💾 Saved to: {output_path}")
    print()
    print("To view:")
    print(f"  blender {output_path}")
    print()


if __name__ == "__main__":
    create_test_scene()
    save_blend_file()
