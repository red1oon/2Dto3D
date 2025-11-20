# MiniBonsai Changelog

## [2.0] - 2025-11-20 15:17

### Added - Major Features
- **Atrium floor selector** - Start/end floor controls with enable/disable
- **Auto door generation** - Building-type-specific door placement
  - Transport Hub: 12m glass entrance + 3× 4m boarding gates
  - Office: 3m revolving door + 2× 2m emergency exits
  - Residential: 2.5m lobby entrance
- **Glass curtain walls** - Transport Hub visualization with mullions (3m spacing)
- **Building type selector** - Transport Hub, Office, Residential
- **Export to DXF** - AutoCAD 2D drawings with layers per floor
- **Export to PDF** - A3 landscape multi-floor layout
- **Export to Bonsai DB** - SQLite with ARC/STR disciplines
  - Structural preset: 300×600mm RC beams on 6m grid
  - Floor heights: 3m, beam heights: 2.4m above floor

### Added - UI/UX
- Atrium settings panel with spinbox controls
- Building type dropdown (triggers door regeneration)
- Export panel with 3 export buttons
- Grid layout fix (resolved pack/grid mixing error)

### Added - Data Model
- `building.type` field in JSON
- `doors` array with type, position, width, label
- Auto-migration for old JSON formats
- Atrium UI synchronization on load

### Changed
- Window size increased to 1600×1000 for better visibility
- Atrium checkbox converted to grid layout for consistency
- Export dialogs start in appropriate directories (DXF/PDF → MiniBonsai, DB → DatabaseFiles)

### Fixed
- Geometry manager conflict (pack vs grid) in atrium panel
- Missing 'enabled' key in atrium data handling
- Atrium floor defaults (L0-L1 → L1-L3 auto-correction)

## [1.2] - 2025-11-20 14:33

### Added
- **Zone resizing** - Drag corner/edge handles to resize
- **Zone add/delete** - Create new zones, delete selected zones
- **Zone selection** - Click to select, shows resize handles
- **Visual feedback** - Thick borders when dragging/resizing/selected
- **Cursor feedback** - Changes to resize arrows on handles

### Changed
- Hit testing returns tuple (type, name) for zones and amenities
- Dragging system refactored to handle zones separately
- Drawing system highlights selected zones

### Fixed
- Zone drawing order (zones drawn before amenities)
- Handle size and positioning for accurate clicking

## [1.1] - 2025-11-20 13:00

### Added
- **Python desktop app** - Replaced HTML due to browser caching issues
- **Amenity dragging** - All 3 amenities (lift, washroom, stairs) movable
- **Atrium dragging** - Atrium void movable on L1-L3
- **JSON migration** - Auto-extract washroom/staircase from floor 0 to fixedAmenities
- **Floor switching** - GF, L1, L2, L3 buttons
- **Grid and rulers** - 5m grid with meter markings

### Changed
- Replaced HTML/JavaScript with Python/Tkinter
- Window size: 1400×900
- Scale: 6 pixels per meter
- Atrium default: L1-L3 (not L0-L1)

### Fixed
- Browser caching preventing HTML updates
- Amenity visibility (all 3 now present)
- Coordinate system (building-relative positioning)

## [1.0] - 2025-11-20 10:39

### Added - Initial Release
- **HTML/JavaScript designer** - Web-based 2D layout tool
- **Zone management** - 4 default zones (ticketing, waiting, retail, boarding)
- **Zone dragging** - Click and drag zone bodies
- **Zone labels** - Ground floor vs upper floor labels
- **Floor selection** - Switch between GF, L1, L2, L3
- **JSON save/load** - Persist designs
- **Grid background** - Visual reference
- **Building outline** - 90m × 70m default

### Known Issues
- Amenities not visible/movable
- Browser caching causes stale versions to load
- Zones can overlap (no collision detection)
- Atrium appears on wrong floors

## Development Timeline

**10:39** - Initial HTML version created
**12:00** - Attempted to add amenity dragging (HTML)
**13:00** - Switched to Python app due to browser cache issues
**14:00** - Added zone resizing and selection
**15:00** - Added atrium controls, doors, glass walls, exports
**15:17** - Released v2.0 Complete

## Migration Notes

### From v1.0 (HTML) to v1.1 (Python)
- Data format remains compatible
- HTML files kept for reference but Python app recommended

### From v1.1 to v2.0
- Added `building.type` field (defaults to 'Transport Hub')
- Added `doors` array (auto-generated if missing)
- Atrium gets 'enabled' key if missing (defaults to true)
- Atrium floors auto-corrected (L0-L1 → L1-L3)

### Old Format Support
v2.0 automatically migrates JSON from older formats:
- Extracts washroom/staircase from `floorsData[0].amenities`
- Adds to `fixedAmenities` if missing
- Fixes atrium floor range
- Generates doors based on building type
