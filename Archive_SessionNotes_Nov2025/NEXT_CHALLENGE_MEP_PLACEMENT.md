# Next Challenge: Place ALL MEP & Building Elements

**Current:** Sprinklers working (273 grid) ✅
**Next:** HVAC, Toilets, Seating, and all other elements

---

## 📊 Current Database Status

```sql
-- What we have now:
ARC   IfcWall                      347
ARC   IfcDoor                      265
ARC   IfcWindow                     80
ARC   IfcBuildingElementProxy      219  (old - misc)
ELEC  IfcCableCarrierSegment       104
FP    IfcPipeSegment               867
FP    IfcBuildingElementProxy      273  (generated sprinklers) ✅
STR   IfcColumn                     29
STR   IfcSlab                        1

MISSING:
❌ HVAC/ACMV diffusers
❌ Toilets
❌ Seating
❌ Lights (ELEC)
❌ Smoke detectors (FP)
❌ Emergency lights (ELEC)
❌ Electrical outlets
```

---

## 🎯 Challenge: Add Standards for All Element Types

### **Already Working (Sprinklers):**
```python
PLACEMENT_STANDARDS = {
    ('sprinkler', 'FP'): PlacementStandards(
        element_type='sprinkler',
        discipline='FP',
        code_reference='NFPA 13 (Light Hazard)',
        min_spacing=1.83,
        max_spacing=4.572,
        optimal_spacing=3.5,
        max_coverage_area=12.08,
        optimal_coverage_area=10.0,
        max_wall_distance=2.29,
        min_wall_clearance=0.15
    ),
}
```

### **Need to Add (Next):**

#### **1. HVAC Diffusers (ACMV)**
```python
('hvac_diffuser', 'ACMV'): PlacementStandards(
    element_type='hvac_diffuser',
    discipline='ACMV',
    code_reference='ASHRAE 62.1 + Local ACMV Standards',
    min_spacing=3.0,           # 3m minimum between diffusers
    max_spacing=8.0,           # 8m maximum coverage
    optimal_spacing=5.0,       # Standard office spacing
    max_coverage_area=25.0,    # 25 m² per diffuser
    optimal_coverage_area=20.0,
    max_wall_distance=4.0,
    min_wall_clearance=0.5,
    strategy='grid'            # Even distribution
),
```

#### **2. Toilets (Architecture - Perimeter)**
```python
('toilet', 'ARC'): PlacementStandards(
    element_type='toilet',
    discipline='ARC',
    code_reference='IBC / Local Building Code',
    min_spacing=1.5,           # 1.5m minimum between toilets
    max_spacing=None,          # Not applicable (perimeter placement)
    optimal_spacing=2.0,       # 2m spacing along walls
    max_coverage_area=None,    # Not applicable
    optimal_coverage_area=None,
    max_wall_distance=0.5,     # Must be against walls
    min_wall_clearance=0.1,
    strategy='perimeter'       # Along walls, not grid
),
```

#### **3. Seating (Architecture - Grid/Rows)**
```python
('seat', 'ARC'): PlacementStandards(
    element_type='seat',
    discipline='ARC',
    code_reference='Airport Terminal Design Standards',
    min_spacing=0.6,           # 600mm seat width minimum
    max_spacing=None,
    optimal_spacing=0.65,      # Standard seat spacing
    max_coverage_area=None,
    optimal_coverage_area=None,
    max_wall_distance=None,
    min_wall_clearance=1.5,    # Circulation space
    strategy='rows'            # Seating in rows (new strategy)
),
```

#### **4. Lights (ELEC - Grid)**
```python
('light_fixture', 'ELEC'): PlacementStandards(
    element_type='light_fixture',
    discipline='ELEC',
    code_reference='NEC 210.70 + IES Standards',
    min_spacing=2.0,
    max_spacing=6.0,
    optimal_spacing=4.0,       # Standard office spacing
    max_coverage_area=16.0,
    optimal_coverage_area=14.0,
    max_wall_distance=3.0,
    min_wall_clearance=0.3,
    strategy='grid'
),
```

---

## 🏗️ Implementation Steps

### **Step 1: Add Standards to code_compliance.py**

```python
# Edit: Scripts/code_compliance.py

PLACEMENT_STANDARDS = {
    ('sprinkler', 'FP'): {...},  # Already exists ✅

    # Add these:
    ('hvac_diffuser', 'ACMV'): PlacementStandards(...),
    ('light_fixture', 'ELEC'): PlacementStandards(...),
    ('toilet', 'ARC'): PlacementStandards(...),
    ('seat', 'ARC'): PlacementStandards(...),
    ('smoke_detector', 'FP'): PlacementStandards(...),
    ('emergency_light', 'ELEC'): PlacementStandards(...),
    ('outlet', 'ELEC'): PlacementStandards(...),
}
```

### **Step 2: Update IFC Class Mapping**

```python
# Edit: Scripts/code_compliance.py - PlacementGenerator class

ELEMENT_IFC_MAP = {
    'sprinkler': 'IfcBuildingElementProxy',  # Already exists ✅

    # Add these:
    'hvac_diffuser': 'IfcFlowTerminal',
    'light_fixture': 'IfcLightFixture',
    'toilet': 'IfcSanitaryTerminal',
    'seat': 'IfcFurniture',
    'smoke_detector': 'IfcSensor',
    'emergency_light': 'IfcLightFixture',
    'outlet': 'IfcOutlet',
}
```

