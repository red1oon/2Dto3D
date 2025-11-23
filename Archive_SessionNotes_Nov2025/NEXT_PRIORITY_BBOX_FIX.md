# NEXT PRIORITY: Fix Element Bounding Boxes

**Date:** 2025-11-18
**Status:** Terminal 1 (dome) correctly extracted, but elements showing as 1m cubes
**User Request:** "Get the blocks properly sized instead of just cubes"

## Current Situation

✅ **COMPLETED TODAY:**
- Terminal 1 (dome building) correctly identified and extracted
- 2,152 IfcPlate elements (THE DOME!) now in database
- ARC bounds: X=[-1.62M, -1.56M], Y=[-90K, -40K] (245 walls, 178 roof)
- STR bounds: X=[342K, 402K], Y=[-336K, -296K] (432 beams - exact IFC match)
- GPS alignment working: ARC/STR centers within 0.3m
- Blender baseline screenshot confirms good 3D visualization

❌ **REMAINING ISSUE:**
- All elements use default dimensions: 1m × 1m × 3.5m (hardcoded)
- Elements appear as uniform cubes instead of actual geometry shapes
- Bbox not calculated from DXF geometry

## The Fix Required

### 1. Update Database Schema
Add bbox columns to `element_transforms` table:
```sql
ALTER TABLE element_transforms ADD COLUMN bbox_min_x REAL;
ALTER TABLE element_transforms ADD COLUMN bbox_min_y REAL;
ALTER TABLE element_transforms ADD COLUMN bbox_min_z REAL;
ALTER TABLE element_transforms ADD COLUMN bbox_max_x REAL;
ALTER TABLE element_transforms ADD COLUMN bbox_max_y REAL;
ALTER TABLE element_transforms ADD COLUMN bbox_max_z REAL;
```

### 2. Update BuildingElement Dataclass
File: `Scripts/generate_base_arc_str_multifloor.py` lines 76-78

Current:
```python
length: float = 1.0  # ← HARDCODED DEFAULT
width: float = 1.0   # ← HARDCODED DEFAULT
height: float = 3.5  # ← HARDCODED DEFAULT
```

Need to add:
```python
bbox_min_x: float = 0.0
bbox_min_y: float = 0.0
bbox_min_z: float = 0.0
bbox_max_x: float = 1.0
bbox_max_y: float = 1.0
bbox_max_z: float = 3.5
```

### 3. Calculate Bbox During Parsing

**Location 1:** STR parsing (lines 650-710)
```python
# When extracting STR entities, calculate bbox from geometry
if entity.dxftype() == 'LWPOLYLINE':
    points = list(entity.get_points('xy'))
    if points:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        bbox_min_x, bbox_max_x = min(xs), max(xs)
        bbox_min_y, bbox_max_y = min(ys), max(ys)
        # Store in element
```

**Location 2:** ARC template parsing (lines 450-500)
- Same logic when building arc_template_entities
- Store bbox in template dict

**Location 3:** ARC replication (lines 716-739)
- Copy bbox from template when replicating

### 4. Database Population

Update `populate_database()` method to write bbox columns:
```python
INSERT INTO element_transforms (
    guid, center_x, center_y, center_z,
    bbox_min_x, bbox_min_y, bbox_min_z,
    bbox_max_x, bbox_max_y, bbox_max_z,
    transform_source
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

## Expected Result

After fix:
- Walls: Actual wall thickness (~0.2m) and length (varies)
- Beams: Actual beam dimensions (~0.3m × 0.6m cross-section, length varies)
- Columns: Actual column size (~0.4m × 0.4m)
- Roof plates: Actual panel dimensions (varies per panel)
- **Realistic 3D visualization in Blender** instead of uniform cubes

## Test Plan

1. Regenerate database with bbox fix
2. Load in Blender 4.2.14
3. Verify elements have realistic sizes (not all 1m cubes)
4. Check if "Full Load" issue resolves (might be related to missing bbox)

---

**Next Developer:** Start here! This is the #1 priority confirmed by user.
