# MiniBonsai - Rapid BIM Generator for Transport Hubs

**Version:** 2.0 (Nov 20, 2025)
**Status:** Proof of Concept (POC)

## Overview

MiniBonsai is a lightweight 2D designer that generates 3D Building Information Models (BIM) for transport hubs and similar buildings. It bridges the gap between conceptual design and detailed BIM, allowing rapid iteration on layouts before committing to full Bonsai/IFC workflows.

### Key Features

- ✅ **2D Visual Designer** - Drag-and-drop interface for rapid layout design
- ✅ **Zone Management** - Resize, add, delete zones per floor
- ✅ **Synced Amenities** - Lift, washroom, staircase consistent across all floors
- ✅ **Atrium Control** - Multi-floor voids with configurable floor range
- ✅ **Building Types** - Transport Hub, Office, Residential presets
- ✅ **Auto Door Generation** - Building-type-specific door placement
- ✅ **Glass Walls** - Curtain wall visualization for transport hubs
- ✅ **Export Formats** - DXF, PDF, Bonsai DB, JSON
- ✅ **Structural Presets** - Auto-generated RC beams (300x600mm on 6m grid)

## Quick Start

### Installation

```bash
# Prerequisites
pip3 install tkinter  # Usually pre-installed

# Optional (for exports)
pip3 install ezdxf reportlab
```

### Running the App

```bash
cd /home/red1/Documents/bonsai/2Dto3D/MiniBonsai/GUI
python3 jetty_builder_complete.py
```

### Basic Workflow

1. **Design** - Load JSON or start from scratch
2. **Edit** - Drag zones, amenities; resize with handles
3. **Configure** - Set building dimensions, atrium floors
4. **Export** - DXF for CAD, PDF for review, DB for Bonsai

## File Structure

```
MiniBonsai/
├── GUI/
│   ├── jetty_builder_complete.py    # Main application (v2.0)
│   ├── jetty_designer_app.py        # Simplified version (v1.2)
│   ├── JettyDesigner.html            # Original HTML version
│   └── *.html                        # Development iterations
├── SampleData/
│   └── terminal1_complete_design(10).json  # Example project
├── README.md                         # This file
├── CHANGELOG.md                      # Version history
└── SPECS.md                          # Future: Full specifications
```

## Features Documentation

### Building Settings
- **Width/Depth** - Building dimensions in meters
- **Floors** - Number of floors (dynamically add/remove)
- **Type** - Transport Hub, Office, Residential (affects doors, glass walls)

### Atrium Settings
- **Enable/Disable** - Toggle atrium visibility
- **Start Floor** - First floor with atrium void (default: L1)
- **End Floor** - Last floor with atrium void (default: L3)

### Zone Tools
- **Add New Zone** - Creates zone at building center
- **Delete Selected Zone** - Removes selected zone (per floor)
- **Resize** - Drag corner/edge handles when zone is selected

### Auto Door Generation
**Transport Hub:**
- Main entrance (12m sliding glass)
- 3x boarding gates (4m each, rear)

**Office:**
- Main entrance (3m revolving door)
- 2x emergency exits (2m, side walls)

**Residential:**
- Lobby entrance (2.5m standard door)

### Export Formats

#### JSON (Native)
Complete design data including:
- Building metadata (width, depth, floors, type)
- Fixed amenities (lift, washroom, staircase)
- Atrium configuration
- Per-floor zone data
- Door placements

#### DXF (AutoCAD)
2D plan view with:
- Building outline
- Zones on separate layers (FLOOR_0, FLOOR_1, etc.)
- Amenities with labels
- Doors with symbols
- Atrium as dashed outline

#### PDF (Standard Drawings)
Multi-floor layout on A3 landscape:
- All floors in grid layout (2 per row)
- Building outline, zones, amenities
- Floor labels
- Similar to TASBLOCK output format

#### Bonsai DB (SQLite)
BIM database with ARC/STR disciplines:
- **STR elements:** RC beams (300x600mm) on 6m grid
- **ARC elements:** Walls, doors, amenities, voids
- Compatible with Bonsai federation structure
- Floor heights: 3m per floor
- Beam heights: 2.4m above floor level

## Technical Details

### Data Model

**Fixed Amenities** (synced across all floors):
```json
{
  "lift": {"x": 42.25, "y": -4.42, "width": 4.5, "height": 13.5},
  "washroom": {"x": 31.0, "y": -30.83, "width": 27.33, "height": 7.67},
  "staircase": {"x": -1.0, "y": -19.25, "width": 27.67, "height": 5.5}
}
```

**Zones** (independent per floor):
```json
{
  "level": 0,
  "zones": {
    "ticketing": {"label": "TICKETING", "x": -20, "y": 0, "width": 15, "height": 20},
    "waiting": {"label": "WAITING", "x": 0, "y": 0, "width": 20, "height": 20}
  }
}
```

**Atrium** (synced across floor range):
```json
{
  "x": 1.92, "y": 3.17,
  "width": 48.83, "height": 37.67,
  "startFloor": 1, "endFloor": 3,
  "enabled": true
}
```

### Coordinate System
- **Origin:** Building center (0, 0)
- **Units:** Meters
- **X-axis:** Building width (horizontal)
- **Y-axis:** Building depth (vertical)
- **Z-axis:** Floor height (exports only)

### Structural Presets (POC)
**RC Frame:**
- Beams: 300mm × 600mm, 6m grid spacing
- Longitudinal beams along building width
- Transverse beams along building depth
- Ceiling level: Floor height + 2.4m
- Grade: Concrete C30 (placeholder)

## Known Limitations

1. **No 3D visualization** - Only 2D plan view (3D export only)
2. **No undo/redo** - Manual save/reload required
3. **Basic collision detection** - Zones can overlap
4. **Fixed structural grid** - 6m spacing hardcoded
5. **No IFC export** - Only SQLite database format
6. **No material properties** - Simplified BIM data
7. **Single user** - No collaborative editing

## Roadmap (Future)

See `SPECS.md` (to be created) for detailed future enhancements:
- 3D preview window
- IFC4 export
- Structural optimization
- Code compliance checking
- Template library
- MEP integration
- Cost estimation

## Development Notes

### Version History
- **v1.0** (10:39) - Initial HTML version with basic zones
- **v1.1** (12:00) - Added amenity dragging
- **v1.2** (14:00) - Python app, zone resizing
- **v2.0** (15:17) - Complete app with atrium, doors, glass walls, exports

### Testing
Load `terminal1_complete_design(10).json` from Downloads to test:
- Old format migration (washroom/staircase from floor 0)
- Atrium floor correction (L0-L1 → L1-L3)
- All zones, amenities, doors

### Browser Cache Issues
HTML versions suffered from aggressive browser caching. Python desktop app is recommended for production use.

## Contact & Support

**Project:** Bonsai BIM Federation
**Repository:** https://github.com/red1oon/IfcOpenShell
**Branch:** feature/IFC4_DB

## License

Part of the IfcOpenShell/Bonsai ecosystem.