### **Step 3: Test One Element Type at a Time**

```bash
# Test HVAC diffusers
python3 Scripts/master_routing.py Terminal1.db \
    --discipline ACMV \
    --device-type hvac_diffuser \
    --generate-devices

# Test lights
python3 Scripts/master_routing.py Terminal1.db \
    --discipline ELEC \
    --device-type light_fixture \
    --generate-devices
```

---

## 🚀 Quick Start: Add HVAC Diffusers (First)

### **1. Add to PLACEMENT_STANDARDS**
Edit `Scripts/code_compliance.py` line ~96:

```python
('hvac_diffuser', 'ACMV'): PlacementStandards(
    element_type='hvac_diffuser',
    discipline='ACMV',
    code_reference='ASHRAE 62.1',
    min_spacing=3.0,
    max_spacing=8.0,
    optimal_spacing=5.0,
    max_coverage_area=25.0,
    optimal_coverage_area=20.0,
    max_wall_distance=4.0,
    min_wall_clearance=0.5
),
```

### **2. Add to ELEMENT_IFC_MAP**
Edit `Scripts/code_compliance.py` line ~138:

```python
ELEMENT_IFC_MAP = {
    'sprinkler': 'IfcBuildingElementProxy',
    'light_fixture': 'IfcBuildingElementProxy',
    'hvac_diffuser': 'IfcFlowTerminal',  # Add this
    'smoke_detector': 'IfcBuildingElementProxy',
}
```

### **3. Update master_routing.py device_type_map**
Edit `Scripts/master_routing.py` line ~420:

```python
device_type_map = {
    'FP': 'sprinkler',
    'ELEC': 'light_fixture',
    'HVAC': 'hvac_diffuser',  # Add this
    'ACMV': 'hvac_diffuser',  # Add this (alias)
    'PLB': 'sink'
}
```

### **4. Generate Fresh DB and Test**

```bash
# Clean start
rm -f Fresh_Terminal1_Test.db
cp Terminal1_MainBuilding_FILTERED.db Fresh_Terminal1_Test.db

# Generate HVAC diffusers
python3 Scripts/master_routing.py Fresh_Terminal1_Test.db \
    --discipline HVAC \
    --generate-devices

# Check results
sqlite3 Fresh_Terminal1_Test.db "
SELECT 'HVAC Diffusers:', COUNT(*)
FROM elements_meta
WHERE element_name='Generated_hvac_diffuser';
"
```

### **5. Test in Viewport**
```bash
# Delete old blend
rm -f Fresh_Terminal1_Test_full.blend

# Open in Blender
~/blender-4.5.3/blender
# File → Import → Fresh_Terminal1_Test.db

# Filter to see: element_name = 'Generated_hvac_diffuser'
```

---

## 📐 Special Cases

### **Toilets (Perimeter Placement)**

Need NEW strategy - `PerimeterPlacement`:
- Place along walls (not grid)
- Face outward from walls
- Respect door clearances
- Group in restroom areas

**Implementation:**
```python
class PerimeterPlacement(PlacementStrategy):
    def generate(self, room_bounds, standards):
        # Find walls
        # Place elements along perimeter
        # Maintain spacing from corners/doors
        # Return positions + rotations
```

### **Seating (Row Placement)**

Need NEW strategy - `RowPlacement`:
- Arrange in rows
- Face specific direction (gates, etc.)
- Account for circulation aisles
- Different spacing: seat-to-seat vs row-to-row

**Implementation:**
```python
class RowPlacement(PlacementStrategy):
    def generate(self, room_bounds, standards, direction='facing_center'):
        # Create rows
        # Space seats within rows
        # Add circulation between rows
        # Return positions + rotations
```

---

## 🎯 Priority Order (Suggested)

1. **HVAC Diffusers (ACMV)** - Grid placement (EASY - same as sprinklers)
2. **Lights (ELEC)** - Grid placement (EASY - same as sprinklers)
3. **Smoke Detectors (FP)** - Corridor placement (MEDIUM - new strategy)
4. **Emergency Lights (ELEC)** - Perimeter placement (MEDIUM - new strategy)
5. **Toilets (ARC)** - Perimeter placement (HARD - fixtures against walls)
6. **Seating (ARC)** - Row placement (HARD - complex rows + circulation)

---

## 📝 Files to Edit

1. **`Scripts/code_compliance.py`**
   - Add standards to PLACEMENT_STANDARDS dict
   - Add IFC classes to ELEMENT_IFC_MAP

2. **`Scripts/master_routing.py`**
   - Add device types to device_type_map

3. **`Scripts/intelligent_routing.py`** (if routing needed)
   - Update load_devices() to handle new types
   - Add routing logic if needed (lights, HVAC might not need pipes)

---

## ✅ Success Criteria

- [ ] HVAC diffusers generate in grid
- [ ] Lights generate in grid
- [ ] All visible in Blender viewport
- [ ] Code-compliant spacing
- [ ] No clustering issues
- [ ] Can filter by element_name

---

**Current Status:** Framework ready, waiting to add element standards
**Next Step:** Add HVAC diffusers (easiest - same grid strategy as sprinklers)
**Documentation:** This file (NEXT_CHALLENGE_MEP_PLACEMENT.md)

---

**Location:** `/home/red1/Documents/bonsai/2Dto3D/`
**Updated:** Nov 17, 2025
