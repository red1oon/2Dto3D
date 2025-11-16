# Mini Bonsai Tree GUI - 2D-to-3D Integration

**Date:** November 17, 2025
**Context:** Integration plan for Mini Bonsai Tree GUI with 2D-to-3D conversion pipeline

---

## 🎯 Overview

The Mini Bonsai Tree GUI will provide a user-friendly interface to:
1. **Select DXF folder** containing architectural/MEP drawings
2. **Configure layer mappings** and template properties
3. **Process DXFs** to database with 3D geometry
4. **Adjust disciplines** (add ACMV, modify mappings, regenerate)
5. **Load into Blender** for coordination/clash detection

---

## 📋 Workflow: User Perspective

### Step 1: Project Setup
```
[Mini Bonsai Tree GUI]
├─ New Project
│  ├─ Project Name: "Terminal 1 - 2D Conversion"
│  ├─ DXF Folder: [Browse] → Select folder with DXF files
│  ├─ Reference IFC (optional): For dimension validation
│  └─ Output Database: Terminal1_Converted.db
```

### Step 2: Layer Mapping Configuration
```
[Layer Mapping Tab]
├─ Auto-Scan DXF Layers (discovers all layer names)
│  Found: 166 layers in "2. BANGUNAN TERMINAL 1.dxf"
│
├─ Smart Template Matching (suggests mappings)
│  ✓ "WALL" → Architecture (ARC)
│  ✓ "DOOR" → Architecture (ARC)
│  ✓ "Bomba" → Fire Protection (FP)
│  ✓ "z-ac-pump" → ACMV
│  ? "z-fire-alarm" → [User assigns: FP]
│
├─ Manual Override
│  [Layer Name] [Discipline ▼] [IFC Class ▼] [Confidence]
│  Bomba        FP             IfcPump        1.0
│  z-ac-pump    ACMV           IfcPump        0.9
│
└─ Save Template: "Airport_Terminal_Standard.json"
```

### Step 3: Spatial Filter (Main Building Selection)
```
[Spatial Filter Tab]
├─ Auto-Detect Main Building
│  ✓ Reference IFC loaded: 68m × 48m expected
│  ✓ Density analysis: Found densest region 74.6m × 52.9m
│  ✓ Generated bounding box: [Preview on map]
│
├─ Manual Adjustment
│  [Interactive Map View]
│  ├─ Drag bounding box corners
│  ├─ Zoom to entities in region
│  └─ Preview: 2,259 entities selected
│
└─ Filters
   ✓ Exclude title blocks (auto-detected)
   ✓ Exclude site boundaries
   ✓ Exclude annotations
```

### Step 4: Discipline Management
```
[Disciplines Tab]
├─ Detected from DXF
│  ✓ Architecture (Seating) - 911 elements (from WALL, DOOR, WINDOW layers)
│  ✓ Structure (STR) - 29 elements (from COL, column layers)
│  ✓ Fire Protection (FP) - 71 elements (from Bomba, z-fire-* layers)
│  ✓ Electrical (ELEC) - 26 elements (from EL layers)
│
├─ Add Missing Disciplines
│  [+ Add Discipline]
│  Name: ACMV
│  Layers: [Select] z-ac-pump, z-mech-text
│  Color: Orange (0.9, 0.7, 0.3)
│  → [Scan & Assign] → Found 148 entities
│
└─ Re-assign Elements
   [Element List] [Current: FP] → [New: ACMV ▼]
   z-ac-pump entities (148) → Move to ACMV
```

### Step 5: Geometry Template Configuration
```
[Geometry Templates Tab]
├─ Wall Settings
│  ├─ Extract actual length: ✓ (from DXF polylines)
│  ├─ Default thickness: 200mm (if not measured)
│  ├─ Default height: 3.0m (single floor)
│  └─ Height rules: [Airport Terminal ▼]
│
├─ Door Settings
│  ├─ Extract size from: [Block Attributes ▼] or [Bounding Box]
│  ├─ Default sizes: 700mm, 900mm, 1200mm
│  └─ Parse naming: "DOOR-900x2100" → 0.9m × 2.1m
│
├─ Window Settings
│  ├─ Extract size from: [Block Attributes ▼]
│  ├─ Default sizes: 900mm, 1200mm, 1500mm
│  └─ Sill height: 1.0m above floor
│
├─ Column Settings
│  ├─ Extract from: [Circle Diameter ▼] or [Rectangle Dimensions]
│  ├─ Default diameter: 400mm
│  └─ Height: 3.5m (floor to floor)
│
└─ Equipment/Proxy
   ├─ Default size: 1.0m cube
   └─ By discipline: ACMV=1.5m, FP=1.2m, ELEC=0.8m
```

