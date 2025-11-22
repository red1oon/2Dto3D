# 2D Drawing → 3D Blender Builder

**Purpose:** AI reads 2D architectural drawings → Fills checklist → Scripts automatically build 3D model

**Philosophy:** AI identifies symbols. Scripts do construction. No manual AI implementation.

---

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INPUT: 2D Drawing (PDF/DXF)                              │
│    - Scanned floor plans                                    │
│    - Architectural drawings                                 │
└────────────────┬────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. AI ROLE: Symbol Identification → Fill Checklist         │
│    - "What's this symbol?" → Switch                         │
│    - "Where is it?" → (4.8, 0.05, 1.2)                     │
│    - "What type?" → 1-gang                                  │
│    Output: TEMPLATE_CONFIGURATOR_EXAMPLE.json               │
└────────────────┬────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. SCRIPT ROLE: Read Checklist → Build 3D Automatically    │
│    - Load IFC LOD300 objects from library                   │
│    - Position based on coordinates                          │
│    - Rotate based on nearest wall                           │
│    - Validate placement                                     │
│    Output: .blend file                                      │
└────────────────┬────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. HUMAN ROLE: Review & Iterate                            │
│    - Check 3D model in Blender                              │
│    - If wrong: Edit checklist JSON, re-run script           │
│    - NO CODE CHANGES needed for normal use                  │
└─────────────────────────────────────────────────────────────┘
```

---

## AI Role: "Cook Following Recipe"

**What AI does:**
- Read 2D drawing (PDF/image)
- Identify symbols: "This is a switch", "This is a door"
- Extract positions: "Switch at grid C2, 1.2m high"
- Fill checklist JSON with findings

**What AI does NOT do:**
- Write positioning algorithms ✗
- Calculate rotation manually ✗
- Debug Blender object placement ✗
- Implement builders/loaders ✗

**AI is the data entry clerk, not the construction crew.**

---

## Script Role: "Automated Construction"

**What scripts do:**
```python
# Read checklist
checklist = json.load("TEMPLATE_CONFIGURATOR_EXAMPLE.json")

# For each item in checklist:
for switch in checklist['electrical']['switches']:
    # 1. Load object from library (automatic)
    obj = library.get('switch_1gang_lod300')

    # 2. Position (automatic)
    obj.location = switch['position']

    # 3. Rotate based on nearest wall (automatic)
    wall = matrix.find_nearest_wall(obj.location)
    obj.rotation = matrix.calculate_rotation(wall)

    # Done. No AI involvement.
```

**Scripts handle:**
- Object loading
- Positioning
- Rotation calculation
- Validation
- All construction logic

---

## Checklist Format (The Truth)

`TEMPLATE_CONFIGURATOR_EXAMPLE_TB_LKTN.json` is the SINGLE SOURCE OF TRUTH:

```json
{
  "structure": {
    "floor": {"dimensions": {"length_m": 9.9, "width_m": 8.5}},
    "walls": [
      {"name": "south_wall", "start": [0, 0, 0], "end": [9.9, 0, 2.7]}
    ]
  },
  "doors": [
    {
      "name": "Main entrance",
      "position": [4.95, 0.05, 0],
      "dimensions": {"width_m": 0.9, "height_m": 2.1},
      "type": "D2"
    }
  ],
  "electrical": {
    "switches": [
      {
        "name": "Living room switch",
        "position": [4.8, 0.05, 1.2],
        "type": "1-gang"
      }
    ]
  }
}
```

**To add object:** Edit JSON, re-run script. That's it.

---

## Current Status

### What Works ✅
- AI reads drawings → fills checklist (manual for now)
- Scripts read checklist → load LOD300 objects
- Switches/outlets rotate correctly (face into room)
- Objects positioned correctly

### What's Broken ❌
- Doors/windows/basins don't rotate (script bug - NOT AI's job to fix)
- Missing WCs in library mapping (config issue - one line fix)
- Missing curved drains (library lookup issue)

### Why Broken?
**Code uses 5 different creation methods:**
- `create_wall_mounted_with_matrix()` - Works! Has rotation ✅
- `create_door()` - Broken, no rotation ✗
- `create_window()` - Broken, no rotation ✗
- `create_plumbing_object()` - Broken, no rotation ✗

**Should be ONE method that handles everything.**

---

## File Structure

```
TEMPLATE_CONFIGURATOR_EXAMPLE_TB_LKTN.json  ← AI fills this (INPUT)
    ↓
blender_template_adjuster.py                 ← Reads checklist, builds model
    ↓ uses
library_access.py                            ← Loads LOD300 objects from DB
spatial_configuration_matrix.py              ← Calculates rotation from walls
    ↓ outputs
