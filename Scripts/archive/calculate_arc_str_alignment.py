#!/usr/bin/env python3
"""
Calculate ARC-STR Alignment Offset

Uses density-based analysis to find the main building center in both
ARC and STR DXFs, then calculates the offset needed to align them.

Usage:
    python3 calculate_arc_str_alignment.py
"""

import ezdxf
from pathlib import Path
from collections import defaultdict

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
ARC_DXF = PROJECT_ROOT / "SourceFiles/TERMINAL1DXF/01 ARCHITECT/2. BANGUNAN TERMINAL 1.dxf"
STR_DXF = PROJECT_ROOT / "SourceFiles/TERMINAL1DXF/02 STRUCTURE/T1-2.1_Lyt_1FB_e1P1_240530.dxf"


def find_building_center(dxf_path, building_layers, grid_size_mm=50000):
    """Find main building center using density grid analysis."""
    doc = ezdxf.readfile(str(dxf_path))
    modelspace = doc.modelspace()

    coords = []

    for entity in modelspace:
        # Filter to building layers
        layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else '0'
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

    print(f"   Sampled {len(coords):,} coordinates")

    # Grid analysis - find densest region
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

    # Calculate center of densest region
    center_x = sum(cell_data['xs']) / len(cell_data['xs'])
    center_y = sum(cell_data['ys']) / len(cell_data['ys'])

    print(f"   Densest cell: {cell_key} with {cell_data['count']:,} entities")
    print(f"   Building center: ({center_x/1000:.1f}m, {center_y/1000:.1f}m)")

    return center_x, center_y


def main():
    print("="*80)
    print("CALCULATE ARC-STR ALIGNMENT OFFSET")
    print("="*80)

    # Find ARC building center
    print("\n🔍 Analyzing ARC DXF...")
    print(f"   File: {ARC_DXF.name}")
    arc_layers = ['wall', 'WALL', 'window', 'WIN', 'door', 'DOOR', 'column', 'COL']
    arc_center_x, arc_center_y = find_building_center(ARC_DXF, arc_layers)

    # Find STR building center
    print("\n🔍 Analyzing STR DXF...")
    print(f"   File: {STR_DXF.name}")
    str_layers = ['column', 'COL', 'COLUMN', 'beam', 'BEAM']
    str_center_x, str_center_y = find_building_center(STR_DXF, str_layers)

    # Calculate alignment offset
    offset_x = str_center_x - arc_center_x
    offset_y = str_center_y - arc_center_y

    print("\n" + "="*80)
    print("✅ ALIGNMENT OFFSET CALCULATED")
    print("="*80)
    print(f"\nARC Center:  ({arc_center_x/1000:.1f}m, {arc_center_y/1000:.1f}m)")
    print(f"STR Center:  ({str_center_x/1000:.1f}m, {str_center_y/1000:.1f}m)")
    print(f"\nOffset to align: ({offset_x:.0f}mm, {offset_y:.0f}mm)")
    print(f"                  ({offset_x/1000:.1f}m, {offset_y/1000:.1f}m)")

    print("\n" + "="*80)
    print("COPY TO building_config.json")
    print("="*80)
    print("""
{
  "coordinate_alignment": {
    "enabled": true,
    "strategy": "manual_offset",
    "offset_x_mm": %.0f,
    "offset_y_mm": %.0f,
    "notes": "Density-based alignment - aligns ARC and STR building centers"
  }
}
""" % (offset_x, offset_y))


if __name__ == '__main__':
    main()
