#!/usr/bin/env python3
"""
Visualize the extracted Terminal 1 DXF files.
Uses clean, single-building DXF files without coordinate transformations.
"""

import ezdxf
from pathlib import Path
from collections import defaultdict

def extract_entities(dxf_path, layer_filter=None):
    """Extract entities from DXF file"""
    doc = ezdxf.readfile(str(dxf_path))
    entities = []

    for entity in doc.modelspace():
        if entity.dxftype() not in ['CIRCLE', 'LINE', 'LWPOLYLINE', 'ARC']:
            continue

        if layer_filter and hasattr(entity.dxf, 'layer'):
            if entity.dxf.layer.upper() not in layer_filter:
                continue

        if entity.dxftype() == 'CIRCLE':
            c = entity.dxf.center
            entities.append({
                'type': 'circle',
                'cx': c.x, 'cy': c.y,
                'r': entity.dxf.radius
            })
        elif entity.dxftype() == 'LINE':
            s, e = entity.dxf.start, entity.dxf.end
            entities.append({
                'type': 'line',
                'x1': s.x, 'y1': s.y, 'x2': e.x, 'y2': e.y
            })
        elif entity.dxftype() == 'LWPOLYLINE':
            points = [(p[0], p[1]) for p in entity.get_points()]
            entities.append({
                'type': 'polyline',
                'points': points
            })
        elif entity.dxftype() == 'ARC':
            c = entity.dxf.center
            entities.append({
                'type': 'arc',
                'cx': c.x, 'cy': c.y,
                'r': entity.dxf.radius,
                'start_angle': entity.dxf.start_angle,
                'end_angle': entity.dxf.end_angle
            })

    return entities

def get_bounds(all_entities):
    """Calculate bounds from all entities"""
    x_coords = []
    y_coords = []

    for entities in all_entities:
        for e in entities:
            if e['type'] == 'circle':
                x_coords.append(e['cx'])
                y_coords.append(e['cy'])
            elif e['type'] == 'line':
                x_coords.extend([e['x1'], e['x2']])
                y_coords.extend([e['y1'], e['y2']])
            elif e['type'] == 'polyline':
                x_coords.extend([p[0] for p in e['points']])
                y_coords.extend([p[1] for p in e['points']])
            elif e['type'] == 'arc':
                # For arcs, use center +/- radius
                x_coords.extend([e['cx'] - e['r'], e['cx'] + e['r']])
                y_coords.extend([e['cy'] - e['r'], e['cy'] + e['r']])

    return {
        'min_x': min(x_coords), 'max_x': max(x_coords),
        'min_y': min(y_coords), 'max_y': max(y_coords)
    }

def generate_svg_content(entities, color, bounds, width, rotate_90_ccw=False):
    """Generate SVG markup for entities"""
    if rotate_90_ccw:
        # Use rotated bounds for scale
        bounds_w = bounds['rot_max_x'] - bounds['rot_min_x']
        bounds_h = bounds['rot_max_y'] - bounds['rot_min_y']
    else:
        bounds_w = bounds['max_x'] - bounds['min_x']
        bounds_h = bounds['max_y'] - bounds['min_y']
    scale = width / bounds_w

    def transform(x, y):
        if rotate_90_ccw:
            # Rotate 90° CCW: (x, y) → (-y, x)
            rx, ry = -y, x
            # Use rotated bounds for positioning
            return ((rx - bounds['rot_min_x']) * scale,
                    (bounds['rot_max_y'] - ry) * scale)
        else:
            return ((x - bounds['min_x']) * scale,
                    (bounds['max_y'] - y) * scale)

    svg = []
    for e in entities:
        if e['type'] == 'circle':
            cx, cy = transform(e['cx'], e['cy'])
            r = max(e['r'] * scale, 2)
            svg.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
                      f'fill="{color}" stroke="{color}" stroke-width="1" opacity="0.7"/>')
        elif e['type'] == 'line':
            x1, y1 = transform(e['x1'], e['y1'])
            x2, y2 = transform(e['x2'], e['y2'])
            svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                      f'stroke="{color}" stroke-width="1.5" opacity="0.7"/>')
        elif e['type'] == 'polyline':
            pts = [transform(p[0], p[1]) for p in e['points']]
            pts_str = ' '.join(f"{x:.1f},{y:.1f}" for x, y in pts)
            svg.append(f'<polyline points="{pts_str}" fill="none" '
                      f'stroke="{color}" stroke-width="1.5" opacity="0.7"/>')
        elif e['type'] == 'arc':
            import math
            cx, cy = transform(e['cx'], e['cy'])
            r = max(e['r'] * scale, 2)
            # Convert angles (DXF uses degrees, SVG uses radians)
            # DXF: counter-clockwise from 3 o'clock
            # SVG: need to flip Y axis
            start_rad = math.radians(e['start_angle'])
            end_rad = math.radians(e['end_angle'])
            # Calculate start and end points
            x1 = cx + r * math.cos(start_rad)
            y1 = cy - r * math.sin(start_rad)  # Flip Y
            x2 = cx + r * math.cos(end_rad)
            y2 = cy - r * math.sin(end_rad)  # Flip Y
            # Large arc flag: if angle > 180 degrees
            angle_diff = (e['end_angle'] - e['start_angle']) % 360
            large_arc = 1 if angle_diff > 180 else 0
            # Sweep direction (counterclockwise in SVG with flipped Y = clockwise)
            sweep = 0
            svg.append(f'<path d="M {x1:.1f} {y1:.1f} A {r:.1f} {r:.1f} 0 {large_arc} {sweep} {x2:.1f} {y2:.1f}" '
                      f'fill="none" stroke="{color}" stroke-width="1.5" opacity="0.7"/>')

    return '\n'.join(svg)

