#!/usr/bin/env python3
"""
Component Library for Terminal 1 DXF Generation
================================================

Provides programmatic generation of all building components:
- ARC: Seating, retail, ticketing, gates, washrooms
- STR: Columns, beams, slabs
- ELEC: Outlets, switches, lighting
- FP: Sprinklers, hydrants, hose reels
- HVAC: AC units, ceiling fans, ventilation
- ACMW: Chilled water piping

Each component is a function that returns DXF entities with proper:
- Dimensions
- Layer assignments
- Grid alignment
- Placement rules
"""

import ezdxf
import math


# =============================================================================
# ARC COMPONENTS
# =============================================================================

def create_seating_row(msp, x, y, orientation='north', layer='A-FURN'):
    """
    Seating Row: 6.0m × 1.5m bench for 6 persons

    Args:
        msp: DXF modelspace
        x, y: Center position (mm)
        orientation: 'north', 'south', 'east', 'west' (facing direction)
        layer: DXF layer name
    """
    # Dimensions in mm
    length = 6000
    width = 1500

    # Calculate corners based on orientation
    if orientation in ['north', 'south']:
        # Bench runs east-west
        pts = [
            (x - length/2, y - width/2),
            (x + length/2, y - width/2),
            (x + length/2, y + width/2),
            (x - length/2, y + width/2),
            (x - length/2, y - width/2)
        ]
    else:
        # Bench runs north-south
        pts = [
            (x - width/2, y - length/2),
            (x + width/2, y - length/2),
            (x + width/2, y + length/2),
            (x - width/2, y + length/2),
            (x - width/2, y - length/2)
        ]

    # Draw bench outline
    msp.add_lwpolyline(pts, dxfattribs={'layer': layer})

    # Draw seat slats (visual detail)
    if orientation in ['north', 'south']:
        for i in range(6):
            seat_x = x - length/2 + (i + 0.5) * (length / 6)
            msp.add_circle((seat_x, y), 150, dxfattribs={'layer': layer})
    else:
        for i in range(6):
            seat_y = y - length/2 + (i + 0.5) * (length / 6)
            msp.add_circle((x, seat_y), 150, dxfattribs={'layer': layer})


def create_retail_unit(msp, x, y, layer='A-WALL-PRTN'):
    """
    Retail Unit: 6.0m × 8.0m shop with open door

    Args:
        msp: DXF modelspace
        x, y: Center position (mm)
        layer: DXF layer for walls
    """
    width = 6000
    depth = 8000
    door_width = 2400

    # Shop outline
    x1, y1 = x - width/2, y - depth/2
    x2, y2 = x + width/2, y + depth/2

    # Left wall
    msp.add_line((x1, y1), (x1, y2), dxfattribs={'layer': layer})

    # Right wall
    msp.add_line((x2, y1), (x2, y2), dxfattribs={'layer': layer})

    # Back wall
    msp.add_line((x1, y2), (x2, y2), dxfattribs={'layer': layer})

    # Front wall with door opening
    msp.add_line((x1, y1), (x - door_width/2, y1), dxfattribs={'layer': layer})
    msp.add_line((x + door_width/2, y1), (x2, y1), dxfattribs={'layer': layer})

    # Door opening marker
    msp.add_line((x - door_width/2, y1), (x + door_width/2, y1),
                 dxfattribs={'layer': 'A-DOOR', 'linetype': 'DASHED'})

    # Counter at back
    counter_depth = 800
    msp.add_line((x1 + 500, y2 - counter_depth),
                 (x2 - 500, y2 - counter_depth),
                 dxfattribs={'layer': 'A-FURN'})


def create_ticketing_counter(msp, x, y, orientation='south', layer='A-FURN'):
    """
    Ticketing Counter: 2.8m × 1.2m with glass partition

    Args:
        msp: DXF modelspace
        x, y: Center position (mm)
        orientation: Direction staff faces
        layer: DXF layer
    """
    width = 2800
    depth = 1200

    # Counter base
    pts = [
        (x - width/2, y - depth/2),
        (x + width/2, y - depth/2),
        (x + width/2, y + depth/2),
        (x - width/2, y + depth/2),
        (x - width/2, y - depth/2)
    ]
    msp.add_lwpolyline(pts, dxfattribs={'layer': layer})

    # Glass partition (customer side)
    glass_y = y - depth/2 if orientation == 'south' else y + depth/2
    msp.add_line((x - width/2, glass_y), (x + width/2, glass_y),
                 dxfattribs={'layer': 'A-GLAZ'})

    # Transaction tray marker
    msp.add_circle((x, glass_y), 200, dxfattribs={'layer': 'A-FURN'})


