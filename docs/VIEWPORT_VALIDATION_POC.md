# Viewport Validation POC - Specification

**Version:** 1.0
**Date:** 2025-11-19
**Status:** Draft

---

## Objective

Prove that the text-based audit report accurately represents what Blender's 3D viewport displays. This validates the assumption that "geometry on paper = geometry by sight".

---

## Approach

1. **Generate database** with known geometry
2. **Run audit** to get text metrics
3. **Launch Blender silently** (background mode)
4. **Bake and render** viewport snapshot
5. **Extract metrics from viewport** (bounding box, dimensions)
6. **Compare** audit metrics vs viewport metrics

If they match, we trust the audit. If not, we find the gap.

---

## POC Implementation

### Step 1: Silent Blender Snapshot Script

```python
# viewport_snapshot.py - Run in Blender background mode

import bpy
import sys
import json

def take_viewport_snapshot(db_path, output_image, output_json):
    """
    Load database, bake to blend, render viewport, extract metrics.
    """

    # 1. Bake database to blend
    from bonsai.bim.module.federation.blend_cache import create_cache
    create_cache(bpy.context, db_path, mode="full")

    # 2. Setup camera for top-down orthographic view
    cam = bpy.data.cameras.new("AuditCam")
    cam.type = 'ORTHO'
    cam_obj = bpy.data.objects.new("AuditCam", cam)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # Position camera above scene center
    # Get scene bounds first
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')

    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            for v in obj.data.vertices:
                co = obj.matrix_world @ v.co
                min_x = min(min_x, co.x)
                max_x = max(max_x, co.x)
                min_y = min(min_y, co.y)
                max_y = max(max_y, co.y)
                min_z = min(min_z, co.z)
                max_z = max(max_z, co.z)

    # Center camera
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    cam_obj.location = (center_x, center_y, max_z + 50)
    cam_obj.rotation_euler = (0, 0, 0)  # Looking down

    # Set orthographic scale to fit scene
    extent = max(max_x - min_x, max_y - min_y)
    cam.ortho_scale = extent * 1.2

    # 3. Render settings
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.filepath = output_image

    # Use workbench render for fast solid view
    bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'

    # 4. Render
    bpy.ops.render.render(write_still=True)

    # 5. Extract viewport metrics
    metrics = {
        'bounding_box': {
            'min': [min_x, min_y, min_z],
            'max': [max_x, max_y, max_z],
            'size': [max_x - min_x, max_y - min_y, max_z - min_z]
        },
        'object_count': len([o for o in bpy.data.objects if o.type == 'MESH']),
        'total_vertices': sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'),
        'total_faces': sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'),
    }

    # Count by IFC class
    class_counts = {}
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and 'ifc_class' in obj:
            ifc_class = obj['ifc_class']
            class_counts[ifc_class] = class_counts.get(ifc_class, 0) + 1
    metrics['by_ifc_class'] = class_counts

    # Save metrics
    with open(output_json, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"Snapshot saved: {output_image}")
    print(f"Metrics saved: {output_json}")

    return metrics


if __name__ == "__main__":
    # Usage: blender --background --python viewport_snapshot.py -- db_path output.png output.json
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
        if len(args) >= 3:
            take_viewport_snapshot(args[0], args[1], args[2])
```

### Step 2: Comparison Script

```python
# compare_audit_viewport.py

import json
import sys

def compare(audit_report_path, viewport_metrics_path):
    """
    Compare audit report metrics with viewport-extracted metrics.
    """

    # Parse audit report (or we could output JSON from audit)
    # For POC, we'll compare viewport JSON with database query

    with open(viewport_metrics_path) as f:
        viewport = json.load(f)

    # Compare key metrics
    print("=" * 70)
    print("AUDIT vs VIEWPORT COMPARISON")
    print("=" * 70)

    print("\nBOUNDING BOX")
    print("-" * 70)
    vp_size = viewport['bounding_box']['size']
    print(f"  Viewport: {vp_size[0]:.1f}m x {vp_size[1]:.1f}m x {vp_size[2]:.1f}m")
    # TODO: Compare with audit

    print("\nELEMENT COUNTS")
    print("-" * 70)
    print(f"  Viewport objects: {viewport['object_count']}")
    print(f"  Viewport vertices: {viewport['total_vertices']}")
    print(f"  Viewport faces: {viewport['total_faces']}")

    print("\nBY IFC CLASS")
    print("-" * 70)
    for ifc_class, count in sorted(viewport['by_ifc_class'].items()):
        print(f"  {ifc_class}: {count}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        compare(sys.argv[1], sys.argv[2])
```