### Step 6: Process & Generate
```
[Process Tab]
├─ Extraction Settings
│  Workers: 4 threads (parallel processing)
│  Cache: ✓ Enable (skip unchanged files)
│
├─ [Run Extraction]
│  ⏳ Phase 1: Spatial filtering... (10s)
│  ⏳ Phase 2: DXF extraction... (30s)
│  ⏳ Phase 3: Dimension validation... (1s)
│  ⏳ Phase 4: 3D geometry generation... (15s)
│  ✅ Complete: 1,037 elements with 3D geometry
│
└─ Results
   Database: Terminal1_Converted.db (1.2MB)
   Coverage: 100% (1,037/1,037 with geometry)
   Dimensions: 64.1m × 42.0m × 4.4m ✓
   Match: 96% vs reference IFC
```

### Step 7: Review & Adjust
```
[Preview Tab]
├─ Quick 3D Preview (embedded viewer)
│  [3D Viewport showing wireframe bounding boxes]
│  ├─ Toggle disciplines: [Seating] [STR] [FP] [ELEC] [ACMV]
│  ├─ Color by discipline
│  └─ Measure dimensions
│
├─ Statistics
│  Total Elements: 1,037
│  ├─ Seating: 911 (88%)
│  ├─ Structure: 29 (3%)
│  ├─ Fire Protection: 71 (7%)
│  └─ Electrical: 26 (2%)
│
└─ Validation
   ✓ Dimensions within tolerance
   ✓ No elements outside bounding box
   ✓ All elements have 3D geometry
   ⚠ ACMV discipline not detected (add manually?)
```

### Step 8: Adjust & Regenerate
```
[Adjust Tab]
User realizes: "z-ac-pump should be ACMV, not FP"

├─ Go back to [Disciplines Tab]
│  ├─ Add ACMV discipline
│  ├─ Assign z-ac-pump layers to ACMV
│  └─ Update layer mappings JSON
│
├─ [Regenerate Database]
│  Options:
│  ⚪ Re-extract from DXF (full pipeline, slow)
│  ⚫ Update discipline only (fast, preserves geometry)
│
│  → [Update Discipline] (5 seconds)
│
└─ Results
   Updated 148 elements: FP → ACMV
   New breakdown:
   ├─ Seating: 911
   ├─ Structure: 29
   ├─ Fire Protection: 71 - 148 = 0 (moved to ACMV)
   ├─ Electrical: 26
   └─ ACMV: 148 ✓ NEW
```

### Step 9: Export to Blender
```
[Export Tab]
├─ Blender Integration
│  ✓ Create .blend cache (7.3MB)
│  ✓ Apply discipline colors
│  ✓ Create collections per discipline
│
├─ [Open in Blender]
│  → Launches Blender with Bonsai
│  → Loads database
│  → User can toggle disciplines, clash detection, etc.
│
└─ Alternative: Save Database Only
   → Terminal1_Converted.db
   → User loads manually in Bonsai Federation panel
```

---

## 🔍 Answering Your Questions

### Q1: Why is Fire Protection (FP) detected?

**Answer:** The **architectural DXF file contains embedded MEP disciplines**:

```
Layers in "2. BANGUNAN TERMINAL 1.dxf" (Architectural file):
├─ Fire Protection Layers:
│  ├─ Bomba (293 entities) - Fire pumps
│  ├─ BOMBA REQUIREMENTS (299 entities)
│  ├─ z-fire-alarm (184 entities)
│  ├─ z-fire-smoke-grille (167 entities)
│  ├─ z-fire-tank (1 entity)
│  └─ z-sprinkler-text (13 entities)
│
├─ ACMV/Mechanical Layers:
│  ├─ z-ac-pump (148 entities) - AC pumps
│  └─ z-mech-text (68 entities)
│
└─ Electrical Layers:
   └─ EL* layers (26 entities)
```

The layer mapping (`smart_layer_mappings.json`) maps:
```json
"Bomba": {"discipline": "FP", "confidence": 1.0}
```

So FP was **automatically detected from the DXF layer names**, not manually added.

### Q2: Can GUI add disciplines like ACMV?

**Answer:** **YES!** Two scenarios:

**Scenario A: ACMV layers exist but unmapped**
```
Current state:
- z-ac-pump layers present (148 entities)
- Currently mapped to generic/FP (incorrect)

GUI action:
1. User clicks [+ Add Discipline]
2. Name: ACMV, Color: Orange
3. Select layers: z-ac-pump, z-mech-text
4. Click [Scan & Assign]
5. Result: 148 entities moved from FP to ACMV
```

