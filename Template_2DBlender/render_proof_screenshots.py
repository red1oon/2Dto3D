#!/usr/bin/env python3
"""
Render proof screenshots from Blender model

Creates multiple viewpoints to demonstrate:
1. Overall building layout
2. Internal walls and rooms
3. Door and window placements
4. Elevation heights (sill levels)
"""

import bpy
import math
from mathutils import Vector

# Output paths
OUTPUT_DIR = "/home/red1/Documents/bonsai/2DtoBlender/Template_2DBlender/output_artifacts/"
BLEND_FILE = OUTPUT_DIR + "TB_LKTN_EXTRACTION_PROOF.blend"

# Render settings
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.image_settings.file_format = 'PNG'


def setup_camera(location, rotation, name="Camera"):
    """Setup camera at specified location and rotation"""
    # Get existing camera or create new
    if "Camera" in bpy.data.objects:
        camera = bpy.data.objects["Camera"]
    else:
        bpy.ops.object.camera_add()
        camera = bpy.context.object
        camera.name = name

    camera.location = Vector(location)
    camera.rotation_euler = rotation
    bpy.context.scene.camera = camera
    return camera


def render_view(output_path, description):
    """Render current view to file"""
    print(f"📸 Rendering: {description}")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"   ✅ Saved: {output_path}")


def main():
    print("=" * 70)
    print("RENDERING PROOF SCREENSHOTS")
    print("=" * 70)

    # Set viewport shading to solid
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'SOLID'

    # View 1: Overall isometric view (from southeast)
    print("\n📷 View 1: Overall Isometric (Southeast)")
    setup_camera(
        location=(35, -35, 25),
        rotation=(math.radians(63), 0, math.radians(45))
    )
    render_view(OUTPUT_DIR + "proof_view1_overall_isometric.png", "Overall building layout")

    # View 2: Top-down view (plan view)
    print("\n📷 View 2: Top-Down Plan View")
    setup_camera(
        location=(13.85, 9.85, 50),
        rotation=(0, 0, 0)
    )
    render_view(OUTPUT_DIR + "proof_view2_topdown_plan.png", "Top-down plan view")

    # View 3: Front elevation (south)
    print("\n📷 View 3: Front Elevation (South)")
    setup_camera(
        location=(13.85, -30, 8),
        rotation=(math.radians(90), 0, 0)
    )
    render_view(OUTPUT_DIR + "proof_view3_front_elevation.png", "Front elevation with windows")

    # View 4: Internal walls closeup (from northwest)
    print("\n📷 View 4: Internal Walls Closeup (Northwest)")
    setup_camera(
        location=(-10, 25, 15),
        rotation=(math.radians(63), 0, math.radians(-45))
    )
    render_view(OUTPUT_DIR + "proof_view4_internal_walls.png", "Internal wall details")

    # View 5: Window sill heights (side view from east)
    print("\n📷 View 5: Window Sill Heights (East Side)")
    setup_camera(
        location=(40, 9.85, 8),
        rotation=(math.radians(90), 0, math.radians(90))
    )
    render_view(OUTPUT_DIR + "proof_view5_window_sills.png", "Window sill heights verification")

    # Summary
    print("\n" + "=" * 70)
    print("RENDERING COMPLETE")
    print("=" * 70)
    print("✅ 5 proof screenshots rendered")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
