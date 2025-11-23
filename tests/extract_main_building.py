#!/usr/bin/env python3
"""
Extract Main Terminal Building from DXF with Spatial Filtering

This script extracts ONLY the main building (~68m × 48m) from the DXF file,
excluding the larger jetty complex, title blocks, and site features.
"""

import sys
sys.path.append('/home/red1/Documents/bonsai/2Dto3D')

from Scripts.dxf_to_database import DXFToDatabase, TemplateLibrary

# Spatial filter from automated bbox finder
# This captures the densest 67.8m × 48.1m region (matches IFC)
SPATIAL_FILTER = {
    'min_x': -1615047.11,
    'max_x': -1540489.36,
    'min_y': 256575.57,
    'max_y': 309442.97
}

print("="*80)
print("DXF EXTRACTION WITH SPATIAL FILTERING")
print("="*80)
print(f"\nSpatial Filter Bounding Box:")
print(f"  X: {SPATIAL_FILTER['min_x']:.2f} to {SPATIAL_FILTER['max_x']:.2f} mm")
print(f"  Y: {SPATIAL_FILTER['min_y']:.2f} to {SPATIAL_FILTER['max_y']:.2f} mm")
print(f"  Size: {(SPATIAL_FILTER['max_x'] - SPATIAL_FILTER['min_x'])/1000:.1f}m × {(SPATIAL_FILTER['max_y'] - SPATIAL_FILTER['min_y'])/1000:.1f}m")
print(f"\nTarget: Match IFC building (67.8m × 48.1m)")
print("\n" + "="*80 + "\n")

# Load template library
template_lib = TemplateLibrary(
    "Terminal1_Project/Templates/terminal_base_v1.0/template_library.db",
    layer_mappings_path="Terminal1_Project/smart_layer_mappings.json"
)

# Create converter WITH spatial filter
converter = DXFToDatabase(
    dxf_path="SourceFiles/TERMINAL1DXF/01 ARCHITECT/2. BANGUNAN TERMINAL 1.dxf",
    output_db="Terminal1_MainBuilding_FILTERED.db",
    template_library=template_lib,
    spatial_filter=SPATIAL_FILTER  # ← KEY: Only extract entities in this box
)

# Step 1: Parse DXF (will filter spatially)
print("Step 1: Parsing DXF with spatial filter...")
entities = converter.parse_dxf()

if not entities:
    print("❌ No entities extracted - spatial filter may be too restrictive")
    sys.exit(1)

print(f"✅ Extracted {len(entities):,} entities within bounding box")

# Step 2: Match templates
print("\nStep 2: Matching entities to templates...")
matched = converter.match_templates()
print(f"✅ Matched {matched:,} entities to IFC templates")

# Step 3: Assign intelligent Z-heights
print("\nStep 3: Assigning intelligent Z-heights...")
converter.assign_intelligent_z_heights(building_type="airport")

# Step 4: Apply vertical separation
print("\nStep 4: Applying vertical separation...")
converter.apply_vertical_separation(grid_size=0.5)

# Step 5: Predict clashes
print("\nStep 5: Predicting potential clashes...")
clash_summary = converter.predict_potential_clashes(tolerance=0.05)

# Step 6: Create database
print("\nStep 6: Creating database...")
converter.create_database()

# Step 7: Populate database
print("\nStep 7: Populating database...")
inserted = converter.populate_database()

print(f"\n✅ Successfully inserted {inserted:,} elements")

# Step 8: Generate statistics
print("\nStep 8: Generating statistics...")
converter.generate_statistics()

print("\n" + "="*80)
print("EXTRACTION COMPLETE")
print("="*80)
print(f"\nDatabase: Terminal1_MainBuilding_FILTERED.db")
print(f"Elements: {inserted:,}")
print(f"\n⚠️  NEXT STEP: Validate building dimensions!")
print(f"   Run: python3 validate_dimensions.py")
