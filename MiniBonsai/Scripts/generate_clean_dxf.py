#!/usr/bin/env python3
"""
Generate Clean DXF Files for POC
================================

Reverse workflow: Generate DXF files that conform to our placement system.
This creates the "source of truth" DXF files with:
- NO slabs (only programmatic slabs)
- Clean, non-overlapping geometry
- Proper layering and element types

Usage:
    python3 generate_clean_dxf.py

Output:
    SourceFiles/Terminal1_Extracted/Terminal1_ARC_clean.dxf
    SourceFiles/Terminal1_Extracted/Terminal1_STR_1F_clean.dxf
    SourceFiles/Terminal1_Extracted/Terminal1_STR_3F_clean.dxf
    SourceFiles/Terminal1_Extracted/Terminal1_STR_4F-6F_clean.dxf
"""

import ezdxf
from pathlib import Path
import json

BASE_DIR = Path(__file__).parent.parent
CHEATSHEET_FILE = BASE_DIR / "terminal1_cheatsheet.json"
OUTPUT_DIR = BASE_DIR / "SourceFiles" / "Terminal1_Extracted"
TEMPLATES_FILE = BASE_DIR / "arc_str_element_templates.json"

# Load building configuration
with open(BASE_DIR / "building_config.json") as f:
    building_config = json.load(f)

with open(TEMPLATES_FILE) as f:
    templates = json.load(f)

# Floor elevations
floor_elevations = templates.get('floor_elevations_m', {
    '1F': 0.0, '3F': 8.0, '4F-6F': 12.0
})

