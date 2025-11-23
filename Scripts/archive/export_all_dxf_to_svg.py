#!/usr/bin/env python3
"""
Export all Terminal 1 DXF files to SVG - simple line rendering
Shows exactly what modeller exported in the DXF
"""

import ezdxf
from pathlib import Path
from collections import defaultdict

def dxf_to_svg(dxf_path: str, output_path: str, title: str, bounds=None):
    """Convert DXF to SVG showing all line work (optionally filtered to bounds)"""

    print(f"\nProcessing: {Path(dxf_path).name}")
    if bounds:
        print(f"  Filter: X=[{bounds['min_x']:,}, {bounds['max_x']:,}] Y=[{bounds['min_y']:,}, {bounds['max_y']:,}]")

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    # Collect all line geometry
    lines = []
    circles = []
    polylines = []
    arcs = []

    for entity in msp:
        etype = entity.dxftype()

        # Apply spatial filter if provided
        if bounds and etype == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            cx, cy = (start.x + end.x) / 2, (start.y + end.y) / 2
            if not (bounds['min_x'] <= cx <= bounds['max_x'] and bounds['min_y'] <= cy <= bounds['max_y']):
                continue

        if etype == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            lines.append({'x1': start.x, 'y1': start.y, 'x2': end.x, 'y2': end.y})

        elif etype == 'CIRCLE':
            center = entity.dxf.center
            if bounds:
                if not (bounds['min_x'] <= center.x <= bounds['max_x'] and bounds['min_y'] <= center.y <= bounds['max_y']):
                    continue
            circles.append({'cx': center.x, 'cy': center.y, 'r': entity.dxf.radius})

        elif etype in ['LWPOLYLINE', 'POLYLINE']:
            points = list(entity.get_points())
            if len(points) >= 2:
                if bounds:
                    cx = sum(p[0] for p in points) / len(points)
                    cy = sum(p[1] for p in points) / len(points)
                    if not (bounds['min_x'] <= cx <= bounds['max_x'] and bounds['min_y'] <= cy <= bounds['max_y']):
                        continue
                polylines.append({'points': [(p[0], p[1]) for p in points]})

        elif etype == 'ARC':
            center = entity.dxf.center
            arcs.append({
                'cx': center.x, 'cy': center.y,
                'r': entity.dxf.radius,
                'start': entity.dxf.start_angle,
                'end': entity.dxf.end_angle
            })

    total = len(lines) + len(circles) + len(polylines) + len(arcs)
    print(f"  Lines: {len(lines):,}, Circles: {len(circles):,}, Polylines: {len(polylines):,}, Arcs: {len(arcs):,}")
    print(f"  Total: {total:,} entities")

    if total == 0:
        print("  ✗ No geometry found")
        return

    # Calculate bounds from ACTUAL extracted geometry (not filter bounds)
    # The filter is used to select entities, but viewport must fit the actual geometry
    all_coords = []
    for line in lines:
        all_coords.extend([(line['x1'], line['y1']), (line['x2'], line['y2'])])
    for circle in circles:
        all_coords.extend([
            (circle['cx'] - circle['r'], circle['cy']),
            (circle['cx'] + circle['r'], circle['cy'])
        ])
    for polyline in polylines:
        all_coords.extend(polyline['points'])
    for arc in arcs:
        # Include arc bounds (approximate with center +/- radius)
        all_coords.extend([
            (arc['cx'] - arc['r'], arc['cy']),
            (arc['cx'] + arc['r'], arc['cy'])
        ])

    if not all_coords:
        print("  ✗ No coordinates found in extracted geometry")
        return

    xs = [c[0] for c in all_coords]
    ys = [c[1] for c in all_coords]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    print(f"  Bounds: X=[{min_x:.0f}, {max_x:.0f}] Y=[{min_y:.0f}, {max_y:.0f}]")
    print(f"  Size: {(max_x-min_x)/1000:.1f}m × {(max_y-min_y)/1000:.1f}m")

    # Create SVG
    width, height, padding = 1600, 1200, 50

    data_width = max_x - min_x
    data_height = max_y - min_y
    scale = min((width - 2*padding) / data_width, (height - 2*padding) / data_height) * 0.95

    offset_x = padding - min_x * scale
    offset_y = padding - min_y * scale

    svg_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        '  <style>',
        '    text { font-family: Arial; }',
        '    .title { font-size: 20px; font-weight: bold; fill: #333; }',
        '    .info { font-size: 12px; fill: #666; }',
        '  </style>',
        f'  <rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'  <text x="{width/2}" y="30" class="title" text-anchor="middle">{title}</text>',
        f'  <text x="{width/2}" y="50" class="info" text-anchor="middle">Total: {total:,} entities | Scale: 1:{1/scale:.0f}</text>',
    ]

    # Draw lines
    for line in lines:
        x1 = line['x1'] * scale + offset_x
        y1 = height - (line['y1'] * scale + offset_y)
        x2 = line['x2'] * scale + offset_x
        y2 = height - (line['y2'] * scale + offset_y)
        svg_lines.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000" stroke-width="0.5" opacity="0.7"/>')

    # Draw circles
    for circle in circles:
        cx = circle['cx'] * scale + offset_x
        cy = height - (circle['cy'] * scale + offset_y)
        r = circle['r'] * scale
        svg_lines.append(f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#000" stroke-width="0.5" opacity="0.7"/>')

    # Draw polylines
    for polyline in polylines:
        points = ' '.join([
            f"{p[0]*scale+offset_x},{height-(p[1]*scale+offset_y)}"
            for p in polyline['points']
        ])
        svg_lines.append(f'  <polyline points="{points}" fill="none" stroke="#000" stroke-width="0.5" opacity="0.7"/>')

    # Draw arcs (convert DXF arc to SVG path)
    import math
    for arc in arcs:
        cx = arc['cx'] * scale + offset_x
        cy = height - (arc['cy'] * scale + offset_y)
        r = arc['r'] * scale
        start_rad = math.radians(arc['start'])
        end_rad = math.radians(arc['end'])

        # Calculate start and end points
        x1 = cx + r * math.cos(start_rad)
        y1 = cy - r * math.sin(start_rad)
        x2 = cx + r * math.cos(end_rad)
        y2 = cy - r * math.sin(end_rad)

        # Determine if large arc (>180 degrees)
        angle_diff = (arc['end'] - arc['start']) % 360
        large_arc = 1 if angle_diff > 180 else 0

        # SVG path for arc
        svg_lines.append(f'  <path d="M {x1},{y1} A {r},{r} 0 {large_arc},0 {x2},{y2}" fill="none" stroke="#000" stroke-width="0.5" opacity="0.7"/>')

    svg_lines.append('</svg>')

    # Write file
    with open(output_path, 'w') as f:
        f.write('\n'.join(svg_lines))

    print(f"  ✓ Saved: {output_path}")

def main():
    base_path = Path(__file__).parent.parent / 'SourceFiles' / 'TERMINAL1DXF'
    output_dir = Path(__file__).parent.parent / 'SourceFiles' / 'DXF_PlanViews'
    output_dir.mkdir(exist_ok=True)

    # Terminal 1 bounds - MUST MATCH generation_log.txt bounds used by database
    # These are the VERIFIED WORKING bounds that extracted 662 STR elements correctly
    arc_bounds = {'min_x': -1620000, 'max_x': -1560000, 'min_y': -90000, 'max_y': -40000}
    str_bounds = {'min_x': 342000, 'max_x': 402000, 'min_y': -336000, 'max_y': -296000}

    dxf_files = [
        {
            'path': base_path / '01 ARCHITECT' / '2. BANGUNAN TERMINAL 1.dxf',
            'title': 'Terminal 1 - ARCHITECT (All Floors) - DOME BUILDING',
            'output': 'ARC_AllFloors.svg',
            'bounds': arc_bounds
        },
        {
            'path': base_path / '02 STRUCTURE' / 'T1-2.0_Lyt_GB_e2P2_240711.dxf',
            'title': 'Terminal 1 - STRUCTURE Ground/Basement (GB)',
            'output': 'STR_GB.svg',
            'bounds': str_bounds
        },
        {
            'path': base_path / '02 STRUCTURE' / 'T1-2.1_Lyt_1FB_e1P1_240530.dxf',
            'title': 'Terminal 1 - STRUCTURE 1st Floor (1F)',
            'output': 'STR_1F.svg',
            'bounds': str_bounds
        },
        {
            'path': base_path / '02 STRUCTURE' / 'T1-2.3_Lyt_3FB_e1P1_240530.dxf',
            'title': 'Terminal 1 - STRUCTURE 3rd Floor (3F)',
            'output': 'STR_3F.svg',
            'bounds': str_bounds
        },
        {
            'path': base_path / '02 STRUCTURE' / 'T1-2.4_Lyt_4FB-6FB_e1P1_240530.dxf',
            'title': 'Terminal 1 - STRUCTURE 4th-6th Floors (4F-6F)',
            'output': 'STR_4F-6F.svg',
            'bounds': str_bounds
        },
        {
            'path': base_path / '02 STRUCTURE' / 'T1-2.5_Lyt_5R_Truss_e3P0_29Oct\'23.dxf',
            'title': 'Terminal 1 - STRUCTURE Roof Truss (RF)',
            'output': 'STR_RF.svg',
            'bounds': str_bounds
        }
    ]

    print("\n" + "="*80)
    print("EXPORTING ALL TERMINAL 1 DXF FILES TO SVG")
    print("Raw geometry as modeller exported")
    print("="*80)

    for dxf_info in dxf_files:
        dxf_to_svg(
            str(dxf_info['path']),
            str(output_dir / dxf_info['output']),
            dxf_info['title'],
            dxf_info.get('bounds')
        )

    print("\n" + "="*80)
    print(f"✓ All DXF files exported to: {output_dir}")
    print("="*80)

if __name__ == '__main__':
    main()
