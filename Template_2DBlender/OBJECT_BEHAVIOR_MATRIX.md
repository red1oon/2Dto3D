# Comprehensive Object Behavior Matrix

**Purpose:** Definitive reference for object classification to prevent placement errors

**Date:** 2025-11-23
**Status:** MASTER REFERENCE - DO NOT DEVIATE WITHOUT REVIEW

---

## 🎯 Core Principle

**Every object has EXACTLY ONE behavior category that determines its placement logic.**

If you're uncertain, this matrix is the SINGLE SOURCE OF TRUTH.

---

## 📊 Complete Behavior Matrix

### 🏢 **FLOOR_MOUNTED** - Sits directly on floor (Z=0)

| IFC Class | Object Type | Pivot Point | Height | Rotation | Why Floor-Mounted |
|-----------|-------------|-------------|---------|----------|-------------------|
| **IfcDoor** | door_single | bottom_center | 0.0 | wall_normal | Door frame sits on floor |
| IfcDoor | door_double | bottom_center | 0.0 | wall_normal | Door frame sits on floor |
| **IfcSanitaryTerminal** | toilet_residential_lod300 | bottom_center_back | 0.0 | room_entrance | Base bolted to floor |
| IfcSanitaryTerminal | toilet | bottom_center_back | 0.0 | room_entrance | Base bolted to floor |
| IfcSanitaryTerminal | squatting_pan_wc | bottom_center | 0.0 | room_entrance | Base on floor |
| IfcSanitaryTerminal | shower_tray | bottom_center | 0.0 | absolute | Floor-level tray |
| IfcSanitaryTerminal | floor_drain | center | 0.0 | absolute | Mounted in floor |
| **IfcFurniture** | bed_double | bottom_center | 0.0 | custom | Legs on floor |
| IfcFurniture | wardrobe | bottom_center | 0.0 | parallel_wall | Legs on floor |
| IfcFurniture | dining_table | bottom_center | 0.0 | custom | Legs on floor |
| IfcFurniture | sofa | bottom_center | 0.0 | parallel_wall | Legs on floor |
| IfcFurniture | chair | bottom_center | 0.0 | custom | Legs on floor |
| IfcFurnish ingElement | refrigerator | bottom_center | 0.0 | wall_parallel | Base on floor |
| IfcFurnishingElement | washing_machine | bottom_center | 0.0 | wall_parallel | Base on floor |
| IfcFurnishingElement | water_heater_tank_lod200 | bottom_center | 0.0 | wall_parallel | Floor-standing type |
| IfcBuildingElementProxy | kitchen_cabinet_lower | bottom_center | 0.0 | wall_parallel | Base cabinets |

### 🧱 **WALL_MOUNTED** - Mounts to wall surface at specific height

| IFC Class | Object Type | Pivot Point | Standard Height (m) | Rotation | Why Wall-Mounted |
|-----------|-------------|-------------|---------------------|----------|------------------|
| **IfcSwitchingDevice** | switch_1gang | center | 1.2 | wall_normal | MS 589 standard |
| IfcSwitchingDevice | switch_2gang | center | 1.2 | wall_normal | MS 589 standard |
| IfcSwitchingDevice | switch_3gang | center | 1.2 | wall_normal | MS 589 standard |
| **IfcOutlet** | outlet_3pin_ms589 | center | 0.3 | wall_normal | MS 589 standard |
| IfcOutlet | outlet_3pin_ms589_lod300 | center | 0.3 | wall_normal | MS 589 standard |
| **IfcSanitaryTerminal** | basin | bottom_center | 0.85 | wall_normal | ⚠️ WALL-MOUNTED! Rim @ 850mm |
| IfcSanitaryTerminal | wall_mounted_basin_lod300 | bottom_center | 0.85 | wall_normal | Explicitly wall-mounted |
| IfcSanitaryTerminal | kitchen_sink | bottom_center | 0.9 | wall_normal | Counter-mounted (wall-aligned) |
| IfcSanitaryTerminal | shower_head | center | 1.8 | wall_normal | Wall-mounted @ 1.8m |
| IfcFlowTerminal | exhaust_fan | center | 2.4 | wall_normal | High wall mount |
| IfcAlarm | smoke_detector_wall | center | 2.4 | wall_normal | High wall mount |
| IfcFlowController | water_heater | bottom_center | 1.5 | wall_normal | Wall-hung type |
| IfcBuildingElementProxy | kitchen_cabinet_upper | bottom_center | 1.5 | wall_parallel | Upper cabinets |
| IfcBuildingElementProxy | mirror | center | 1.4 | wall_normal | Bathroom mirror |