**Scenario B: User has separate ACMV DXF file**
```
DXF folder contains:
├─ 01_Architecture.dxf (current source)
├─ 02_Structure.dxf
├─ 03_ACMV.dxf ← NEW
└─ 04_Electrical.dxf

GUI action:
1. Add 03_ACMV.dxf to project
2. Auto-scan layers (finds ACMV-specific layer names)
3. Add ACMV discipline
4. Process all DXFs → merge into single database
5. Result: Database now has ACMV elements
```

### Q3: Can GUI adjust template properties and regenerate?

**Answer:** **YES!** Multiple regeneration modes:

**Mode 1: Update Geometry Only (Fast)**
```
User adjusts:
- Wall default height: 3.0m → 3.5m
- Door default width: 900mm → 1000mm

GUI action:
[Regenerate Geometry] (keeps positions, re-generates meshes)
- Reads existing element_transforms (positions preserved)
- Re-runs generate_3d_geometry.py with new parameters
- Updates base_geometries table
- Time: ~15 seconds (geometry only)
```

**Mode 2: Update Disciplines Only (Fastest)**
```
User adjusts:
- Move z-ac-pump from FP to ACMV

GUI action:
[Update Discipline Mapping] (SQL update only)
- UPDATE elements_meta SET discipline='ACMV' WHERE layer LIKE 'z-ac-pump%'
- No re-extraction, no geometry changes
- Time: <1 second
```

**Mode 3: Full Re-extraction (Slow)**
```
User adjusts:
- Changed spatial filter bounding box
- Updated layer mappings (wall → ARC instead of generic)

GUI action:
[Full Re-process] (re-runs entire pipeline)
- Phase 1: Spatial filtering (new bbox)
- Phase 2: DXF extraction (new mappings)
- Phase 3: Validation
- Phase 4: Geometry generation
- Time: ~60 seconds (full pipeline)
```

---

## 🛠️ GUI Implementation Requirements

### Backend Scripts (Already Exist)
1. ✅ `find_main_building_bbox.py` - Spatial filtering
2. ✅ `dxf_to_database.py` - DXF extraction
3. ✅ `validate_dimensions.py` - Validation
4. ✅ `generate_3d_geometry.py` - Geometry generation

### New GUI Components Needed

**1. Project Manager**
```python
class ProjectManager:
    def create_project(name, dxf_folder, output_db):
        # Initialize project config
        pass

    def load_project(project_file):
        # Load existing .mbtp (Mini Bonsai Tree Project)
        pass

    def scan_dxf_folder(folder):
        # Discover all DXF files
        # Return list with file sizes, layer counts
        pass
```

**2. Layer Scanner**
```python
class LayerScanner:
    def scan_layers(dxf_path):
        # Returns: {layer_name: entity_count}
        pass

    def suggest_mappings(layers):
        # Uses smart_layer_mappings.json template
        # Returns: {layer: (discipline, ifc_class, confidence)}
        pass

    def detect_mep_disciplines(layers):
        # Scans for MEP keywords: bomba, ac, elec, mech, etc.
        # Returns: [FP, ACMV, ELEC, SP]
        pass
```

**3. Spatial Filter UI**
```python
class SpatialFilterWidget(QWidget):
    def __init__(self, dxf_path, reference_ifc=None):
        # Shows interactive map
        # User can drag bounding box
        # Real-time entity count preview
        pass

    def auto_detect_main_building():
        # Calls find_main_building_bbox.py
        # Returns suggested bbox
        pass

    def get_bbox():
        # Returns {min_x, max_x, min_y, max_y}
        pass
```

**4. Discipline Manager**
```python
class DisciplineManager:
    def add_discipline(name, color, layers):
        # Adds new discipline
        # Updates layer mappings
        pass

    def reassign_elements(from_discipline, to_discipline, layer_filter):
        # SQL: UPDATE elements_meta SET discipline=...
        pass

    def get_discipline_stats(db_path):
        # Returns: {discipline: element_count}
        pass
```

**5. Geometry Template Editor**
```python
class GeometryTemplateEditor(QWidget):
    def get_wall_settings():
        # Returns: {thickness, height, extract_length}
        pass

    def get_door_settings():
        # Returns: {default_sizes, extraction_method}
        pass

    def save_template(template_path):
        # Saves to JSON for reuse
        pass

    def load_template(template_path):
        # Airport, Office, Residential templates
        pass
```

**6. Pipeline Executor**
```python
class PipelineExecutor:
    def run_extraction(config):
        # Calls scripts in sequence
        # Emits progress signals for GUI
        pass

    def regenerate_geometry(db_path, template_settings):
        # Calls generate_3d_geometry.py with new params
        pass

    def update_disciplines_only(db_path, reassignments):
        # Fast SQL update
        pass
```