def create_boarding_gate(msp, x, y, gate_num, layer='A-DOOR'):
    """
    Boarding Gate: 8.0m wide with telescopic bridge

    Args:
        msp: DXF modelspace
        x, y: Center position at waterside wall (mm)
        gate_num: Gate number (1, 2, 3...)
        layer: DXF layer
    """
    width = 8000
    depth = 3000  # Extension to jetty

    # Gate frame
    pts = [
        (x - width/2, y),
        (x - width/2, y + depth),
        (x + width/2, y + depth),
        (x + width/2, y)
    ]
    msp.add_lwpolyline(pts, dxfattribs={'layer': layer})

    # Telescopic bridge (centerline)
    msp.add_line((x, y), (x, y + depth),
                 dxfattribs={'layer': layer, 'linetype': 'DASHED'})

    # Gate number label
    text = msp.add_text(f'GATE {gate_num}',
                        dxfattribs={'layer': 'A-ANNO-NOTE', 'height': 400})
    text.dxf.insert = (x, y + depth/2)
    text.dxf.align_point = (x, y + depth/2)
    text.dxf.halign = 4  # MIDDLE_CENTER


def create_washroom_block(msp, x, y, layer='A-WALL-PRTN'):
    """
    Washroom Block: 6.0m × 8.0m with fixtures

    Args:
        msp: DXF modelspace
        x, y: Center position (mm)
        layer: DXF layer
    """
    width = 6000
    depth = 8000

    # Washroom outline
    x1, y1 = x - width/2, y - depth/2
    x2, y2 = x + width/2, y + depth/2

    pts = [
        (x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)
    ]
    msp.add_lwpolyline(pts, dxfattribs={'layer': layer})

    # Partition dividing male/female
    msp.add_line((x, y1), (x, y2), dxfattribs={'layer': layer})

    # Fixtures (simple circles for toilets/sinks)
    # Male side (left)
    for i in range(3):
        toilet_y = y1 + 1000 + i * 2000
        msp.add_circle((x - width/4, toilet_y), 300, dxfattribs={'layer': 'A-FURN'})

    # Female side (right)
    for i in range(5):
        toilet_y = y1 + 800 + i * 1400
        msp.add_circle((x + width/4, toilet_y), 300, dxfattribs={'layer': 'A-FURN'})

    # Labels
    text_m = msp.add_text('M', dxfattribs={'layer': 'A-ANNO-NOTE', 'height': 500})
    text_m.dxf.insert = (x - width/4, y)
    text_m.dxf.align_point = (x - width/4, y)
    text_m.dxf.halign = 4  # MIDDLE_CENTER

    text_f = msp.add_text('F', dxfattribs={'layer': 'A-ANNO-NOTE', 'height': 500})
    text_f.dxf.insert = (x + width/4, y)
    text_f.dxf.align_point = (x + width/4, y)
    text_f.dxf.halign = 4  # MIDDLE_CENTER


# =============================================================================
# STR COMPONENTS
# =============================================================================

def create_column(msp, x, y, size=400, layer='S-COLS', label=None):
    """
    Structural Column: 400mm × 400mm

    Args:
        msp: DXF modelspace
        x, y: Center position (mm)
        size: Column size (mm)
        layer: DXF layer
        label: Grid label (e.g., 'A1', 'B2')
    """
    half = size / 2
    pts = [
        (x - half, y - half),
        (x + half, y - half),
        (x + half, y + half),
        (x - half, y + half),
        (x - half, y - half)
    ]
    msp.add_lwpolyline(pts, dxfattribs={'layer': layer})

    if label:
        text = msp.add_text(label, dxfattribs={'layer': layer, 'height': 200})
        text.dxf.insert = (x, y)
        text.dxf.align_point = (x, y)
        text.dxf.halign = 4  # MIDDLE_CENTER


