#!/usr/bin/env python3
"""
Simple DXF to SVG/HTML Visualizer for Clean Centered DXFs
==========================================================

For DXFs already centered at origin (0, 0) with meter coordinates.
No coordinate transforms, no alignment offsets needed.

Usage:
    python3 visualize_clean_dxf.py
"""

import ezdxf
from pathlib import Path

def extract_entities(dxf_path):
    """Extract entities from DXF file"""
    doc = ezdxf.readfile(str(dxf_path))
    entities = []

    for entity in doc.modelspace():
        if entity.dxftype() not in ['CIRCLE', 'LINE', 'LWPOLYLINE', 'ARC']:
            continue

        layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else '0'

        if entity.dxftype() == 'CIRCLE':
            c = entity.dxf.center
            entities.append({
                'type': 'circle',
                'cx': c.x, 'cy': c.y,
                'r': entity.dxf.radius,
                'layer': layer
            })
        elif entity.dxftype() == 'LINE':
            s, e = entity.dxf.start, entity.dxf.end
            entities.append({
                'type': 'line',
                'x1': s.x, 'y1': s.y,
                'x2': e.x, 'y2': e.y,
                'layer': layer
            })
        elif entity.dxftype() == 'LWPOLYLINE':
            points = [(p[0], p[1]) for p in entity.get_points()]
            entities.append({
                'type': 'polyline',
                'points': points,
                'layer': layer
            })
        elif entity.dxftype() == 'ARC':
            c = entity.dxf.center
            entities.append({
                'type': 'arc',
                'cx': c.x, 'cy': c.y,
                'r': entity.dxf.radius,
                'start_angle': entity.dxf.start_angle,
                'end_angle': entity.dxf.end_angle,
                'layer': layer
            })

    return entities


def get_bounds(all_entities):
    """Calculate bounds from all entities"""
    x_coords = []
    y_coords = []

    for e in all_entities:
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
            x_coords.extend([e['cx'] - e['r'], e['cx'] + e['r']])
            y_coords.extend([e['cy'] - e['r'], e['cy'] + e['r']])

    return {
        'min_x': min(x_coords), 'max_x': max(x_coords),
        'min_y': min(y_coords), 'max_y': max(y_coords)
    }


def generate_svg_content(entities, color, bounds, svg_width):
    """Generate SVG markup for entities"""
    bounds_w = bounds['max_x'] - bounds['min_x']
    bounds_h = bounds['max_y'] - bounds['min_y']
    scale = svg_width / bounds_w

    def transform(x, y):
        # SVG Y-axis is inverted
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
                      f'stroke="{color}" stroke-width="2" opacity="0.8"/>')
        elif e['type'] == 'polyline':
            pts = [transform(p[0], p[1]) for p in e['points']]
            pts_str = ' '.join(f"{x:.1f},{y:.1f}" for x, y in pts)
            svg.append(f'<polyline points="{pts_str}" fill="none" '
                      f'stroke="{color}" stroke-width="2" opacity="0.8"/>')

    return '\n'.join(svg)


