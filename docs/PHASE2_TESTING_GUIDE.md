# Phase 2 Testing Guide - Shape Realism Improvement

**Database:** `Terminal1_MainBuilding_FILTERED.db`
**Status:** Ready for testing
**Expected improvement:** Realistic varied dimensions vs uniform defaults

---

## 🎯 What to Test

You should see **significant improvement** in shape realism compared to Phase 1:

### Expected Changes:

#### Walls:
- **Before:** All walls 1m length (uniform, abstract)
- **After:** Walls 0.5m to 11m (varied, realistic floor plan)
- **Coverage:** 99.1% with measured dimensions

#### Windows:
- **Before:** All windows 1.2m width (uniform)
- **After:** Varied window sizes from DXF blocks
- **Coverage:** 100% with measured dimensions

#### Columns:
- **Before:** All columns 400mm diameter (uniform)
- **After:** Varied column sizes (300mm to 1.5m)
- **Coverage:** 100% with measured dimensions

#### Overall:
- **Dimension accuracy:** 10% → 89.7%
- **Unique wall lengths:** 1 → 127 different sizes
- **Floor plan match:** Should closely match original DXF

---

## 📋 Testing Checklist

### 1. Load Database in Blender

```bash
# Open Blender with Bonsai
~/blender-4.2.14/blender

# In Bonsai Federation Panel:
# 1. Click "Load Database"
# 2. Select: Terminal1_MainBuilding_FILTERED.db
# 3. Click "Full Load" (not Preview - we want to see actual geometry)
```

**Expected:**
- ✅ All 1,185 elements load successfully
- ✅ No errors in console
- ✅ Building appears in viewport

### 2. Visual Inspection - Overall Layout

**What to look for:**
- [ ] Floor plan should be **recognizable** (not abstract)
- [ ] Walls should show **length variety** (short segments, long corridors)
- [ ] Building proportions should **match DXF** layout
- [ ] No obvious geometric errors or missing elements

**Navigation tips:**
- Use middle mouse to rotate view
- Use scroll wheel to zoom
- Press numpad 7 for top view (best for floor plan comparison)

### 3. Wall Inspection (99.1% coverage)

**Top view (numpad 7):**
- [ ] Walls show **varied lengths** (not all uniform)
- [ ] Long corridor walls (6-11m) visible
- [ ] Short wall segments (0.5-2m) visible
- [ ] Wall layout matches DXF floor plan

**Expected observations:**
- Corridors: Long walls (7-11m)
- Rooms: Medium walls (3-5m)
- Partitions: Short walls (0.5-2m)

**How to verify:**
- Select a wall → Properties panel shows length
- Compare multiple walls → should see different sizes
- Overlay DXF in background → walls should align

### 4. Window Inspection (100% coverage)

**What to check:**
- [ ] Windows show **varied sizes** (not all 1.2m)
- [ ] Window proportions look realistic
- [ ] Windows positioned at correct height (1m above floor)

**Select a window:**
- Check dimensions in properties
- Should see varied widths (0.9m, 1.2m, 1.5m, etc.)

### 5. Column Inspection (100% coverage)

**What to check:**
- [ ] Columns show **size variety**
- [ ] Some rectangular (e.g., 1.2m × 0.3m)
- [ ] Some larger (e.g., 1.65m × 1.05m)
- [ ] Columns appear cylindrical or rectangular as appropriate

**Note:** Columns rendered as cylinders (12 segments)

### 6. Comparison with Phase 1 (Optional)

If you have Phase 1 blend file saved:

**Open side-by-side:**
1. Open Phase 1: `Terminal1_MainBuilding_FILTERED_full.blend` (old)
2. Open Phase 2: Load fresh from database (new)

**Compare:**
- [ ] Phase 2 walls show more variety than Phase 1
- [ ] Phase 2 layout more recognizable
- [ ] Phase 2 proportions closer to DXF

### 7. Discipline Filtering Test

**Test discipline visibility:**
1. Hide/unhide Architecture (ARC) → Should see walls/doors/windows
2. Hide/unhide Structure (STR) → Should see columns
3. Hide/unhide Fire Protection (FP) → Should see FP equipment

**Expected:**
- ✅ All disciplines still work correctly
- ✅ Geometry visible when discipline enabled
- ✅ No missing elements

