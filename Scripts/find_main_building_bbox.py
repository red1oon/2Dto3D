#!/usr/bin/env python3
"""
Find Main Building Bounding Box

Automatically determines the spatial filter coordinates for extracting
only the main building from a DXF file.

Usage:
    python3 find_main_building_bbox.py <dxf_file> <reference_ifc_db>

Example:
    python3 find_main_building_bbox.py \
        "SourceFiles/TERMINAL1DXF/01 ARCHITECT/2. BANGUNAN TERMINAL 1.dxf" \
        "/home/red1/Documents/bonsai/8_IFC/enhanced_federation.db"
"""

import sys
import sqlite3
import ezdxf
from pathlib import Path
from collections import defaultdict


def get_ifc_building_size(ifc_db_path):
    """Get building dimensions from IFC database."""
    conn = sqlite3.connect(ifc_db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            MIN(t.center_x), MAX(t.center_x),
            MIN(t.center_y), MAX(t.center_y)
        FROM element_transforms t
        JOIN elements_meta m ON t.guid = m.guid
        WHERE m.ifc_class IN ('IfcWall', 'IfcColumn', 'IfcSlab')
    """)

    bounds = cursor.fetchone()
    conn.close()

    if not bounds or bounds[0] is None:
        raise ValueError("Could not determine IFC building size")

    width = bounds[1] - bounds[0]
    depth = bounds[3] - bounds[2]

    return width, depth


def analyze_dxf_density(dxf_path, grid_size_mm=50000):
    """Find densest region in DXF file using grid analysis."""
    doc = ezdxf.readfile(dxf_path)
    modelspace = doc.modelspace()

    # Focus on building geometry layers
    building_layers = ['wall', 'WALL', 'WALL1', 'window', 'WIN', 'door', 'DOOR',
                       'column', 'COL', 'staircase', 'STAIR']

    # Collect coordinates from geometric entities
    coords = []

    for entity in modelspace:
        # Filter to building layers
        layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else 'UNKNOWN'
        if not any(bl.lower() in layer.lower() for bl in building_layers):
            continue

        # Extract coordinates
        if hasattr(entity.dxf, 'insert'):
            coords.append((entity.dxf.insert.x, entity.dxf.insert.y))
        elif hasattr(entity.dxf, 'start'):
            coords.append((entity.dxf.start.x, entity.dxf.start.y))
            if hasattr(entity.dxf, 'end'):
                coords.append((entity.dxf.end.x, entity.dxf.end.y))
        elif hasattr(entity.dxf, 'center'):
            coords.append((entity.dxf.center.x, entity.dxf.center.y))

    if not coords:
        raise ValueError("No building geometry found in DXF")

    print(f"📊 Sampled {len(coords):,} geometric coordinates")

    # Grid analysis
    cells = defaultdict(lambda: {'count': 0, 'xs': [], 'ys': []})

    for x, y in coords:
        cell_x = int(x / grid_size_mm)
        cell_y = int(y / grid_size_mm)
        cell_key = (cell_x, cell_y)

        cells[cell_key]['count'] += 1
        cells[cell_key]['xs'].append(x)
        cells[cell_key]['ys'].append(y)

    # Find densest cell
    densest_cell = max(cells.items(), key=lambda x: x[1]['count'])
    cell_key, cell_data = densest_cell

    print(f"\n🎯 Densest region: Cell {cell_key} with {cell_data['count']:,} entities")

    # Calculate center of densest region
    center_x = sum(cell_data['xs']) / len(cell_data['xs'])
    center_y = sum(cell_data['ys']) / len(cell_data['ys'])

    return center_x, center_y


def create_bounding_box(center_x, center_y, target_width_m, target_depth_m):
    """Create bounding box around center point."""
    # Convert to mm and add 10% margin
    margin = 1.1
    half_width = (target_width_m * margin * 1000) / 2
    half_depth = (target_depth_m * margin * 1000) / 2

    bbox = {
        'min_x': center_x - half_width,
        'max_x': center_x + half_width,
        'min_y': center_y - half_depth,
        'max_y': center_y + half_depth
    }

    return bbox


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    dxf_file = sys.argv[1]
    ifc_db = sys.argv[2]

    print("="*80)
    print("FIND MAIN BUILDING BOUNDING BOX")
    print("="*80)

    # Step 1: Get target size from IFC
    print(f"\n📐 Step 1: Analyzing IFC building dimensions...")
    try:
        target_width, target_depth = get_ifc_building_size(ifc_db)
        print(f"   Target building size: {target_width:.1f}m × {target_depth:.1f}m")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        sys.exit(1)

    # Step 2: Find densest region in DXF
    print(f"\n🔍 Step 2: Finding densest building region in DXF...")
    try:
        center_x, center_y = analyze_dxf_density(dxf_file)
        print(f"   Building center: ({center_x/1000:.1f}m, {center_y/1000:.1f}m)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        sys.exit(1)

    # Step 3: Create bounding box
    print(f"\n📦 Step 3: Creating bounding box...")
    bbox = create_bounding_box(center_x, center_y, target_width, target_depth)

    print(f"   X: {bbox['min_x']:.2f} to {bbox['max_x']:.2f} mm")
    print(f"   Y: {bbox['min_y']:.2f} to {bbox['max_y']:.2f} mm")
    print(f"   Size: {(bbox['max_x'] - bbox['min_x'])/1000:.1f}m × {(bbox['max_y'] - bbox['min_y'])/1000:.1f}m")

    # Step 4: Output Python code
    print("\n" + "="*80)
    print("✅ SPATIAL FILTER CONFIGURATION")
    print("="*80)
    print("\nCopy this into your extraction script:\n")

    print("SPATIAL_FILTER = {")
    print(f"    'min_x': {bbox['min_x']:.2f},")
    print(f"    'max_x': {bbox['max_x']:.2f},")
    print(f"    'min_y': {bbox['min_y']:.2f},")
    print(f"    'max_y': {bbox['max_y']:.2f}")
    print("}")

    print("\nUsage:")
    print("converter = DXFToDatabase(")
    print("    dxf_path='...',")
    print("    output_db='...',")
    print("    template_library=template_lib,")
    print("    spatial_filter=SPATIAL_FILTER  # ← Apply filter")
    print(")")

    print("\n" + "="*80)
    print("⚠️  VALIDATION REQUIRED")
    print("="*80)
    print("After extraction, verify building dimensions match IFC:")
    print(f"Expected: {target_width:.1f}m × {target_depth:.1f}m (±20m tolerance)")


if __name__ == '__main__':
    main()