def create_clean_arc_dxf():
    """
    Generate clean ARC DXF - Ferry Terminal with proper elevations

    Layout:
    - FRONT (South): Landside entrance with canopy
    - BACK (North): Waterside jetty connection
    - SIDES (East/West): Glass curtain walls with circulation
    - CENTER: Open atrium with ceiling fans
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    # Terminal dimensions
    width = 45.0  # East-West
    depth = 66.0  # North-South (landside to waterside)
    wall_thickness = 0.3

    # ========================================================================
    # FRONT ELEVATION (South - Landside Entrance)
    # ========================================================================
    # Main entrance wall with large opening
    entrance_width = 12.0
    entrance_offset = 0  # Center

    # West section of front wall
    msp.add_line(
        (-width/2, -depth/2),
        (entrance_offset - entrance_width/2, -depth/2),
        dxfattribs={'layer': 'WALL'}
    )
    msp.add_line(
        (-width/2, -depth/2 + wall_thickness),
        (entrance_offset - entrance_width/2, -depth/2 + wall_thickness),
        dxfattribs={'layer': 'WALL'}
    )

    # East section of front wall
    msp.add_line(
        (entrance_offset + entrance_width/2, -depth/2),
        (width/2, -depth/2),
        dxfattribs={'layer': 'WALL'}
    )
    msp.add_line(
        (entrance_offset + entrance_width/2, -depth/2 + wall_thickness),
        (width/2, -depth/2 + wall_thickness),
        dxfattribs={'layer': 'WALL'}
    )

    # Entrance canopy (extends 4m forward)
    canopy_depth = 4.0
    canopy_y = -depth/2 - canopy_depth
    msp.add_lwpolyline([
        (entrance_offset - entrance_width/2 - 2, -depth/2),
        (entrance_offset - entrance_width/2 - 2, canopy_y),
        (entrance_offset + entrance_width/2 + 2, canopy_y),
        (entrance_offset + entrance_width/2 + 2, -depth/2),
    ], dxfattribs={'layer': 'ENTRANCE_CANOPY'})

    # ========================================================================
    # BACK ELEVATION (North - Waterside Jetty)
    # ========================================================================
    # Jetty connection - full width glass with boarding gates
    gate_width = 8.0
    num_gates = 4
    gate_spacing = width / num_gates

    for i in range(num_gates):
        gate_x = -width/2 + i * gate_spacing + gate_spacing/2
        # Gate frame
        msp.add_lwpolyline([
            (gate_x - gate_width/2, depth/2),
            (gate_x - gate_width/2, depth/2 + 3.0),  # Extends to jetty
            (gate_x + gate_width/2, depth/2 + 3.0),
            (gate_x + gate_width/2, depth/2),
        ], dxfattribs={'layer': 'BOARDING_GATE'})

    # Back wall (solid sections between gates)
    for i in range(num_gates + 1):
        if i == 0:
            x1 = -width/2
            x2 = -width/2 + gate_spacing/2 - gate_width/2
        elif i == num_gates:
            x1 = -width/2 + (num_gates - 0.5) * gate_spacing + gate_width/2
            x2 = width/2
        else:
            x1 = -width/2 + (i - 0.5) * gate_spacing + gate_width/2
            x2 = -width/2 + (i + 0.5) * gate_spacing - gate_width/2

        if x2 > x1:
            msp.add_line((x1, depth/2), (x2, depth/2), dxfattribs={'layer': 'WALL'})
            msp.add_line((x1, depth/2 - wall_thickness), (x2, depth/2 - wall_thickness), dxfattribs={'layer': 'WALL'})

    # ========================================================================
    # SIDE ELEVATIONS (East/West - Glass Curtain Walls)
    # ========================================================================
    panel_width = 1.5
    num_panels = int(depth / panel_width)

    for i in range(num_panels):
        y = -depth/2 + i * panel_width

        # East facade (curtain wall)
        msp.add_lwpolyline([
            (width/2 - 0.05, y),
            (width/2 - 0.05, y + panel_width),
        ], dxfattribs={'layer': 'CURTAIN_WALL_E'})

        # West facade (curtain wall)
        msp.add_lwpolyline([
            (-width/2 + 0.05, y),
            (-width/2 + 0.05, y + panel_width),
        ], dxfattribs={'layer': 'CURTAIN_WALL_W'})

    # ========================================================================
    # INTERIOR PARTITIONS
    # ========================================================================
    # Restroom blocks (corners) with detailed stalls
    restroom_width = 10.0
    restroom_depth = 8.0

    # Southwest restroom block
    rr_sw_x = -width/2 + wall_thickness
    rr_sw_y = -depth/2 + wall_thickness

    # Outer walls
    msp.add_lwpolyline([
        (rr_sw_x, rr_sw_y),
        (rr_sw_x + restroom_width, rr_sw_y),
        (rr_sw_x + restroom_width, rr_sw_y + restroom_depth),
        (rr_sw_x, rr_sw_y + restroom_depth),
        (rr_sw_x, rr_sw_y),
    ], dxfattribs={'layer': 'PARTITION_WALL'})

    # Toilet stalls (3 stalls)
    stall_width = 1.5
    for i in range(3):
        stall_x = rr_sw_x + 0.5 + i * (stall_width + 0.3)
        msp.add_lwpolyline([
            (stall_x, rr_sw_y + 0.5),
            (stall_x + stall_width, rr_sw_y + 0.5),
            (stall_x + stall_width, rr_sw_y + 2.5),
            (stall_x, rr_sw_y + 2.5),
        ], dxfattribs={'layer': 'FIXTURE'})

    # Southeast restroom block
    rr_se_x = width/2 - restroom_width - wall_thickness
    rr_se_y = -depth/2 + wall_thickness

    # Outer walls
    msp.add_lwpolyline([
        (rr_se_x, rr_se_y),
        (rr_se_x + restroom_width, rr_se_y),
        (rr_se_x + restroom_width, rr_se_y + restroom_depth),
        (rr_se_x, rr_se_y + restroom_depth),
        (rr_se_x, rr_se_y),
    ], dxfattribs={'layer': 'PARTITION_WALL'})

    # Toilet stalls (3 stalls)
    for i in range(3):
        stall_x = rr_se_x + 0.5 + i * (stall_width + 0.3)
        msp.add_lwpolyline([
            (stall_x, rr_se_y + 0.5),
            (stall_x + stall_width, rr_se_y + 0.5),
            (stall_x + stall_width, rr_se_y + 2.5),
            (stall_x, rr_se_y + 2.5),
        ], dxfattribs={'layer': 'FIXTURE'})

    # Ticketing counter area (near entrance)
    counter_length = 18.0
    counter_depth = 4.0
    counter_y = -depth/2 + 14.0

    # Counter enclosure
    msp.add_lwpolyline([
        (-counter_length/2 - 1, counter_y),
        (counter_length/2 + 1, counter_y),
        (counter_length/2 + 1, counter_y + counter_depth),
        (-counter_length/2 - 1, counter_y + counter_depth),
        (-counter_length/2 - 1, counter_y),
    ], dxfattribs={'layer': 'PARTITION_WALL'})

    # Individual counter stations (6 stations)
    station_width = 2.8
    for i in range(6):
        station_x = -counter_length/2 + i * (station_width + 0.2) + 0.5
        msp.add_lwpolyline([
            (station_x, counter_y + 0.5),
            (station_x + station_width, counter_y + 0.5),
            (station_x + station_width, counter_y + counter_depth - 0.5),
            (station_x, counter_y + counter_depth - 0.5),
        ], dxfattribs={'layer': 'COUNTER'})

    # Retail kiosks (mid-section) - 4 kiosks
    kiosk_size = 4.5
    kiosk_spacing = 11.0

    for i in range(4):
        kiosk_x = -16.5 + i * kiosk_spacing
        kiosk_y = 5.0

        # Kiosk enclosure
        msp.add_lwpolyline([
            (kiosk_x - kiosk_size/2, kiosk_y - kiosk_size/2),
            (kiosk_x + kiosk_size/2, kiosk_y - kiosk_size/2),
            (kiosk_x + kiosk_size/2, kiosk_y + kiosk_size/2),
            (kiosk_x - kiosk_size/2, kiosk_y + kiosk_size/2),
            (kiosk_x - kiosk_size/2, kiosk_y - kiosk_size/2),
        ], dxfattribs={'layer': 'RETAIL_KIOSK'})

        # Service counter inside
        msp.add_lwpolyline([
            (kiosk_x - 1.5, kiosk_y - 1.5),
            (kiosk_x + 1.5, kiosk_y - 1.5),
        ], dxfattribs={'layer': 'COUNTER'})

    # Waiting lounge seating areas (central atrium)
    seat_row_length = 12.0
    seat_depth = 1.5

    # North waiting area (3 rows)
    for i in range(3):
        seat_y = 15.0 + i * 3.0
        msp.add_lwpolyline([
            (-seat_row_length/2, seat_y),
            (seat_row_length/2, seat_y),
            (seat_row_length/2, seat_y + seat_depth),
            (-seat_row_length/2, seat_y + seat_depth),
            (-seat_row_length/2, seat_y),
        ], dxfattribs={'layer': 'SEATING'})

    # South waiting area (2 rows)
    for i in range(2):
        seat_y = -10.0 + i * 3.0
        msp.add_lwpolyline([
            (-seat_row_length/2, seat_y),
            (seat_row_length/2, seat_y),
            (seat_row_length/2, seat_y + seat_depth),
            (-seat_row_length/2, seat_y + seat_depth),
            (-seat_row_length/2, seat_y),
        ], dxfattribs={'layer': 'SEATING'})

    output_path = OUTPUT_DIR / "Terminal1_ARC_clean.dxf"
    doc.saveas(output_path)

    wall_count = 10  # Approximate
    partition_count = 5
    feature_count = 4 + num_gates + num_panels * 2  # Canopy + gates + panels

    print(f"Generated: {output_path}")
    print(f"  - {wall_count} exterior walls ({width:.1f}m x {depth:.1f}m)")
    print(f"  - Front: Landside entrance with {entrance_width:.1f}m opening + canopy")
    print(f"  - Back: Waterside jetty with {num_gates} boarding gates")
    print(f"  - Sides: {num_panels * 2} glass curtain wall panels")
    print(f"  - Interior: {partition_count} partitions (restrooms, counters, kiosks)")

    return output_path


def create_clean_str_dxf(floor_id, floor_data):
    """Generate clean STR DXF with columns and beams - Floor-specific configuration"""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    footprint = building_config.get('building_footprint', {})
    width = footprint.get('width_m', 45.0)
    depth = footprint.get('depth_m', 66.0)

    # Floor-specific structural grid configuration (2D array concept)
    # [floor_id][element_type] = parameters
    floor_config = {
        '1F': {
            'column_spacing': 6.0,
            'column_size': 0.5,  # Larger columns at base
            'beam_width': 0.4,
            'description': 'Ground floor - heavy loading'
        },
        '3F': {
            'column_spacing': 6.0,
            'column_size': 0.4,  # Standard columns
            'beam_width': 0.3,
            'description': 'Mid floor - standard loading'
        },
        '4F-6F': {
            'column_spacing': 6.0,
            'column_size': 0.35,  # Lighter columns at top
            'beam_width': 0.25,
            'description': 'Upper floors - reduced loading'
        }
    }

    config = floor_config.get(floor_id, floor_config['3F'])
    column_spacing = config['column_spacing']
    column_size = config['column_size']
    beam_width = config['beam_width']

    nx = int(width / column_spacing) + 1
    ny = int(depth / column_spacing) + 1

    # 2D Array of structural elements by floor
    columns_array = []
    beams_h_array = []
    beams_v_array = []

    # Place columns in 2D grid
    for ix in range(nx):
        col_row = []
        for iy in range(ny):
            cx = -width/2 + ix * column_spacing
            cy = -depth/2 + iy * column_spacing

            # Store column position
            col_row.append({'x': cx, 'y': cy, 'size': column_size})

            # Draw column as small square
            msp.add_lwpolyline([
                (cx - column_size/2, cy - column_size/2),
                (cx + column_size/2, cy - column_size/2),
                (cx + column_size/2, cy + column_size/2),
                (cx - column_size/2, cy + column_size/2),
                (cx - column_size/2, cy - column_size/2),
            ], dxfattribs={'layer': 'COLUMN LINE'})

        columns_array.append(col_row)

    # Add horizontal beams (connecting columns in X direction)
    for ix in range(nx - 1):
        beam_row = []
        for iy in range(ny):
            x1 = -width/2 + ix * column_spacing + column_size/2
            x2 = -width/2 + (ix + 1) * column_spacing - column_size/2
            cy = -depth/2 + iy * column_spacing

            # Store beam data
            beam_row.append({'x1': x1, 'x2': x2, 'y': cy, 'width': beam_width})

            # Draw beam as double line
            msp.add_line((x1, cy - beam_width/2), (x2, cy - beam_width/2), dxfattribs={'layer': 'BEAM LINE'})
            msp.add_line((x1, cy + beam_width/2), (x2, cy + beam_width/2), dxfattribs={'layer': 'BEAM LINE'})

        beams_h_array.append(beam_row)

    # Add vertical beams (connecting columns in Y direction)
    for ix in range(nx):
        beam_col = []
        for iy in range(ny - 1):
            cx = -width/2 + ix * column_spacing
            y1 = -depth/2 + iy * column_spacing + column_size/2
            y2 = -depth/2 + (iy + 1) * column_spacing - column_size/2

            # Store beam data
            beam_col.append({'x': cx, 'y1': y1, 'y2': y2, 'width': beam_width})

            msp.add_line((cx - beam_width/2, y1), (cx - beam_width/2, y2), dxfattribs={'layer': 'BEAM LINE'})
            msp.add_line((cx + beam_width/2, y1), (cx + beam_width/2, y2), dxfattribs={'layer': 'BEAM LINE'})

        beams_v_array.append(beam_col)

    column_count = nx * ny
    beam_count = len(beams_h_array) * ny + len(beams_v_array) * (ny - 1)

    output_path = OUTPUT_DIR / f"Terminal1_STR_{floor_id}_clean.dxf"
    doc.saveas(output_path)

    print(f"Generated: {output_path}")
    print(f"  - {config['description']}")
    print(f"  - {column_count} columns ({nx}×{ny} grid, size: {column_size}m)")
    print(f"  - {beam_count} beams (width: {beam_width}m)")
    print(f"  - 2D Array: {nx}×{ny} columns, {len(beams_h_array)}×{ny} H-beams, {nx}×{len(beams_v_array[0]) if beams_v_array else 0} V-beams")

    return output_path


def main():
    """Generate all clean DXF files for POC"""
    print("="*70)
    print("GENERATING CLEAN DXF FILES FOR POC")
    print("="*70)
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate ARC DXF (walls, curtain wall - NO SLABS)
    create_clean_arc_dxf()
    print()

    # Generate STR DXF for each floor (columns, beams - NO SLABS)
    str_floors = {
        '1F': {'elevation_m': 0.0},
        '3F': {'elevation_m': 8.0},
        '4F-6F': {'elevation_m': 12.0},
    }

    for floor_id, floor_data in str_floors.items():
        create_clean_str_dxf(floor_id, floor_data)
        print()

    print("="*70)
    print("CLEAN DXF GENERATION COMPLETE")
    print("="*70)
    print()
    print("Next steps:")
    print("1. Replace old DXF files with these clean versions")
    print("2. Run generate_arc_str_database.py")
    print("3. Floor slabs will come ONLY from programmatic generation")
    print("4. No more fragmented/overlapping slabs!")


if __name__ == '__main__':
    main()
