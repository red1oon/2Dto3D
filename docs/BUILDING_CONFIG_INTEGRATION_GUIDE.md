# Building Config Integration Guide

**For:** 2Dto3D Development Team
**Purpose:** How to use building_config.json in the workflow
**Status:** Topology preprocessing in development
**Date:** November 17, 2025

---

## Quick Start: What Is building_config.json?

**Purpose:** Master configuration file that drives the entire 2D→3D workflow

**Created by:** Topology preprocessing script (in development)
**Used by:** All generation scripts (dxf_to_database.py, generate_3d_geometry.py, master_routing.py)

**Analogy:** Think of it as the "DNA" of your building - contains all the intelligence needed to generate a complete BIM model from 2D DXF files.

---

## Why This Approach?

### Problem It Solves

**Before (Hardcoded):**
```python
# In code - hard to change
SPRINKLER_SPACING = 3.0
FLOOR_HEIGHT = 4.0
TARGET_FLOOR = "1F"
```

**After (Config-Driven):**
```json
// In building_config.json - easy to adjust
{
  "mep_strategy": {
    "FP": { "sprinkler_spacing": 3.0 }
  },
  "floor_levels": [
    { "level_id": "1F", "elevation": 0.0, "active": true }
  ]
}
```

**Benefits:**
- ✅ Change parameters without touching code
- ✅ Multi-building support (different configs per project)
- ✅ GUI integration ready (edit JSON → regenerate model)
- ✅ Version control friendly (see what changed)

---

## Current Config Structure (Nov 17, 2025)

### 1. Building Metadata
```json
{
  "building_info": {
    "name": "Terminal 1 Main Building",
    "building_type": "AIRPORT_TERMINAL",
    "total_floors": 7,
    "floor_to_floor_height": 4.0
  }
}
```

**Used by:** Header information, IFC project metadata

---

### 2. Floor Levels (Multi-Story Support)
```json
{
  "floor_levels": [
    {
      "level_id": "1F",
      "elevation": 0.0,
      "active": true,           // ← Only process active floors
      "is_poc_target": true,    // ← Primary test floor
      "dxf_sources": {
        "ARC": "SourceFiles/.../BANGUNAN TERMINAL 1.dxf",
        "STR": "SourceFiles/.../T1-2.1_Lyt_1FB_e1P1_240530.dxf"
      },
      "functional_zones": [
        "departure_hall",
        "check_in_counters",
        "retail_area"
      ]
    }
  ]
}
```

**Used by:**
- `dxf_to_database.py` - Which DXF files to load
- `generate_3d_geometry.py` - Z-height for element placement
- `master_routing.py` - Which floors to generate MEP for

---

### 3. MEP Strategies (Per Discipline)
```json
{
  "mep_strategy": {
    "FP": {
      "system_type": "wet_pipe_sprinkler",
      "sprinkler_spacing": 3.0,
      "branch_pipe_diameter": 0.025,
      "trunk_pipe_diameter": 0.1,
      "routing_strategy": "grid_with_corridor_trunks",
      "fixture_height_above_floor": 3.8
    },
    "ELEC": {
      "fixture_spacing": 6.0,
      "fixture_types": {
        "departure_hall": "LED_DOWNLIGHT_200W",
        "corridor": "LED_STRIP_100W"
      },
      "routing_strategy": "cable_tray_with_conduit_drops"
    }
  }
}
```

**Used by:**
- `code_compliance.py` - Spacing validation
- `intelligent_routing.py` - Pipe/conduit sizing and routing
- `master_routing.py` - Device generation parameters

---

### 4. POC Controls (Single Floor Mode)
```json
{
  "poc_config": {
    "mode": "single_floor",
    "target_floor": "1F",
    "active_disciplines": ["ARC", "STR", "FP", "ELEC"],
    "geometry_generation": {
      "floors": true,
      "mep_devices": true,
      "mep_routing": true
    }
  }
}
```

**Used by:** All scripts to determine what to generate

---

### 5. Spatial Infrastructure (Topology Results)
```json
{
  "spatial_infrastructure": {
    "vertical_shafts": [
      {
        "shaft_id": "SHAFT_01",
        "shaft_type": "MEP_RISER",
        "location": { "x": -50350.0, "y": 34200.0 },
        "serves_floors": ["GB", "1F", "2F", "3F"],
        "disciplines": ["FP", "SP", "ELEC"]
      }
    ],
    "mechanical_rooms": [...],
    "corridors": [...]  // To be populated by preprocessing
  }
}
```