**7. 3D Preview Widget**
```python
class Preview3DWidget(QOpenGLWidget):
    def load_database(db_path):
        # Loads bounding boxes for quick preview
        pass

    def toggle_discipline(discipline, visible):
        # Show/hide discipline
        pass

    def get_element_info(element_guid):
        # Click element → show properties
        pass
```

---

## 📂 Project File Structure

```
Terminal1_Project/
├─ project.mbtp (Mini Bonsai Tree Project file)
│  {
│    "name": "Terminal 1 - 2D Conversion",
│    "dxf_folder": "/path/to/DXFs",
│    "output_db": "Terminal1_Converted.db",
│    "reference_ifc": "enhanced_federation.db",
│    "layer_mappings": "smart_layer_mappings.json",
│    "geometry_template": "airport_terminal.json",
│    "spatial_filter": {
│      "min_x": -1615047, "max_x": -1540489,
│      "min_y": 256576, "max_y": 309443
│    },
│    "disciplines": {
│      "Seating": {"color": [0.5, 0.7, 0.5], "layers": ["WALL", "DOOR", ...]},
│      "ACMV": {"color": [0.9, 0.7, 0.3], "layers": ["z-ac-pump", ...]}
│    }
│  }
│
├─ smart_layer_mappings.json (layer → discipline + IFC class)
├─ airport_terminal.json (geometry template settings)
├─ Terminal1_Converted.db (output database)
└─ Terminal1_Converted_full.blend (cached blend file)
```

---

## 🎯 Key Features Summary

| Feature | Status | Notes |
|---------|--------|-------|
| **DXF Folder Selection** | 📋 Planned | GUI browses folder, scans all DXF files |
| **Layer Auto-Detection** | ✅ Backend Ready | Can scan layers with ezdxf |
| **Smart Layer Mapping** | ✅ Template Exists | `smart_layer_mappings.json` |
| **Spatial Filter UI** | 📋 Planned | Interactive map, drag bbox |
| **Add/Edit Disciplines** | 📋 Planned | ACMV, SP, custom disciplines |
| **Geometry Template Config** | 📋 Planned | Wall/door/window size settings |
| **Pipeline Execution** | ✅ Scripts Ready | 4-phase pipeline functional |
| **Regenerate Modes** | ✅ Scripts Ready | Full/Geometry/Discipline modes |
| **3D Preview** | 📋 Planned | OpenGL widget for quick check |
| **Export to Blender** | ✅ Works | Database → Bonsai load |

---

## 📊 User Benefit

**Before (Manual Process):**
1. Find DXF files (scattered folders)
2. Manually edit layer mappings JSON
3. Run Python scripts from terminal (4 separate commands)
4. Check database in sqlite3 terminal
5. Manually adjust if wrong
6. Repeat extraction (60 seconds each time)
7. Load in Blender to verify

**After (Mini Bonsai Tree GUI):**
1. Open GUI → Select DXF folder
2. Review auto-detected mappings
3. Click [Process] (one button, 60 seconds)
4. Preview in GUI (embedded 3D viewer)
5. Adjust disciplines/templates (instant visual feedback)
6. Click [Regenerate] if needed (15 seconds, no re-extraction)
7. Click [Open in Blender] (automatic launch)

**Time Savings:** ~15 minutes → ~3 minutes per iteration
**User-Friendliness:** Terminal commands → Visual GUI
**Error Reduction:** Validation at each step with visual preview

---

## 🚀 Next Steps for GUI Development

### Phase 1: Core UI (Week 1-2)
- [ ] Project manager (create/load/save)
- [ ] DXF folder browser
- [ ] Layer scanner and mapping table
- [ ] Execute pipeline (progress bar)

### Phase 2: Discipline Management (Week 3)
- [ ] Discipline list widget
- [ ] Add/remove disciplines
- [ ] Layer reassignment UI
- [ ] Color picker per discipline

### Phase 3: Geometry Templates (Week 4)
- [ ] Template editor UI
- [ ] Load/save template presets
- [ ] Regenerate geometry with new settings

### Phase 4: Preview & Export (Week 5)
- [ ] 3D preview widget (OpenGL)
- [ ] Statistics dashboard
- [ ] Export to Blender integration

---

**Documentation:** This file
**Backend:** ✅ All scripts ready
**Frontend:** 📋 GUI implementation needed
**Timeline:** 5 weeks estimated
**Priority:** HIGH (user-facing feature for Mini Bonsai Tree)
