#!/usr/bin/env python3
"""Validate extracted database dimensions match IFC."""
import sqlite3

# IFC reference dimensions (from enhanced_federation.db)
IFC_WIDTH = 67.8   # meters
IFC_DEPTH = 48.1   # meters
TOLERANCE = 20     # ±20m tolerance

# Connect to filtered database
conn = sqlite3.connect("Terminal1_MainBuilding_FILTERED.db")
cursor = conn.cursor()

# Get building extents
cursor.execute("""
    SELECT 
        MIN(center_x), MAX(center_x),
        MIN(center_y), MAX(center_y),
        MIN(center_z), MAX(center_z)
    FROM element_transforms
""")
min_x, max_x, min_y, max_y, min_z, max_z = cursor.fetchone()

# Calculate dimensions
width = max_x - min_x
depth = max_y - min_y
height = max_z - min_z

# Print results
print("="*70)
print("DIMENSION VALIDATION")
print("="*70)
print()
print(f"Extracted Database:")
print(f"  Width:  {width:.1f}m")
print(f"  Depth:  {depth:.1f}m")
print(f"  Height: {height:.1f}m")
print()
print(f"IFC Reference:")
print(f"  Width:  {IFC_WIDTH:.1f}m")
print(f"  Depth:  {IFC_DEPTH:.1f}m")
print()
print(f"Differences:")
print(f"  Width:  {abs(width - IFC_WIDTH):.1f}m")
print(f"  Depth:  {abs(depth - IFC_DEPTH):.1f}m")
print()

# Validate
width_ok = abs(width - IFC_WIDTH) < TOLERANCE
depth_ok = abs(depth - IFC_DEPTH) < TOLERANCE

if width_ok and depth_ok:
    print("✅ DIMENSIONS VALIDATED!")
    print(f"   Within ±{TOLERANCE}m tolerance")
else:
    print("❌ DIMENSION MISMATCH!")
    if not width_ok:
        print(f"   Width mismatch: {width:.1f}m vs {IFC_WIDTH:.1f}m")
    if not depth_ok:
        print(f"   Depth mismatch: {depth:.1f}m vs {IFC_DEPTH:.1f}m")

print()
print("="*70)

conn.close()