**Used by:**
- `master_routing.py` - Vertical routing (connect floors)
- `corridor_detection.py` - Trunk line placement
- Future: Zone-based MEP distribution

---

## Integration Workflow

### Step 1: Preprocessing (Creates Config)

**Script:** `preprocess_building.py` (in development by other developer)

```bash
# Run topology analysis
python Scripts/preprocess_building.py \
    --dxf-dir SourceFiles/TERMINAL1DXF/ \
    --output building_config.json
```

**What it does:**
1. Analyzes DXF files (layers, blocks, dimensions)
2. Detects building topology (walls, corridors, rooms, shafts)
3. Infers building type (airport, office, residential, etc.)
4. Generates MEP strategies based on building type
5. Writes `building_config.json`

**Output:** `building_config.json` with all metadata populated

---

### Step 2: Read Config in Scripts

**In dxf_to_database.py:**
```python
import json

# Load config
with open('building_config.json') as f:
    config = json.load(f)

# Get active floor
target_floor = config['poc_config']['target_floor']
floor_config = next(f for f in config['floor_levels']
                    if f['level_id'] == target_floor)

# Get DXF sources
arc_dxf = floor_config['dxf_sources']['ARC']
str_dxf = floor_config['dxf_sources']['STR']

# Get elevation
z_height = floor_config['elevation']

# Process only active disciplines
active_disciplines = config['poc_config']['active_disciplines']
if 'FP' in active_disciplines:
    process_fp_elements(config['mep_strategy']['FP'])
```

---

**In generate_3d_geometry.py:**
```python
# Get floor height from config
floor_height = config['building_info']['floor_to_floor_height']

# Check if floors should be generated
if config['poc_config']['geometry_generation']['floors']:
    slab_thickness = floor_config['slab_thickness']
    generate_floor_slab(z_height=z_height, thickness=slab_thickness)
```

---

**In master_routing.py:**
```python
# Get MEP strategy for discipline
fp_strategy = config['mep_strategy']['FP']

# Use config values
sprinkler_spacing = fp_strategy['sprinkler_spacing']
routing_strategy = fp_strategy['routing_strategy']

# Generate devices
if routing_strategy == 'grid_with_corridor_trunks':
    corridors = config['spatial_infrastructure']['corridors']
    route_with_corridors(corridors, sprinkler_spacing)
```

---

### Step 3: Validate Against Config

**Example validation:**
```python
def validate_element_placement(elements, config):
    """Ensure generated elements match config expectations"""

    fp_strategy = config['mep_strategy']['FP']
    max_spacing = fp_strategy['sprinkler_spacing'] * 1.5  # 50% tolerance

    # Check spacing
    for e1, e2 in adjacent_pairs(elements):
        distance = calc_distance(e1, e2)
        if distance > max_spacing:
            warnings.append(f"Spacing violation: {distance}m > {max_spacing}m")

    # Check connectivity
    if config['poc_config']['validation']['require_connectivity']:
        if not all_connected(elements):
            errors.append("Disconnected elements found")

    return {'errors': errors, 'warnings': warnings}
```

---

## Current Implementation Status

### ✅ What's Working (Using Config)

**Files that read building_config.json:**
- None yet (config just created Nov 17)

**What needs updating:**
1. `dxf_to_database.py` - Read floor elevations, DXF sources
2. `generate_3d_geometry.py` - Read geometry generation flags
3. `code_compliance.py` - Read MEP spacing rules
4. `intelligent_routing.py` - Read routing strategies
5. `master_routing.py` - Read POC config, active disciplines

---

### 🚧 What's In Development

**Topology Preprocessing:**
- Wall adjacency graph detection
- Corridor detection (currently broken - finds 0, should find ~65)
- Room classification (functional zones)
- Shaft detection (from STR DXF ports)
- Building type inference

**Output:** Will populate `spatial_infrastructure` section of config

---

## Implementation Checklist

### For Topology Preprocessing Developer

- [ ] Implement WAG (Wall Adjacency Graph) algorithm
- [ ] Detect corridors (parallel walls, length > 5m, width 1.5-4m)
- [ ] Classify rooms by area and adjacency
- [ ] Detect vertical shafts (from STR DXF or room analysis)
- [ ] Infer building type (airport, office, residential)
- [ ] Generate default MEP strategies based on building type
- [ ] Write confidence scores for all detections
- [ ] Populate `spatial_infrastructure.corridors` in config
- [ ] Populate `spatial_infrastructure.vertical_shafts`
- [ ] Run validation (no orphan walls, corridors form network)