def main():
    print("="*80)
    print("CLEAN DXF VISUALIZER - Centered Coordinates")
    print("="*80)

    base = Path(__file__).parent.parent
    extract_dir = base / "SourceFiles" / "Terminal1_Extracted"

    # Layer groups and colors
    layer_config = {
        'ARC': {
            'file': 'Terminal1_ARC.dxf',
            'layers': {
                'Walls': {'filter': ['WALL'], 'color': '#34495e'},
                'Curtain Walls': {'filter': ['CURTAIN_WALL_E', 'CURTAIN_WALL_W'], 'color': '#3498db'},
                'Partitions': {'filter': ['PARTITION_WALL'], 'color': '#95a5a6'},
                'Canopy': {'filter': ['ENTRANCE_CANOPY'], 'color': '#e67e22'},
                'Gates': {'filter': ['BOARDING_GATE'], 'color': '#16a085'},
                'Counters': {'filter': ['COUNTER'], 'color': '#8e44ad'},
                'Kiosks': {'filter': ['RETAIL_KIOSK'], 'color': '#27ae60'},
                'Fixtures': {'filter': ['FIXTURE'], 'color': '#95a5a6'},
                'Seating': {'filter': ['SEATING'], 'color': '#e74c3c'},
            }
        },
        'STR': {
            'files': ['Terminal1_STR_1F.dxf', 'Terminal1_STR_3F.dxf', 'Terminal1_STR_4F-6F.dxf'],
            'layers': {
                'Beams': {'filter': ['BEAM LINE'], 'color': '#3498db'},
                'Columns': {'filter': ['COLUMN LINE'], 'color': '#e67e22'},
            }
        }
    }

    # Extract ARC entities
    print("\n📐 Loading ARC...")
    arc_path = extract_dir / layer_config['ARC']['file']
    all_arc_entities = extract_entities(arc_path)

    arc_groups = {}
    for layer_name, layer_info in layer_config['ARC']['layers'].items():
        entities = [e for e in all_arc_entities if e['layer'] in layer_info['filter']]
        arc_groups[f'ARC-{layer_name}'] = entities
        print(f"  {layer_name}: {len(entities)} entities")

    # Extract STR entities
    print("\n🏗️ Loading STR...")
    str_groups = {}
    for str_file in layer_config['STR']['files']:
        floor_name = str_file.replace('Terminal1_STR_', '').replace('.dxf', '')
        str_path = extract_dir / str_file
        all_str_entities = extract_entities(str_path)

        for layer_name, layer_info in layer_config['STR']['layers'].items():
            entities = [e for e in all_str_entities if e['layer'] in layer_info['filter']]
            str_groups[f'STR-{floor_name}-{layer_name}'] = entities
            if entities:
                print(f"  {floor_name} {layer_name}: {len(entities)} entities")

    # Calculate bounds from ARC only (STR should match)
    bounds = get_bounds(all_arc_entities)
    padding = 2.0  # meters
    bounds['min_x'] -= padding
    bounds['max_x'] += padding
    bounds['min_y'] -= padding
    bounds['max_y'] += padding

    print(f"\n  Bounds: X=[{bounds['min_x']:.1f}, {bounds['max_x']:.1f}]m, "
          f"Y=[{bounds['min_y']:.1f}, {bounds['max_y']:.1f}]m")

    # Calculate SVG dimensions
    svg_width = 800
    bounds_w = bounds['max_x'] - bounds['min_x']
    bounds_h = bounds['max_y'] - bounds['min_y']
    svg_height = int(svg_width * bounds_h / bounds_w)

    # Build HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Ferry Terminal - Clean DXF View</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: #2c3e50; overflow: hidden; }}
        .container {{ width: 100vw; height: 100vh; display: flex; flex-direction: column; }}
        .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ font-size: 18px; margin: 0; }}
        .header p {{ font-size: 11px; opacity: 0.9; margin: 0; }}

        .workspace {{ display: grid; grid-template-columns: 320px 1fr; flex: 1; overflow: hidden; }}

        .left-panel {{ background: #f8f9fa; padding: 15px; overflow-y: auto; border-right: 2px solid #ddd; }}

        .configurator {{ background: white; padding: 15px; border-radius: 8px; border: 2px solid #3498db; margin-bottom: 15px; }}
        .configurator h3 {{ margin: 0 0 15px 0; color: #2c3e50; font-size: 14px; font-weight: 700; }}
        .config-group {{ margin-bottom: 12px; }}
        .config-label {{ display: block; margin-bottom: 5px; color: #34495e; font-size: 11px; font-weight: 600; }}
        .config-input {{ width: 100%; padding: 6px; border: 2px solid #ddd; border-radius: 4px; font-size: 12px; }}
        .floor-list {{ list-style: none; padding: 0; }}
        .floor-item {{ padding: 8px; margin-bottom: 5px; background: #f8f9fa; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }}
        .floor-item.active {{ background: #d5f4e6; border-left: 3px solid #2ecc71; }}
        .floor-name {{ font-size: 12px; font-weight: 600; }}

        .layer-controls {{ background: white; padding: 15px; border-radius: 8px; border: 2px solid #9b59b6; }}
        .control-section {{ margin-bottom: 12px; }}
        .control-section h3 {{ margin: 0 0 10px 0; color: #2c3e50; font-size: 13px; font-weight: 700; }}
        .control-section h4 {{ margin: 10px 0 8px 0; color: #34495e; font-size: 11px; font-weight: 600; padding-left: 8px; border-left: 3px solid #3498db; }}
        .toggles {{ display: flex; flex-direction: column; gap: 6px; }}

        .toggle-btn {{ display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: white; border: 2px solid #ddd;
                      border-radius: 4px; cursor: pointer; transition: all 0.2s; }}
        .toggle-btn:hover {{ transform: translateX(3px); box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .toggle-btn.active {{ border-color: #2ecc71; background: #ecf9f2; }}
        .color-box {{ width: 14px; height: 14px; border-radius: 3px; border: 2px solid #333; }}
        .toggle-label {{ flex: 1; font-size: 11px; font-weight: 600; }}

        .canvas-area {{ background: #34495e; display: flex; align-items: center; justify-content: center; position: relative; overflow: auto; }}
        .canvas-container {{ background: white; box-shadow: 0 0 20px rgba(0,0,0,0.5); }}
        svg {{ display: block; }}

        .footer {{ background: #1e3c72; color: white; padding: 8px 20px; text-align: center; font-size: 11px; opacity: 0.9; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🌳 Mini Bonsai Tree - DXF Mode</h1>
                <p>Interactive Building Configurator</p>
            </div>
            <div style="text-align: right;">
                <h1 style="font-size: 14px;">Ferry Terminal</h1>
                <p>45m × 66m | 2,970m² | 3 Levels</p>
            </div>
        </div>

        <div class="workspace">
            <div class="left-panel">
                <div class="configurator">
                <h3>🌳 Mini Bonsai Tree - Configurator</h3>

                <div class="config-group">
                    <label class="config-label">Facility Type</label>
                    <select class="config-input" id="facilityType">
                        <option selected>Ferry Terminal</option>
                        <option>Airport Terminal</option>
                        <option>Shopping Mall</option>
                        <option>Office Building</option>
                        <option>Train Station</option>
                        <option>Bus Terminal</option>
                    </select>
                </div>

                <div class="config-group">
                    <label class="config-label">Land Area (m²)</label>
                    <input type="number" class="config-input" value="2970" min="500" id="landArea" placeholder="Width × Depth">
                    <small style="color: #7f8c8d; font-size: 11px;">Current: 45m × 66m = 2,970m²</small>
                </div>

                <div class="config-group">
                    <label class="config-label">Number of Levels</label>
                    <input type="number" class="config-input" value="3" min="1" max="10" id="numLevels">
                </div>

                <div class="config-group">
                    <label class="config-label">Capacity (pax/day)</label>
                    <input type="number" class="config-input" value="2000" min="100" step="100" id="capacity">
                </div>

                <div class="config-group">
                    <label class="config-label">Budget (USD)</label>
                    <input type="number" class="config-input" value="5000000" min="100000" step="100000" id="budget" placeholder="$5M">
                    <small style="color: #7f8c8d; font-size: 11px;">5D BIM - design driven by budget</small>
                </div>

                <hr style="border: none; border-top: 1px solid #ddd; margin: 15px 0;">

                <div class="config-group">
                    <label class="config-label">Floor Selector (View)</label>
                    <select class="config-input" id="floorSelector" onchange="selectFloor(this.value)">
                        <option value="1F">1F (Ground)</option>
                        <option value="3F">3F (Mid)</option>
                        <option value="4F-6F">4F-6F (Upper)</option>
                    </select>
                </div>

                <div class="config-group">
                    <button class="config-input" style="background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%); color: white; font-weight: 700; cursor: pointer; border: none;" onclick="generateBuilding()">
                        🏗️ Generate Building
                    </button>
                    <button class="config-input" style="background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); color: white; font-weight: 600; cursor: pointer; border: none; margin-top: 8px;" onclick="exportDXF()">
                        📥 Export DXF Set
                    </button>
                </div>
                </div>

                <div class="layer-controls">
                    <div class="control-section">
                        <h3>ARC Layers</h3>
                    <div class="toggles">
"""

    # Add ARC toggle buttons
    for layer_name, layer_info in layer_config['ARC']['layers'].items():
        group_name = f'ARC-{layer_name}'
        entities = arc_groups.get(group_name, [])
        color = layer_info['color']
        count = len(entities)
        html += f"""                    <div class="toggle-btn active" onclick="toggleLayer('{group_name}')" id="toggle-{group_name}">
                        <div class="color-box" style="background: {color};"></div>
                        <div class="toggle-label">{layer_name} ({count})</div>
                    </div>
"""

    html += """                </div>
            </div>

            <div class="control-section">
                <h3>STR (Structural) - Select Floor</h3>
"""

    # Add STR toggle buttons organized by floor
    for str_file in layer_config['STR']['files']:
        floor_name = str_file.replace('Terminal1_STR_', '').replace('.dxf', '')

        html += f"""                <h4>{floor_name}</h4>
                <div class="toggles">
"""

        for layer_name, layer_info in layer_config['STR']['layers'].items():
            group_name = f'STR-{floor_name}-{layer_name}'
            entities = str_groups.get(group_name, [])
            color = layer_info['color']
            count = len(entities)
            html += f"""                    <div class="toggle-btn" onclick="toggleLayer('{group_name}')" id="toggle-{group_name}">
                        <div class="color-box" style="background: {color};"></div>
                        <div class="toggle-label">{layer_name} ({count})</div>
                    </div>
"""

        html += """                    </div>
"""

    html += f"""                </div>
                </div>
            </div>

            <div class="canvas-area">
                <div class="canvas-container">
                    <svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
                        <rect width="{svg_width}" height="{svg_height}" fill="#f5f5f5"/>
"""

    # Add ARC SVG groups
    for layer_name, layer_info in layer_config['ARC']['layers'].items():
        group_name = f'ARC-{layer_name}'
        entities = arc_groups.get(group_name, [])
        color = layer_info['color']
        svg_content = generate_svg_content(entities, color, bounds, svg_width)
        html += f"""                <g id="layer-{group_name}" class="layer-group">
{svg_content}
                </g>
"""

    # Add STR SVG groups (initially hidden)
    for str_file in layer_config['STR']['files']:
        floor_name = str_file.replace('Terminal1_STR_', '').replace('.dxf', '')
        for layer_name, layer_info in layer_config['STR']['layers'].items():
            group_name = f'STR-{floor_name}-{layer_name}'
            entities = str_groups.get(group_name, [])
            color = layer_info['color']
            svg_content = generate_svg_content(entities, color, bounds, svg_width)
            html += f"""                <g id="layer-{group_name}" class="layer-group" style="display: none;">
{svg_content}
                </g>
"""

    html += """                </svg>
                </div>
            </div>
        </div>

        <div class="footer">
            Drag & Drop Editor | Canvas: origin (0,0) | Press F11 for fullscreen
        </div>
    </div>

    <script>
        let selectedGroup = null;
        let isDragging = false;
        let startX, startY;
        let currentTransform = { x: 0, y: 0 };
        let currentFloor = '1F';

        // Generative BIM - Generate Building
        function generateBuilding() {
            const config = {
                facilityType: document.getElementById('facilityType').value,
                landArea: parseInt(document.getElementById('landArea').value),
                numLevels: parseInt(document.getElementById('numLevels').value),
                capacity: parseInt(document.getElementById('capacity').value),
                budget: parseInt(document.getElementById('budget').value)
            };

            console.log('🏗️ GENERATIVE BIM - Building Parameters:');
            console.log(`  Facility: ${config.facilityType}`);
            console.log(`  Land Area: ${config.landArea.toLocaleString()}m²`);
            console.log(`  Levels: ${config.numLevels}`);
            console.log(`  Capacity: ${config.capacity.toLocaleString()} pax/day`);
            console.log(`  Budget: $${(config.budget / 1000000).toFixed(1)}M USD`);
            console.log('');
            console.log('📊 Calculating optimized layout...');
            console.log('⚙️ Generating structural grid...');
            console.log('🎨 Placing architectural elements...');
            console.log('🔧 Routing MEP systems...');
            console.log('💰 Optimizing for budget constraint...');
            console.log('');
            console.log('✅ Generation would happen here!');
            console.log('   → This would call Python backend to regenerate DXFs');
            console.log('   → Then reload this visualization with new building');

            alert(`🌳 Mini Bonsai Tree - Generative BIM\\n\\nBuilding configured!\\n\\nFacility: ${config.facilityType}\\nArea: ${config.landArea.toLocaleString()}m²\\nLevels: ${config.numLevels}\\nCapacity: ${config.capacity.toLocaleString()} pax/day\\nBudget: $${(config.budget / 1000000).toFixed(1)}M\\n\\n(Full generation coming soon!)`);
        }

        // Export DXF Set
        function exportDXF() {
            console.log('📥 Exporting DXF set...');
            console.log('  → Terminal1_ARC.dxf');
            console.log('  → Terminal1_STR_1F.dxf');
            console.log('  → Terminal1_STR_3F.dxf');
            console.log('  → Terminal1_STR_4F-6F.dxf');
            alert('📥 DXF Export\\n\\nDXF files are already generated!\\nLocation: SourceFiles/Terminal1_Extracted/\\n\\n(Web download coming soon)');
        }

        // Floor selector functionality
        function selectFloor(floorId) {
            currentFloor = floorId;

            // Hide all STR layers
            const allStrLayers = document.querySelectorAll('[id^="layer-STR-"]');
            allStrLayers.forEach(layer => {
                layer.style.display = 'none';
            });

            // Deactivate all STR toggles
            const allStrToggles = document.querySelectorAll('[id^="toggle-STR-"]');
            allStrToggles.forEach(toggle => {
                toggle.classList.remove('active');
            });

            // Show selected floor's layers
            const floorLayers = document.querySelectorAll(`[id^="layer-STR-${floorId}-"]`);
            floorLayers.forEach(layer => {
                layer.style.display = 'block';
            });

            // Activate selected floor's toggles
            const floorToggles = document.querySelectorAll(`[id^="toggle-STR-${floorId}-"]`);
            floorToggles.forEach(toggle => {
                toggle.classList.add('active');
            });

            console.log(`Floor selected: ${floorId}`);
        }

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

        // Drag and Drop functionality
        const svg = document.querySelector('svg');
        const layerGroups = document.querySelectorAll('.layer-group');

        layerGroups.forEach(group => {
            group.style.cursor = 'move';

            group.addEventListener('mousedown', (e) => {
                if (group.style.display === 'none') return;

                isDragging = true;
                selectedGroup = group;

                const transform = group.getAttribute('transform') || 'translate(0,0)';
                const match = transform.match(/translate\\(([^,]+),([^)]+)\\)/);
                if (match) {
                    currentTransform.x = parseFloat(match[1]);
                    currentTransform.y = parseFloat(match[2]);
                }

                const pt = svg.createSVGPoint();
                pt.x = e.clientX;
                pt.y = e.clientY;
                const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

                startX = svgP.x - currentTransform.x;
                startY = svgP.y - currentTransform.y;

                e.preventDefault();
            });
        });

        svg.addEventListener('mousemove', (e) => {
            if (!isDragging || !selectedGroup) return;

            const pt = svg.createSVGPoint();
            pt.x = e.clientX;
            pt.y = e.clientY;
            const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

            const newX = svgP.x - startX;
            const newY = svgP.y - startY;

            selectedGroup.setAttribute('transform', `translate(${newX},${newY})`);
            currentTransform.x = newX;
            currentTransform.y = newY;
        });

        svg.addEventListener('mouseup', () => {
            if (isDragging && selectedGroup) {
                console.log(`Layer moved: ${selectedGroup.id}, offset: (${currentTransform.x.toFixed(2)}, ${currentTransform.y.toFixed(2)})`);
            }
            isDragging = false;
            selectedGroup = null;
        });

        svg.addEventListener('mouseleave', () => {
            isDragging = false;
            selectedGroup = null;
        });

        // Double-click to reset position
        layerGroups.forEach(group => {
            group.addEventListener('dblclick', () => {
                group.setAttribute('transform', 'translate(0,0)');
                currentTransform = { x: 0, y: 0 };
                console.log(`Layer reset: ${group.id}`);
            });
        });
    </script>
</body>
</html>
"""

    output = base / "SourceFiles" / "Terminal1_Clean_View.html"
    with open(output, 'w') as f:
        f.write(html)

    print(f"\n{'='*80}")
    print("SUCCESS!")
    print(f"Output: file://{output.absolute()}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