def create_beam(msp, x1, y1, x2, y2, width=300, layer='S-BEAM'):
    """
    Structural Beam: 300mm wide × 600mm deep

    Args:
        msp: DXF modelspace
        x1, y1, x2, y2: Endpoints (mm)
        width: Beam width (mm)
        layer: DXF layer
    """
    # Calculate perpendicular offset
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx*dx + dy*dy)

    if length == 0:
        return

    # Unit perpendicular vector
    px = -dy / length * width / 2
    py = dx / length * width / 2

    # Beam edges (double line representation)
    msp.add_line((x1 + px, y1 + py), (x2 + px, y2 + py),
                 dxfattribs={'layer': layer})
    msp.add_line((x1 - px, y1 - py), (x2 - px, y2 - py),
                 dxfattribs={'layer': layer})


# =============================================================================
# ELEC COMPONENTS
# =============================================================================

def create_power_outlet(msp, x, y, layer='E-POWR'):
    """
    Power Outlet: 13A switched socket

    Args:
        msp: DXF modelspace
        x, y: Position (mm)
        layer: DXF layer
    """
    # Simple square symbol
    size = 200
    half = size / 2
    pts = [
        (x - half, y - half),
        (x + half, y - half),
        (x + half, y + half),
        (x - half, y + half),
        (x - half, y - half)
    ]
    msp.add_lwpolyline(pts, dxfattribs={'layer': layer})

    # Plus sign inside
    msp.add_line((x - half/2, y), (x + half/2, y), dxfattribs={'layer': layer})
    msp.add_line((x, y - half/2), (x, y + half/2), dxfattribs={'layer': layer})


def create_light_switch(msp, x, y, layer='E-SWCH'):
    """
    Light Switch: Standard rocker switch

    Args:
        msp: DXF modelspace
        x, y: Position (mm)
        layer: DXF layer
    """
    # Circle with 'S' inside
    msp.add_circle((x, y), 150, dxfattribs={'layer': layer})
    text = msp.add_text('S', dxfattribs={'layer': layer, 'height': 150})
    text.dxf.insert = (x, y)
    text.dxf.align_point = (x, y)
    text.dxf.halign = 4  # MIDDLE_CENTER


def create_light_fixture(msp, x, y, layer='E-LITE'):
    """
    LED Downlight: Recessed ceiling light

    Args:
        msp: DXF modelspace
        x, y: Position (mm)
        layer: DXF layer
    """
    # Circle with cross
    msp.add_circle((x, y), 150, dxfattribs={'layer': layer})
    msp.add_line((x - 100, y), (x + 100, y), dxfattribs={'layer': layer})
    msp.add_line((x, y - 100), (x, y + 100), dxfattribs={'layer': layer})


# =============================================================================
# FP COMPONENTS
# =============================================================================

def create_sprinkler(msp, x, y, sprinkler_type='pendent', layer='FP-SPKL'):
    """
    Fire Sprinkler: Pendent or sidewall type

    Args:
        msp: DXF modelspace
        x, y: Position (mm)
        sprinkler_type: 'pendent' or 'sidewall'
        layer: DXF layer
    """
    # Circle with 'SP' inside
    msp.add_circle((x, y), 120, dxfattribs={'layer': layer})

    if sprinkler_type == 'pendent':
        # Vertical drop indicator
        msp.add_line((x, y - 120), (x, y - 300), dxfattribs={'layer': layer})
    else:
        # Sidewall spray indicator
        msp.add_line((x, y), (x + 300, y), dxfattribs={'layer': layer})
        msp.add_line((x + 300, y), (x + 250, y + 50), dxfattribs={'layer': layer})
        msp.add_line((x + 300, y), (x + 250, y - 50), dxfattribs={'layer': layer})


def create_fire_hydrant(msp, x, y, layer='FP-STND'):
    """
    Fire Hydrant: Internal hydrant with hose cabinet

    Args:
        msp: DXF modelspace
        x, y: Position (mm)
        layer: DXF layer
    """
    # Cabinet rectangle
    width, height = 800, 1200
    pts = [
        (x - width/2, y - height/2),
        (x + width/2, y - height/2),
        (x + width/2, y + height/2),
        (x - width/2, y + height/2),
        (x - width/2, y - height/2)
    ]
    msp.add_lwpolyline(pts, dxfattribs={'layer': layer})

    # 'FH' label
    text = msp.add_text('FH', dxfattribs={'layer': layer, 'height': 300})
    text.dxf.insert = (x, y)
    text.dxf.align_point = (x, y)
    text.dxf.halign = 4  # MIDDLE_CENTER


# =============================================================================
# HVAC COMPONENTS
# =============================================================================