---

### For Main 2Dto3D Developer

- [ ] Add `load_config()` function to all scripts
- [ ] Update `dxf_to_database.py` to use `floor_levels[].dxf_sources`
- [ ] Update `generate_3d_geometry.py` to use `geometry_generation` flags
- [ ] Update `code_compliance.py` to use `mep_strategy.*.spacing`
- [ ] Update `intelligent_routing.py` to use `routing_strategy`
- [ ] Fix corridor detection (use config corridors if auto-detection fails)
- [ ] Add floor/slab generation (use `slab_thickness` from config)
- [ ] Implement trunk line routing (use corridors from config)
- [ ] Add config validation on load (schema check)
- [ ] Add config override mechanism (`--config path/to/custom.json`)

---

## Testing Strategy

### Unit Tests (Per Script)

```python
# test_config_loading.py
def test_load_config():
    config = load_building_config('building_config.json')
    assert config['building_info']['building_type'] == 'AIRPORT_TERMINAL'
    assert len(config['floor_levels']) == 7

def test_get_active_floor():
    floor = get_active_floor(config)
    assert floor['level_id'] == '1F'
    assert floor['active'] == True
```

---

### Integration Tests (Full Workflow)

```bash
# Test 1: Fresh generation from config
./abort_to_layer0.sh
python Scripts/master_routing.py BASE_ARC_STR.db \
    --config building_config.json \
    --discipline FP

# Expected: 273 sprinklers at 3.0m spacing (from config)

# Test 2: Override spacing via config edit
# Edit building_config.json: sprinkler_spacing → 4.0
./abort_to_layer0.sh
python Scripts/master_routing.py BASE_ARC_STR.db \
    --config building_config.json \
    --discipline FP

# Expected: Fewer sprinklers (wider spacing)
```

---

### Validation Tests

```python
def test_config_schema():
    """Ensure config has all required fields"""
    required_keys = [
        '_meta', 'building_info', 'floor_levels',
        'spatial_infrastructure', 'mep_strategy', 'poc_config'
    ]
    assert all(k in config for k in required_keys)

def test_floor_elevations():
    """Ensure floor elevations are sequential"""
    elevations = [f['elevation'] for f in config['floor_levels']]
    assert elevations == sorted(elevations)  # Must be ascending

def test_mep_strategy_complete():
    """Ensure all active disciplines have strategies"""
    active = config['poc_config']['active_disciplines']
    strategies = config['mep_strategy'].keys()
    assert all(d in strategies for d in active)
```

---

## GUI Integration (Future)

### Editable Parameters

**From config:**
```json
{
  "gui_config": {
    "adjustable_parameters": [
      "mep_strategy.FP.sprinkler_spacing",
      "mep_strategy.ELEC.fixture_spacing",
      "poc_config.target_floor",
      "poc_config.active_disciplines"
    ]
  }
}
```

**GUI mockup:**
```
┌─────────────────────────────────────────┐
│ Building Configuration                  │
├─────────────────────────────────────────┤
│ Target Floor:  [1F ▼]                   │
│                                         │
│ Fire Protection:                        │
│   Sprinkler Spacing: [3.0] m           │
│   Pipe Routing:      [Grid + Corridors]│
│                                         │
│ Electrical:                             │
│   Light Spacing:     [6.0] m           │
│   Fixture Type:      [LED Downlight ▼] │
│                                         │
│ [Generate Model]  [Reset to Defaults]  │
└─────────────────────────────────────────┘
```

**Workflow:**
1. GUI reads `building_config.json`
2. User adjusts sliders/dropdowns
3. GUI writes updated JSON
4. Click "Generate Model" → runs layer scripts with new config

---

## Common Patterns

### Pattern 1: Get Active Floor Config

```python
def get_active_floor_config(config):
    """Get the floor marked as POC target"""
    target = config['poc_config']['target_floor']
    return next(f for f in config['floor_levels']
                if f['level_id'] == target)
```

---

### Pattern 2: Check If Feature Enabled

```python
def should_generate_floors(config):
    """Check if floor geometry generation is enabled"""
    return config['poc_config']['geometry_generation'].get('floors', False)
```

---

### Pattern 3: Get MEP Parameters