---

## 📊 Quick Statistics Check

**In Blender Python console:**

```python
import bpy
import sqlite3

# Connect to database
db_path = "/home/red1/Documents/bonsai/2Dto3D/Terminal1_MainBuilding_FILTERED.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check dimension coverage
cursor.execute("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN dimensions IS NOT NULL THEN 1 ELSE 0 END) as with_dims
    FROM elements_meta
""")
total, with_dims = cursor.fetchone()
print(f"Dimension coverage: {with_dims}/{total} ({with_dims/total*100:.1f}%)")

# Check wall length variety
cursor.execute("""
    SELECT
        COUNT(DISTINCT ROUND(json_extract(dimensions, '$.length'), 1))
    FROM elements_meta WHERE ifc_class = 'IfcWall'
""")
unique_walls = cursor.fetchone()[0]
print(f"Unique wall lengths: {unique_walls}")

conn.close()
```

**Expected output:**
```
Dimension coverage: 1063/1185 (89.7%)
Unique wall lengths: 127
```

---

## ✅ Success Criteria

Phase 2 is successful if:

- [ ] **Floor plan recognizable** - Looks like actual building (not abstract)
- [ ] **Wall variety visible** - Different lengths clearly apparent
- [ ] **Proportions realistic** - Matches DXF layout
- [ ] **No errors** - All elements load without crashes
- [ ] **Dimension coverage >70%** - Already achieved 89.7% ✅
- [ ] **User satisfaction** - "Looks like the building!" (vs "valid but simple")

---

## 🐛 Troubleshooting

### Issue: Database not found
**Solution:**
```bash
cd /home/red1/Documents/bonsai/2Dto3D
ls -la Terminal1_MainBuilding_FILTERED.db  # Verify exists
```

### Issue: Geometry looks same as Phase 1
**Possible causes:**
1. Loaded wrong database (old Phase 1 version)
2. Blend cache loading instead of fresh generation
3. Preview mode instead of Full Load

**Solution:**
- Delete blend cache: `rm Terminal1_MainBuilding_FILTERED_*.blend`
- Full Load again (generates fresh from database)
- Check database timestamp (should be Nov 17, 2025)

### Issue: Some walls still look uniform
**Expected behavior:**
- 10.3% elements use defaults (no DXF dimension data)
- Mostly IfcBuildingElementProxy and some doors
- Walls should be 99.1% varied

**Check:**
```sql
sqlite3 Terminal1_MainBuilding_FILTERED.db
SELECT COUNT(*) FROM elements_meta
WHERE ifc_class = 'IfcWall' AND dimensions IS NULL;
-- Should return 3 (only 3 walls without dimensions)
```

### Issue: Dimensions look extreme (too small/large)
**Safety:** Dimension clamping should prevent this
- Walls: 0.1m to 50m
- Doors: 0.5m to 3m
- Windows: 0.3m to 5m
- Columns: 0.2m to 2m

**If you see violations:**
- Report specific element GUID
- Include dimensions value from database

---

## 📝 Feedback Template

**Please provide feedback:**

### Visual Quality:
- Does the floor plan look like the actual building? (Yes/No)
- Are wall lengths varied and realistic? (Yes/No)
- Do proportions match the DXF? (Yes/No)

### Specific Observations:
- What looks good?
- What needs improvement?
- Any obvious errors?

### Comparison to Phase 1:
- Better / Same / Worse?
- Specific improvements noticed?

### Overall Rating:
- Phase 1: "Valid but simple" (baseline)
- Phase 2: "___________________" (your assessment)

---

## 🎯 Next Steps After Testing

### If Successful:
1. Proceed with Mini Bonsai Tree GUI integration
2. Consider Phase 3 enhancements (door swing, wall thickness)
3. Document workflow for other buildings

### If Issues Found:
1. Report specific problems with GUIDs
2. Provide screenshots if helpful
3. Check database queries for dimension quality

---

**Testing Time:** ~15 minutes
**Database:** Terminal1_MainBuilding_FILTERED.db (1.2MB)
**Elements:** 1,185 with 89.7% dimension coverage
**Status:** Ready for testing ✅

Good luck with testing! The improvement should be very noticeable compared to Phase 1.