### Step 3: Runner Script

```bash
#!/bin/bash
# validate_viewport.sh

DB_PATH="$1"
OUTPUT_DIR="${2:-/tmp/viewport_validation}"

mkdir -p "$OUTPUT_DIR"

echo "=== VIEWPORT VALIDATION POC ==="
echo ""

# Step 1: Run audit
echo "1. Running audit..."
python3 audit_database.py "$DB_PATH" --output "$OUTPUT_DIR/audit_report.txt"

# Step 2: Launch Blender silently for snapshot
echo "2. Rendering viewport snapshot..."
blender --background --python viewport_snapshot.py -- \
    "$DB_PATH" \
    "$OUTPUT_DIR/viewport.png" \
    "$OUTPUT_DIR/viewport_metrics.json"

# Step 3: Compare
echo "3. Comparing results..."
python3 compare_audit_viewport.py \
    "$OUTPUT_DIR/audit_report.txt" \
    "$OUTPUT_DIR/viewport_metrics.json"

echo ""
echo "=== OUTPUTS ==="
echo "  Audit report: $OUTPUT_DIR/audit_report.txt"
echo "  Viewport image: $OUTPUT_DIR/viewport.png"
echo "  Viewport metrics: $OUTPUT_DIR/viewport_metrics.json"
```

---

## Validation Criteria

### Must Match (tolerance ±0.1m):
- Bounding box dimensions (X, Y, Z)
- Total element count
- Total vertex count
- Total face count
- Count per IFC class

### Should Match:
- Element positions (center coordinates)
- Orientation distribution (E-W vs N-S)

### Visual Inspection:
- Screenshot should show recognizable building shape
- No obvious holes or missing geometry
- Scale appears correct

---

## Success Criteria

**POC passes if:**
1. All "Must Match" metrics are within tolerance
2. Visual inspection shows expected building form
3. No unexpected artifacts (inside-out faces, z-fighting)

**If POC fails:**
- Identify which metric diverges
- Trace back through pipeline to find the decode gap
- Fix and re-run

---

## Usage

```bash
# Run full validation
./validate_viewport.sh ~/Documents/bonsai/2Dto3D/DatabaseFiles/Terminal1_ARC_STR.db

# Or step by step
python3 audit_database.py Terminal1_ARC_STR.db -o audit.txt

blender --background --python viewport_snapshot.py -- \
    Terminal1_ARC_STR.db viewport.png viewport.json

python3 compare_audit_viewport.py audit.txt viewport.json
```

---

## Expected Output

```
=== VIEWPORT VALIDATION POC ===

1. Running audit...
   [Audit report generated]

2. Rendering viewport snapshot...
   [Blender bakes and renders]

3. Comparing results...

======================================================================
AUDIT vs VIEWPORT COMPARISON
======================================================================

BOUNDING BOX
----------------------------------------------------------------------
  Audit:    110.2m x 138.7m x 12.0m
  Viewport: 110.2m x 138.7m x 12.0m
  Status:   ✓ MATCH

ELEMENT COUNTS
----------------------------------------------------------------------
  Audit:    740 elements, 7298 vertices, 11636 faces
  Viewport: 740 objects, 7298 vertices, 11636 faces
  Status:   ✓ MATCH

BY IFC CLASS
----------------------------------------------------------------------
  IfcPlate:  Audit=418, Viewport=418  ✓
  IfcBeam:   Audit=111, Viewport=111  ✓
  IfcSlab:   Audit=90,  Viewport=90   ✓
  IfcWall:   Audit=72,  Viewport=72   ✓
  IfcColumn: Audit=45,  Viewport=45   ✓
  IfcWindow: Audit=4,   Viewport=4    ✓

======================================================================
VALIDATION: PASSED ✓
======================================================================
```

---

## Next Steps After POC

If POC validates successfully:
1. Trust audit engine for rapid iteration
2. Only use Blender for final visual verification
3. Potentially add geometry sanity checks (normals, manifold)

If POC fails:
1. Debug the specific mismatch
2. Update decode layer to match Blender exactly
3. Re-run POC until passes