### 🔝 **CEILING_MOUNTED** - Hangs from ceiling

| IFC Class | Object Type | Pivot Point | Offset from Ceiling | Rotation | Why Ceiling-Mounted |
|-----------|-------------|-------------|---------------------|----------|---------------------|
| **IfcLightFixture** | ceiling_light | center | -0.05 | absolute | Recessed/surface mount |
| IfcLightFixture | downlight | center | 0.0 | absolute | Recessed in ceiling |
| IfcFlowMovingDevice | ceiling_fan | center | -0.3 | absolute | Hangs from ceiling |
| IfcAirTerminal | air_diffuser | center | 0.0 | absolute | Flush with ceiling |
| IfcAirTerminal | return_air_grille | center | 0.0 | absolute | Ceiling-mounted |
| IfcFireSuppressionTerminal | sprinkler_head | center | -0.05 | absolute | Hangs slightly below |
| IfcAlarm | smoke_detector | center | 0.0 | absolute | Ceiling-mounted type |
| IfcSensor | motion_sensor | center | 0.0 | absolute | Ceiling mount preferred |

### 🎯 **FREE_STANDING** - Placed anywhere (no surface constraint)

| IFC Class | Object Type | Pivot Point | Special Rules | Why Free-Standing |
|-----------|-------------|-------------|---------------|-------------------|
| IfcFlowController | pump | bottom_center | Near water source | Mechanical room equipment |
| IfcFlowController | water_filter | bottom_center | On platform | Mechanical equipment |
| IfcElectricDistributionPoint | distribution_board | bottom_center | Wall-adjacent | Can be freestanding |
| IfcBuildingElementProxy | planter | bottom_center | Decorative placement | Architectural feature |

---

## ❌ **COMMON ERRORS TO AVOID**

### Error 1: Basin Classified as Floor-Mounted ❌
```
WRONG: basin → floor_mounted (sits on floor)
RIGHT: basin → wall_mounted (rim at 850mm height)
```

**Why:** Basins mount to wall studs, NOT the floor. The bottom may touch floor for stability, but mounting point is the wall.

### Error 2: Water Heater Ambiguity ❌
```
CLARIFICATION:
- water_heater_tank_lod200 → floor_mounted (floor-standing vertical tank)
- water_heater (wall-hung) → wall_mounted (compact wall unit)
```

**Why:** Two different types! Check dimensions and manufacturer specs.

### Error 3: Kitchen Cabinets Mixed ❌
```
WRONG: All cabinets → floor_mounted
RIGHT:
  - kitchen_cabinet_lower → floor_mounted (base cabinets)
  - kitchen_cabinet_upper → wall_mounted (wall cabinets @ 1.5m)
```

**Why:** Upper and lower cabinets have different mounting.

### Error 4: Smoke Detectors ❌
```
CLARIFICATION:
- Default → ceiling_mounted (preferred by codes)
- smoke_detector_wall → wall_mounted (special cases only)
```

**Why:** Building codes prefer ceiling mount (smoke rises).

---

## 🔍 **DECISION TREE**

When unsure about object behavior:

