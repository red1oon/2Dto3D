# 2Dto3D Directory Structure

**Last Cleaned:** November 17, 2025

---

## 📁 Directory Layout

```
2Dto3D/
├── Terminal1_MainBuilding_FILTERED.db  # ⭐ Active database with rotation fix
│
├── docs/                               # 📚 All documentation (13 files)
│   ├── README.md                       # Project overview
│   ├── 2D_TO_3D_COMPLETE_WORKFLOW.md   # Complete pipeline guide
│   ├── PHASE_2_5_ROTATION_FIX_SUMMARY.md  # Current phase
│   ├── BONSAI_TESTER_VALIDATION.md     # Validation results
│   ├── USER_MANUAL.md                  # User guide
│   └── ... (8 more guides)
│
├── Scripts/                            # 🔧 Production scripts
│   ├── dxf_to_database.py             # DXF extraction
│   ├── generate_3d_geometry.py        # 3D geometry generation with rotation
│   ├── extract_wall_angles.py         # Rotation angle extraction
│   ├── find_main_building_bbox.py     # Automated bbox finder
│   └── ... (20+ utility scripts)
│
├── tests/                              # 🧪 Test & analysis tools
│   ├── analyze_wall_rotations.py      # Rotation analysis
│   ├── verify_rotation_fix.py         # Verification script
│   ├── validate_dimensions.py         # Dimension validation
│   └── extract_main_building.py       # Main extraction script
│
├── Terminal1_Project/                  # 📋 Project configuration
│   ├── smart_layer_mappings.json      # Layer → discipline mappings
│   └── Templates/                      # Template library
│
├── SourceFiles/                        # 📥 DXF source files
│   └── TERMINAL1DXF/                   # Source DXF files
│
├── TemplateConfigurator/               # 🎨 GUI tool (separate project)
│
├── logs/                               # 📝 Execution logs
│   ├── extraction_*.log
│   ├── geometry_generation_*.log
│   └── CLEANUP_SUMMARY.txt
│
└── old_backups/                        # 💾 Old backup files
    └── (14 MB old database backup)
```

---

## 🧹 Cleanup Summary

### Files Deleted (Total: ~80 MB freed)

**Databases & Caches (63 MB):**
- Old blend cache (7.3 MB)
- Test databases (56 MB total):
  - Terminal1_3D_FINAL.db
  - Generated_Terminal1_SAMPLE.db
  - Test_Elevation_*.db (4 files)

**Documentation (28 files, ~400 KB):**
- Old session summaries (11 files)
- Redundant technical docs (6 files)
- Strategy/marketing docs (5 files) - belong in ProjectKnowledge/
- GUI/template docs (6 files) - wrong location

**Scripts & Configs:**
- Redundant test scripts (3 files)
- Duplicate JSON configs (2 files)
- Old Documentation/ folder with 43 outdated planning docs

### Files Organized

**Created folders:**
- `docs/` - All documentation (13 essential files)
- `tests/` - Test and analysis scripts (4 files)
- `logs/` - Execution logs (4 files)
- `old_backups/` - Old backup files (2 files)

**Kept in root:**
- ✅ Terminal1_MainBuilding_FILTERED.db (1.4 MB) - Active database
- ✅ Scripts/ - Production pipeline scripts
- ✅ SourceFiles/ - DXF source files
- ✅ Terminal1_Project/ - Project configuration
- ✅ TemplateConfigurator/ - Separate GUI tool

---

## 📊 Before vs After

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Root directory files** | 37 .md + 6 .py + 8 .db + 1 .blend | 1 .db only | 95% cleaner |
| **Total size** | ~145 MB | ~1.4 MB active | 99% reduction |
| **Documentation files** | 37 scattered | 13 organized | Focused |
| **Script organization** | Mixed | Separated | Clear structure |

---

## 🎯 File Locations Quick Reference

### Want to...
- **Generate new database?** → `python3 tests/extract_main_building.py`
- **Add 3D geometry?** → `python3 Scripts/generate_3d_geometry.py <db>`
- **Validate rotations?** → `python3 tests/verify_rotation_fix.py`
- **Test in Blender?** → See `docs/test_in_blender.md`
- **Understand pipeline?** → Read `docs/2D_TO_3D_COMPLETE_WORKFLOW.md`
- **Check phase status?** → Read `docs/PHASE_2_5_ROTATION_FIX_SUMMARY.md`

### Common Workflows

**Full Pipeline:**
```bash
# 1. Extract from DXF with rotation angles
python3 tests/extract_main_building.py
python3 Scripts/extract_wall_angles.py

# 2. Generate 3D geometry
python3 Scripts/generate_3d_geometry.py Terminal1_MainBuilding_FILTERED.db

# 3. Validate
python3 tests/validate_dimensions.py
~/Documents/bonsai/BonsaiTester/bonsai-test Terminal1_MainBuilding_FILTERED.db

# 4. Test in Blender
~/blender-4.5.3/blender  # Load Terminal1_MainBuilding_FILTERED.db
```

---

## 🔍 Notes

1. **Active database:** `Terminal1_MainBuilding_FILTERED.db` (1.4 MB)
   - Contains: 1,185 elements with 3D geometry
   - Phase 2.5 rotation fix applied ✅
   - BonsaiTester validated: 99.7% pass rate ✅

2. **Documentation:** All in `docs/` folder
   - 13 essential files only
   - Organized by purpose (guides, phases, testing)
   - README.md is the starting point

3. **Scripts:** Production code in `Scripts/`, tests in `tests/`
   - Clear separation of concerns
   - Easy to find what you need

4. **Logs:** Execution logs in `logs/` folder
   - Kept for debugging reference
   - Can be deleted safely if needed

5. **Backups:** Old files in `old_backups/`
   - 14 MB old database backup
   - Can be deleted to save space

---

**Structure maintained by:** Claude Code
**Last cleanup:** November 17, 2025
**Status:** ✅ Clean and organized