TB_LKTN_v8_AllLOD300.blend                  ← 3D Blender model (OUTPUT)
```

**Database:**
- `Ifc_Object_Library.db` - LOD300 object geometry (vertices, faces)

---

## How to Use

### Step 1: AI Fills Checklist (or manual for POC)
```bash
# AI reads drawing:
# "I see a switch symbol at grid B1, 1.2m height"

# AI fills checklist:
{
  "electrical": {
    "switches": [
      {"position": [1.5, 0.05, 1.2], "type": "1-gang"}
    ]
  }
}
```

### Step 2: Run Script
```bash
~/blender-4.2.14/blender --background --python run_builder.py
```

### Step 3: Review Result
```bash
~/blender-4.2.14/blender output.blend
# Check if objects positioned correctly
# If wrong: Edit JSON, re-run script
```

### Step 4: Iterate
```bash
# Edit checklist JSON (fix position/type)
# Re-run script
# Check again
# Repeat until correct
```

**NO CODE CHANGES for normal workflow.**

---

## Configuration Files (AI Fills These)

### Tables/Settings AI Configures:

1. **Checklist JSON** - Object inventory and positions
2. **Library mapping** - Which LOD300 object to use for each type
3. **Room envelope** - Building bounds for validation

### AI Does NOT Configure:

- Positioning algorithms
- Rotation calculation logic
- Blender API calls
- Database queries

---

## Rules

### Rule 1: Tables Are Truth
- Checklist JSON is source of truth
- Scripts read tables, build accordingly
- To change model: Edit JSON, not code

### Rule 2: AI = Symbol Reader
- AI identifies: "This is a switch at (X, Y, Z)"
- AI fills: Checklist JSON
- AI does NOT: Write construction logic

### Rule 3: Scripts = Builders
- Scripts read checklist automatically
- Scripts handle ALL construction logic
- Scripts should work without AI once checklist is filled

### Rule 4: One Method, Not Five
- Should be ONE universal `create_object()` method
- Current mess: 5 different methods, inconsistent behavior
- Fix by consolidating, not patching

---

## Required Fixes (Script Issues, Not AI)

### Fix 1: Consolidate Object Creation

**Problem:** 5 methods, only 1 works correctly

**Solution:** Create ONE method:
```python
def create_object(self, name, obj_type, position, height=None):
    """Universal object creator - handles ALL objects"""
    # Load from library
    obj = self.library.get(obj_type)

    # Position
    obj.location = position

    # Rotate (using matrix - works for switches)
    if self.matrix:
        wall = self.matrix.find_nearest_wall(position)
        obj.rotation_euler.z = self.matrix.calculate_rotation(wall)

    return obj
```

Replace all 5 methods with this ONE.

---

### Fix 2: Complete Library Mapping

**Problem:** Some object types not mapped to library

**Solution:** Update config (line 567):
```python
self.library_type_map = {
    'switch': 'switch_1gang_lod300',
    'power_outlet': 'outlet_3pin_ms589_lod300',
    'basin': 'wall_mounted_basin_lod300',
    'wc': 'toilet_residential_lod300',        # ADD
    'door': 'door_single_900_lod300',
    'window': 'window_aluminum_2panel_1200x1000_lod300',
    'floor_drain': 'floor_drain_lod300',
    'discharge_drain': 'discharge_drain_lod300',  # ADD
}
```

---

## Success Criteria

### For AI:
✅ Reads 2D drawing
✅ Identifies symbols correctly (>95% accuracy)
✅ Fills checklist JSON with correct positions

### For Scripts:
✅ Reads checklist JSON
✅ Loads all objects from library
✅ Positions objects at specified coordinates
✅ Rotates objects based on nearest wall (ALL objects, not just switches)
✅ Validates placement (objects inside envelope)

### For Human:
✅ Reviews 3D model
✅ Edits checklist if needed
✅ Re-runs script
✅ Gets correct result

**No coding required for normal workflow.**

---

## Philosophy Summary

**OLD WAY (Wrong):**
- AI implements everything
- Manual positioning/rotation for each object
- Different code paths for each object type
- Hours of AI debugging placement

**NEW WAY (Correct):**
- AI: "Switch at (4.8, 0.05, 1.2)" → Fills JSON
- Script: Reads JSON → Builds automatically
- Human: Reviews → Edits JSON if needed → Re-runs
- ONE code path for ALL objects

**AI is data entry. Scripts are construction. Humans are supervisors.**

---

*This README documents the SYSTEM, not implementation details.*
*For code details, read the code itself.*
*For usage, follow the workflow above.*