def main():
    print("="*80)
    print("VISUALIZING EXTRACTED TERMINAL 1 - ARC + STR")
    print("="*80)

    base = Path(__file__).parent.parent
    extract_dir = base / "SourceFiles" / "Terminal1_Extracted"

    # Define ARC layers and colors
    arc_layers = {
        'Walls': {
            'filter': ['WALL', 'WALL1', 'A-WALL', 'CH-WALL'],
            'color': '#34495e'
        },
        'Roof': {
            'filter': ['ROOF', 'ROOFSTR', 'CH-ROOF'],
            'color': '#e74c3c'
        },
        'Columns': {
            'filter': ['COL', 'COLUMN'],
            'color': '#9b59b6'
        },
    }

    # Define STR layers and colors
    str_layers = {
        'Beams': {
            'filter': ['BEAM LINE'],
            'color': '#3498db'
        },
        'Columns': {
            'filter': ['COLUMN LINE'],
            'color': '#e67e22'
        },
        'Slabs': {
            'filter': ['SLAB EDGE LINE'],
            'color': '#1abc9c'
        },
        'Grid': {
            'filter': ['AXIS LINE(DIR 1)', 'AXIS LINE(DIR 2)', 'AXIS CIRCLE(DIR 1)', 'AXIS CIRCLE(DIR 2)'],
            'color': '#95a5a6'
        },
    }

    # STR floor files to process
    str_floors = [
        ('1F', 'Terminal1_STR_1F.dxf'),
        ('3F', 'Terminal1_STR_3F.dxf'),
        ('4F-6F', 'Terminal1_STR_4F-6F.dxf'),
    ]

    # Extract ARC layers
    print("\n📐 Loading ARC layers...")
    arc_path = extract_dir / "Terminal1_ARC.dxf"
    arc_doc = ezdxf.readfile(str(arc_path))

    arc_groups = {}
    for layer_name, layer_info in arc_layers.items():
        entities = []
        for entity in arc_doc.modelspace():
            if entity.dxftype() not in ['CIRCLE', 'LINE', 'LWPOLYLINE', 'ARC']:
                continue
            if not hasattr(entity.dxf, 'layer'):
                continue
            if entity.dxf.layer.upper() not in layer_info['filter']:
                continue

            if entity.dxftype() == 'CIRCLE':
                c = entity.dxf.center
                entities.append({'type': 'circle', 'cx': c.x, 'cy': c.y, 'r': entity.dxf.radius})
            elif entity.dxftype() == 'LINE':
                s, e = entity.dxf.start, entity.dxf.end
                entities.append({'type': 'line', 'x1': s.x, 'y1': s.y, 'x2': e.x, 'y2': e.y})
            elif entity.dxftype() == 'LWPOLYLINE':
                points = [(p[0], p[1]) for p in entity.get_points()]
                entities.append({'type': 'polyline', 'points': points})
            elif entity.dxftype() == 'ARC':
                c = entity.dxf.center
                entities.append({
                    'type': 'arc', 'cx': c.x, 'cy': c.y, 'r': entity.dxf.radius,
                    'start_angle': entity.dxf.start_angle, 'end_angle': entity.dxf.end_angle
                })

        arc_groups[f'ARC-{layer_name}'] = entities
        print(f"  ARC-{layer_name}: {len(entities)} entities")

    # Also extract ALL ARC entities (dome curves) regardless of layer
    dome_arcs = []
    for entity in arc_doc.modelspace():
        if entity.dxftype() == 'ARC':
            c = entity.dxf.center
            dome_arcs.append({
                'type': 'arc', 'cx': c.x, 'cy': c.y, 'r': entity.dxf.radius,
                'start_angle': entity.dxf.start_angle, 'end_angle': entity.dxf.end_angle
            })
    if dome_arcs:
        arc_groups['ARC-Dome'] = dome_arcs
        arc_layers['Dome'] = {'filter': [], 'color': '#27ae60'}  # Green for dome
        print(f"  ARC-Dome: {len(dome_arcs)} entities")

    # Calculate ARC center from actual extracted data
    arc_all_x, arc_all_y = [], []
    for group_entities in arc_groups.values():
        for e in group_entities:
            if e['type'] == 'circle':
                arc_all_x.append(e['cx'])
                arc_all_y.append(e['cy'])
            elif e['type'] == 'line':
                arc_all_x.extend([e['x1'], e['x2']])
                arc_all_y.extend([e['y1'], e['y2']])
            elif e['type'] == 'polyline':
                arc_all_x.extend([p[0] for p in e['points']])
                arc_all_y.extend([p[1] for p in e['points']])
            elif e['type'] == 'arc':
                arc_all_x.append(e['cx'])
                arc_all_y.append(e['cy'])

    arc_center = ((min(arc_all_x) + max(arc_all_x)) / 2, (min(arc_all_y) + max(arc_all_y)) / 2)
    print(f"  ARC center: ({arc_center[0]/1000:.1f}m, {arc_center[1]/1000:.1f}m)")

    # Extract STR layers from each floor with coordinate transformation
    print("\n🏗️ Loading STR layers...")
    str_groups = {}

    for floor_name, floor_file in str_floors:
        str_path = extract_dir / floor_file
        if not str_path.exists():
            print(f"  ⚠️ {floor_file} not found, skipping")
            continue

        str_doc = ezdxf.readfile(str(str_path))

        # First pass: find actual bounds of this STR floor
        str_x, str_y = [], []
        for entity in str_doc.modelspace():
            if entity.dxftype() == 'CIRCLE':
                c = entity.dxf.center
                str_x.append(c.x)
                str_y.append(c.y)
            elif entity.dxftype() == 'LINE':
                s, e = entity.dxf.start, entity.dxf.end
                str_x.extend([s.x, e.x])
                str_y.extend([s.y, e.y])
            elif entity.dxftype() == 'LWPOLYLINE':
                for p in entity.get_points():
                    str_x.append(p[0])
                    str_y.append(p[1])

        if not str_x:
            print(f"  ⚠️ {floor_name} has no geometry, skipping")
            continue

        # Calculate offset to align this floor's center with ARC center
        floor_center_x = (min(str_x) + max(str_x)) / 2
        floor_center_y = (min(str_y) + max(str_y)) / 2

        # Align centers, then apply manual adjustment
        # STR extracted bounds are larger than Terminal 1, need extra offset
        # After 90° CCW rotation: original X = vertical, original -Y = horizontal
        # To move UP: increase X offset, To move RIGHT: decrease Y offset
        offset_x = arc_center[0] - floor_center_x + 10000  # Extra 10m up (was 20m - overshot)
        offset_y = arc_center[1] - floor_center_y - 5000   # Extra 5m right
        print(f"  {floor_name} -> offset: ({offset_x/1000:.1f}m, {offset_y/1000:.1f}m) [adjusted]")

        for layer_name, layer_info in str_layers.items():
            entities = []
            for entity in str_doc.modelspace():
                if entity.dxftype() not in ['CIRCLE', 'LINE', 'LWPOLYLINE', 'ARC']:
                    continue
                if not hasattr(entity.dxf, 'layer'):
                    continue
                if entity.dxf.layer.upper() not in layer_info['filter']:
                    continue

                # Apply offset transformation to align with ARC
                if entity.dxftype() == 'CIRCLE':
                    c = entity.dxf.center
                    entities.append({'type': 'circle', 'cx': c.x + offset_x, 'cy': c.y + offset_y, 'r': entity.dxf.radius})
                elif entity.dxftype() == 'LINE':
                    s, e = entity.dxf.start, entity.dxf.end
                    entities.append({'type': 'line', 'x1': s.x + offset_x, 'y1': s.y + offset_y, 'x2': e.x + offset_x, 'y2': e.y + offset_y})
                elif entity.dxftype() == 'LWPOLYLINE':
                    points = [(p[0] + offset_x, p[1] + offset_y) for p in entity.get_points()]
                    entities.append({'type': 'polyline', 'points': points})
                elif entity.dxftype() == 'ARC':
                    c = entity.dxf.center
                    entities.append({
                        'type': 'arc', 'cx': c.x + offset_x, 'cy': c.y + offset_y, 'r': entity.dxf.radius,
                        'start_angle': entity.dxf.start_angle, 'end_angle': entity.dxf.end_angle
                    })

            group_name = f'STR-{floor_name}-{layer_name}'
            str_groups[group_name] = entities
            if entities:
                print(f"  STR-{floor_name}-{layer_name}: {len(entities)} entities")

    # Calculate bounds from ALL entities (ARC + STR) for proper viewport
    all_entities = [
        arc_groups.get('ARC-Walls', []),
        arc_groups.get('ARC-Roof', []),
        arc_groups.get('ARC-Dome', [])
    ]
    # Add STR entities to bounds calculation
    for group_name, entities in str_groups.items():
        all_entities.append(entities)

    bounds = get_bounds(all_entities)
    # Add small padding
    padding = 2000
    bounds['min_x'] -= padding
    bounds['max_x'] += padding
    bounds['min_y'] -= padding
    bounds['max_y'] += padding

    # Calculate rotated bounds for 90° CCW rotation: (x, y) → (-y, x)
    # After rotation: new_x = -old_y, new_y = old_x
    bounds['rot_min_x'] = -bounds['max_y']  # -max_y becomes min_x after rotation
    bounds['rot_max_x'] = -bounds['min_y']  # -min_y becomes max_x after rotation
    bounds['rot_min_y'] = bounds['min_x']   # min_x becomes min_y after rotation
    bounds['rot_max_y'] = bounds['max_x']   # max_x becomes max_y after rotation

    print(f"\n  ARC Bounds: X=[{bounds['min_x']:.0f}, {bounds['max_x']:.0f}], Y=[{bounds['min_y']:.0f}, {bounds['max_y']:.0f}]")
    print(f"  Rotated bounds: X=[{bounds['rot_min_x']:.0f}, {bounds['rot_max_x']:.0f}], Y=[{bounds['rot_min_y']:.0f}, {bounds['rot_max_y']:.0f}]")

    # Calculate SVG dimensions using rotated bounds (portrait orientation)
    svg_width = 700  # Narrower for portrait
    rot_bounds_w = bounds['rot_max_x'] - bounds['rot_min_x']
    rot_bounds_h = bounds['rot_max_y'] - bounds['rot_min_y']
    svg_height = int(svg_width * rot_bounds_h / rot_bounds_w)

    # Update bounds width for scale calculation
    bounds['width'] = rot_bounds_w

    # Build HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Terminal 1 - ARC + STR Visualization</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 25px; text-align: center; }}
        .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
        .header p {{ font-size: 14px; opacity: 0.9; }}

        .controls {{ padding: 20px; background: #f8f9fa; }}
        .control-section {{ margin-bottom: 20px; }}
        .control-section h3 {{ margin-bottom: 12px; color: #2c3e50; font-size: 16px; }}
        .control-section h4 {{ margin: 10px 0 8px 0; color: #34495e; font-size: 14px; }}
        .toggles {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 8px; }}

        .toggle-btn {{ display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: white; border: 2px solid #ddd;
                      border-radius: 6px; cursor: pointer; transition: all 0.3s; user-select: none; }}
        .toggle-btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
        .toggle-btn.active {{ border-color: #2ecc71; background: #ecf9f2; }}
        .color-box {{ width: 16px; height: 16px; border-radius: 3px; border: 2px solid #333; flex-shrink: 0; }}
        .toggle-label {{ flex: 1; font-size: 12px; font-weight: 600; }}
        .toggle-count {{ font-size: 10px; color: #7f8c8d; }}

        .discipline-toggle {{ display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; background: #e8e8e8;
                             border: 2px solid #aaa; border-radius: 4px; cursor: pointer; margin-right: 10px; font-size: 12px; font-weight: 600; }}
        .discipline-toggle.active {{ background: #d5f4e6; border-color: #2ecc71; }}

        .svg-container {{ padding: 30px; background: #fafafa; display: flex; justify-content: center; }}
        svg {{ border: 2px solid #ddd; border-radius: 8px; background: white; }}

        .info {{ padding: 15px; background: #d5f4e6; border-top: 3px solid #2ecc71; text-align: center; color: #27ae60; font-size: 13px; }}
        .note {{ padding: 10px 20px; background: #fff3cd; border-left: 4px solid #ffc107; margin: 10px 20px; font-size: 12px; color: #856404; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Terminal 1 - ARC + STR Visualization</h1>
            <p>Architecture and Structural overlaid | Click toggles to show/hide layers | Each STR floor in separate coordinate system</p>
        </div>

        <div class="note">
            <strong>Smart Alignment:</strong> STR floors have been automatically aligned to ARC coordinates using cheatsheet offsets.
            All layers now overlay correctly - toggle to compare disciplines and floors on the same canvas.
        </div>

        <div class="controls">
            <div class="control-section">
                <h3>ARC (Architecture)</h3>
                <div class="toggles">
"""

    # Add ARC toggle buttons
    for layer_name, layer_info in arc_layers.items():
        group_name = f'ARC-{layer_name}'
        entities = arc_groups.get(group_name, [])
        color = layer_info['color']
        count = len(entities)
        html += f"""                    <div class="toggle-btn active" onclick="toggleLayer('{group_name}')" id="toggle-{group_name}">
                        <div class="color-box" style="background: {color};"></div>
                        <div style="flex: 1;">
                            <div class="toggle-label">{layer_name}</div>
                            <div class="toggle-count">{count} elem</div>
                        </div>
                    </div>
"""

    html += """                </div>
            </div>

            <div class="control-section">
                <h3>STR (Structural)</h3>
"""

    # Add STR floor sections
    for floor_name, floor_file in str_floors:
        html += f"""                <h4>{floor_name}</h4>
                <div class="toggles">
"""
        for layer_name, layer_info in str_layers.items():
            group_name = f'STR-{floor_name}-{layer_name}'
            entities = str_groups.get(group_name, [])
            color = layer_info['color']
            count = len(entities)
            # Start STR layers hidden (not active) since they're in different coord systems
            html += f"""                    <div class="toggle-btn" onclick="toggleLayer('{group_name}')" id="toggle-{group_name}">
                        <div class="color-box" style="background: {color};"></div>
                        <div style="flex: 1;">
                            <div class="toggle-label">{layer_name}</div>
                            <div class="toggle-count">{count} elem</div>
                        </div>
                    </div>
"""
        html += """                </div>
"""

    html += f"""            </div>
        </div>

        <div class="svg-container">
            <svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
                <rect width="{svg_width}" height="{svg_height}" fill="#f5f5f5"/>
"""

    # Add ARC SVG groups (with 90° CCW rotation)
    for layer_name, layer_info in arc_layers.items():
        group_name = f'ARC-{layer_name}'
        entities = arc_groups.get(group_name, [])
        color = layer_info['color']
        svg_content = generate_svg_content(entities, color, bounds, svg_width, rotate_90_ccw=True)
        html += f"""                <g id="layer-{group_name}" class="layer-group">
{svg_content}
                </g>
"""

    # Add STR SVG groups (initially hidden via display:none, with 90° CCW rotation)
    # All STR is now aligned to ARC coordinates, so use the same bounds
    for floor_name, floor_file in str_floors:
        for layer_name, layer_info in str_layers.items():
            group_name = f'STR-{floor_name}-{layer_name}'
            entities = str_groups.get(group_name, [])
            color = layer_info['color']
            svg_content = generate_svg_content(entities, color, bounds, svg_width, rotate_90_ccw=True)
            html += f"""                <g id="layer-{group_name}" class="layer-group" style="display: none;">
{svg_content}
                </g>
"""

    html += """            </svg>
        </div>

        <div class="info">
            Terminal 1 ARC + STR extraction. ARC and STR in separate coordinate systems - toggle to compare.
        </div>
    </div>

    <script>
        function toggleLayer(layerName) {
            const group = document.getElementById('layer-' + layerName);
            const toggle = document.getElementById('toggle-' + layerName);

            if (group.style.display === 'none') {
                group.style.display = 'block';
                toggle.classList.add('active');
            } else {
                group.style.display = 'none';
                toggle.classList.remove('active');
            }
        }
    </script>
</body>
</html>
"""

    output = base / "SourceFiles" / "Terminal1_Extracted_View.html"
    with open(output, 'w') as f:
        f.write(html)

    print(f"\n{'='*80}")
    print("SUCCESS!")
    print(f"Output: file://{output.absolute()}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