```python
def get_mep_params(config, discipline):
    """Get MEP strategy for a discipline"""
    if discipline not in config['mep_strategy']:
        raise ValueError(f"No MEP strategy for {discipline}")
    return config['mep_strategy'][discipline]

# Usage
fp_params = get_mep_params(config, 'FP')
spacing = fp_params['sprinkler_spacing']
```

---

### Pattern 4: Merge Auto-Detected with Config

```python
def merge_corridors(config, detected_corridors):
    """
    Use auto-detected corridors, but allow config overrides
    """
    config_corridors = config['spatial_infrastructure'].get('corridors', [])

    # Start with auto-detected
    corridors = detected_corridors.copy()

    # Override with manual corrections from config
    for manual in config_corridors:
        if manual.get('force_include'):
            corridors.append(manual)

    return corridors
```

---

## Error Handling

### Config Validation on Load

```python
def load_and_validate_config(path):
    """Load config with validation"""
    try:
        with open(path) as f:
            config = json.load(f)
    except FileNotFoundError:
        raise ConfigError(f"Config not found: {path}")
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON: {e}")

    # Schema validation
    validate_schema(config)

    # Business logic validation
    validate_floors(config)
    validate_mep_strategies(config)

    return config

def validate_schema(config):
    """Ensure all required keys present"""
    required = ['_meta', 'building_info', 'floor_levels', 'mep_strategy']
    missing = [k for k in required if k not in config]
    if missing:
        raise ConfigError(f"Missing required keys: {missing}")

def validate_floors(config):
    """Ensure at least one active floor"""
    active_floors = [f for f in config['floor_levels'] if f.get('active')]
    if not active_floors:
        raise ConfigError("No active floors defined")
```

---

## Migration Path (Hardcoded → Config)

### Before (Hardcoded in code)
```python
# code_compliance.py
SPRINKLER_SPACING = 3.0  # meters
MAX_COVERAGE = 12.08  # m²

# generate_3d_geometry.py
FLOOR_HEIGHT = 4.0  # meters

# master_routing.py
ACTIVE_DISCIPLINES = ['ARC', 'STR', 'FP', 'ELEC']
```

---

### After (Config-driven)
```python
# Load config once at module level
with open('building_config.json') as f:
    CONFIG = json.load(f)

# code_compliance.py
fp_strategy = CONFIG['mep_strategy']['FP']
SPRINKLER_SPACING = fp_strategy['sprinkler_spacing']
MAX_COVERAGE = fp_strategy['max_coverage_per_head']

# generate_3d_geometry.py
FLOOR_HEIGHT = CONFIG['building_info']['floor_to_floor_height']

# master_routing.py
ACTIVE_DISCIPLINES = CONFIG['poc_config']['active_disciplines']
```

---

### Migration Checklist

- [ ] Identify all hardcoded parameters
- [ ] Add to building_config.json (with defaults)
- [ ] Replace hardcoded values with `CONFIG['path']['to']['value']`
- [ ] Add validation tests
- [ ] Update documentation
- [ ] Test with different config values

---

## Next Steps (Priority Order)

### Week 1: Basic Config Integration
1. Add `load_config()` to all scripts
2. Use `poc_config.active_disciplines` filter
3. Use `floor_levels[].elevation` for Z-heights
4. Test: Can change target floor via config

---

### Week 2: MEP Strategy Integration
1. Use `mep_strategy.*.spacing` in code_compliance.py
2. Use `routing_strategy` in intelligent_routing.py
3. Use `pipe_diameters` for hierarchical sizing
4. Test: Can change spacing via config

---

### Week 3: Topology Integration
1. Implement corridor detection (populate config)
2. Use detected corridors in routing
3. Implement shaft detection
4. Test: Trunk lines follow corridors from config

---

### Week 4: Validation & Polish
1. Add config schema validation
2. Add confidence scoring
3. Implement override mechanisms
4. Write comprehensive tests
5. Document all config fields

---

## Conclusion

**building_config.json is the future of 2Dto3D.**

**Benefits:**
- ✅ Separation of data (JSON) and logic (Python)
- ✅ Multi-project scalability
- ✅ GUI integration readiness
- ✅ Version control friendly
- ✅ Testability (same config = same output)

**Next Action:**
- Topology developer: Implement corridor detection → populate config
- Main developer: Integrate config loading into all scripts

**Questions?** Check full research report: `docs/RESEARCH_2D_TO_3D_APPROACHES.md`

---

**Document Version:** 1.0
**Last Updated:** November 17, 2025
**Maintainer:** Development Team