```
┌─────────────────────────────────────┐
│ Does object touch/sit on FLOOR?    │
└──────────┬──────────────────────────┘
           │
     YES   │   NO
           │
     ┌─────▼─────┐
     │floor      │    ┌────────────────────────────────┐
     │_mounted   │    │ Does object mount to WALL?      │
     └───────────┘    └──────┬─────────────────────────┘
                             │
                       YES   │   NO
                             │
                       ┌─────▼─────┐
                       │wall       │    ┌───────────────────────────┐
                       │_mounted   │    │ Does object hang from      │
                       └───────────┘    │ CEILING?                   │
                                        └──────┬────────────────────┘
                                               │
                                         YES   │   NO
                                               │
                                         ┌─────▼─────┐
                                         │ceiling    │    ┌───────────────┐
                                         │_mounted   │    │free_standing  │
                                         └───────────┘    └───────────────┘
```

---

## 📏 **MALAYSIAN STANDARDS QUICK REFERENCE**

### MS 589 (Electrical)
- **Switches:** 1200mm above FFL (finished floor level)
- **Outlets:** 300mm above FFL
- **Faceplate:** 86mm × 86mm standard

### MS 1184 (Sanitary)
- **Basin rim:** 850mm above FFL
- **Toilet clearances:** 600mm front, 300mm sides
- **Shower head:** 1800-2000mm above FFL

### MS 1064 (Accessibility)
- **Door width:** 800mm minimum (900mm preferred)
- **Door height:** 2100mm minimum
- **Clearances:** Per UBBL requirements

### UBBL (Uniform Building By-Laws)
- **Room heights:** 2.75m minimum (habitable rooms)
- **Ventilation:** Required for bathrooms/kitchens
- **Fire safety:** Smoke detectors required

---

## 🛠️ **VALIDATION SCRIPT**

Use this SQL to verify all objects have correct behavior:

```sql
-- Find objects missing behavior category
SELECT object_type, COUNT(*) as count
FROM object_catalog
WHERE behavior_category IS NULL
GROUP BY object_type;

-- Find objects with suspicious behavior
SELECT object_type, behavior_category, COUNT(*) as count
FROM object_catalog
WHERE
    (object_type LIKE '%basin%' AND behavior_category = 'floor_mounted') OR
    (object_type LIKE '%switch%' AND behavior_category != 'wall_mounted') OR
    (object_type LIKE '%door%' AND behavior_category != 'floor_mounted')
GROUP BY object_type, behavior_category;

-- Verify MS 589 compliance
SELECT pr.object_type, pr.standard_height, oc.behavior_category
FROM placement_rules pr
JOIN object_catalog oc ON pr.object_type = oc.object_type
WHERE oc.behavior_category = 'wall_mounted'
AND pr.standard_height NOT IN (0.3, 1.2, 1.5, 1.8, 2.4);
```

---

## ✅ **APPROVAL CHECKLIST**

Before adding a new object type to library:

- [ ] Behavior category assigned (floor/wall/ceiling/free)
- [ ] Pivot point defined
- [ ] Standard height specified (if wall/ceiling mounted)
- [ ] Rotation method chosen
- [ ] Malaysian standards checked (if applicable)
- [ ] Similar objects reviewed for consistency
- [ ] Added to this matrix document

---

## 📚 **REFERENCE SOURCES**

1. **MS 589:2020** - Plugs, socket-outlets and adaptors
2. **MS 1184:2014** - Sanitary appliances - Ceramic wash basins
3. **MS 1064:Part 2** - Accessible Design - Accessible route
4. **UBBL 1984** - Uniform Building By-Laws (as amended)
5. **IFC 4.3 Specification** - buildingSMART International

---

## 🚨 **WHEN TO UPDATE THIS MATRIX**

Update immediately when:
1. New object type added to library
2. Malaysian standard updated
3. Classification error discovered
4. Special case identified

**Owner:** DeepSeek Integration Team
**Last Updated:** 2025-11-23
**Next Review:** When adding new object categories

---

**REMEMBER: When in doubt, consult THIS matrix. It prevents the basin-type errors that cost us time!**