def create_ac_cassette(msp, x, y, layer='M-HVAC'):
    """
    AC Ceiling Cassette: 4-way discharge

    Args:
        msp: DXF modelspace
        x, y: Position (mm)
        layer: DXF layer
    """
    size = 800
    half = size / 2

    # Square outline
    pts = [
        (x - half, y - half),
        (x + half, y - half),
        (x + half, y + half),
        (x - half, y + half),
        (x - half, y - half)
    ]
    msp.add_lwpolyline(pts, dxfattribs={'layer': layer})

    # 4-way discharge arrows
    msp.add_line((x, y), (x, y - half), dxfattribs={'layer': layer})  # North
    msp.add_line((x, y), (x + half, y), dxfattribs={'layer': layer})  # East
    msp.add_line((x, y), (x, y + half), dxfattribs={'layer': layer})  # South
    msp.add_line((x, y), (x - half, y), dxfattribs={'layer': layer})  # West


def create_ceiling_fan(msp, x, y, layer='M-VENT'):
    """
    Ceiling Fan: HVLS (High Volume Low Speed)

    Args:
        msp: DXF modelspace
        x, y: Position (mm)
        layer: DXF layer
    """
    diameter = 2400
    radius = diameter / 2

    # Fan blades (4 blades as lines)
    msp.add_circle((x, y), radius, dxfattribs={'layer': layer, 'linetype': 'DASHED'})
    msp.add_line((x - radius, y), (x + radius, y), dxfattribs={'layer': layer})
    msp.add_line((x, y - radius), (x, y + radius), dxfattribs={'layer': layer})

    # Center hub
    msp.add_circle((x, y), 150, dxfattribs={'layer': layer})


# =============================================================================
# ACMW COMPONENTS
# =============================================================================

def create_acmw_riser(msp, x, y, layer='P-ACMW'):
    """
    Chilled Water Riser: DN80 vertical pipe

    Args:
        msp: DXF modelspace
        x, y: Position (mm)
        layer: DXF layer
    """
    # Double circle for supply/return
    msp.add_circle((x - 80, y), 100, dxfattribs={'layer': layer})
    msp.add_circle((x + 80, y), 100, dxfattribs={'layer': layer})

    # Labels
    text_s = msp.add_text('S', dxfattribs={'layer': layer, 'height': 100})
    text_s.dxf.insert = (x - 80, y)
    text_s.dxf.align_point = (x - 80, y)
    text_s.dxf.halign = 4  # MIDDLE_CENTER

    text_r = msp.add_text('R', dxfattribs={'layer': layer, 'height': 100})
    text_r.dxf.insert = (x + 80, y)
    text_r.dxf.align_point = (x + 80, y)
    text_r.dxf.halign = 4  # MIDDLE_CENTER


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_point_in_bounds(x, y, bounds):
    """
    Check if point (x, y) is inside rectangular bounds

    Args:
        x, y: Point coordinates
        bounds: Dict with 'x_min', 'x_max', 'y_min', 'y_max'

    Returns:
        True if point is inside bounds
    """
    return (bounds['x_min'] <= x <= bounds['x_max'] and
            bounds['y_min'] <= y <= bounds['y_max'])


def is_point_in_atrium(x, y, atrium_bounds):
    """
    Check if point is inside atrium void

    Args:
        x, y: Point coordinates
        atrium_bounds: Dict with atrium boundaries or None

    Returns:
        True if point is in atrium (should be avoided)
    """
    if not atrium_bounds:
        return False
    return is_point_in_bounds(x, y, atrium_bounds)


def calculate_zone_bounds(zone_data, building_width, building_depth):
    """
    Calculate absolute bounds for a zone from JSON data

    Args:
        zone_data: Dict with 'x', 'y', 'width', 'height' in meters
        building_width: Total building width (m)
        building_depth: Total building depth (m)

    Returns:
        Dict with 'x_min', 'x_max', 'y_min', 'y_max' in mm
    """
    scale = 1000.0  # m to mm

    # Zone center and size (from JSON)
    zone_x = zone_data.get('x', 0) * scale
    zone_y = zone_data.get('y', 0) * scale
    zone_w = zone_data.get('width', 6.0) * scale
    zone_h = zone_data.get('height', 6.0) * scale

    # Building center offset
    bldg_w = building_width * scale
    bldg_d = building_depth * scale

    # Absolute bounds
    return {
        'x_min': zone_x - zone_w/2,
        'x_max': zone_x + zone_w/2,
        'y_min': zone_y - zone_h/2,
        'y_max': zone_y + zone_h/2
    }
