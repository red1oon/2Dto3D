#!/usr/bin/env python3
"""
Verify Terminal1_3D_FINAL.db matches Bonsai Federation requirements
"""

import sqlite3
import sys
from pathlib import Path

def verify_database(db_path):
    """Comprehensive database verification"""

    print(f"🔍 Verifying: {db_path.name}")
    print("=" * 70)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    checks_passed = 0
    checks_failed = 0

    # Check 1: Required tables exist
    print("\n✓ Checking required tables...")
    required_tables = ['elements_meta', 'element_transforms', 'elements_rtree', 'global_offset']
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]

    for table in required_tables:
        if table in existing_tables:
            print(f"   ✅ {table}")
            checks_passed += 1
        else:
            print(f"   ❌ {table} MISSING!")
            checks_failed += 1

    # Check 2: element_geometry is VIEW not table
    print("\n✓ Checking element_geometry...")
    cursor.execute("SELECT type FROM sqlite_master WHERE name='element_geometry'")
    geom_type = cursor.fetchone()
    if geom_type and geom_type[0] == 'view':
        print(f"   ✅ element_geometry is VIEW")
        checks_passed += 1
    else:
        print(f"   ❌ element_geometry should be VIEW, found: {geom_type}")
        checks_failed += 1

    # Check 3: R-tree has camelCase columns
    print("\n✓ Checking R-tree columns...")
    cursor.execute("PRAGMA table_info(elements_rtree)")
    columns = {row[1] for row in cursor.fetchall()}
    expected_cols = {'id', 'minX', 'maxX', 'minY', 'maxY', 'minZ', 'maxZ'}

    if columns == expected_cols:
        print(f"   ✅ R-tree has camelCase columns: {sorted(columns)}")
        checks_passed += 1
    else:
        print(f"   ❌ R-tree columns wrong!")
        print(f"      Expected: {expected_cols}")
        print(f"      Found: {columns}")
        checks_failed += 1

    # Check 4: R-tree and element_transforms have same units
    print("\n✓ Checking R-tree units...")
    cursor.execute("""
        SELECT
            t.center_x as transform_x,
            r.minX as rtree_minX,
            r.maxX as rtree_maxX
        FROM element_transforms t
        JOIN elements_meta m ON t.guid = m.guid
        JOIN elements_rtree r ON m.id = r.id
        LIMIT 1
    """)
    row = cursor.fetchone()
    if row:
        transform_x, rtree_minX, rtree_maxX = row
        expected_minX = transform_x - 0.5
        expected_maxX = transform_x + 0.5

        if abs(rtree_minX - expected_minX) < 0.1 and abs(rtree_maxX - expected_maxX) < 0.1:
            print(f"   ✅ R-tree in meters (same units as element_transforms)")
            print(f"      transform_x: {transform_x:.2f}m")
            print(f"      rtree_minX: {rtree_minX:.2f}m (±0.5m bbox)")
            print(f"      rtree_maxX: {rtree_maxX:.2f}m")
            checks_passed += 1
        else:
            print(f"   ❌ R-tree units mismatch!")
            print(f"      transform_x: {transform_x}m")
            print(f"      rtree_minX: {rtree_minX}m (expected {expected_minX}m)")
            print(f"      rtree_maxX: {rtree_maxX}m (expected {expected_maxX}m)")
            checks_failed += 1

    # Check 5: Population counts
    print("\n✓ Checking table populations...")
    cursor.execute("""
        SELECT
            (SELECT COUNT(*) FROM elements_meta) as meta,
            (SELECT COUNT(*) FROM element_transforms) as transforms,
            (SELECT COUNT(*) FROM elements_rtree) as rtree,
            (SELECT COUNT(*) FROM global_offset) as offset
    """)
    counts = cursor.fetchone()
    meta_count, transform_count, rtree_count, offset_count = counts

    print(f"   elements_meta: {meta_count:,}")
    print(f"   element_transforms: {transform_count:,}")
    print(f"   elements_rtree: {rtree_count:,}")
    print(f"   global_offset: {offset_count}")

    if meta_count == transform_count == rtree_count and offset_count == 1:
        print(f"   ✅ All tables properly populated")
        checks_passed += 1
    else:
        print(f"   ❌ Population mismatch!")
        checks_failed += 1

    # Check 6: Test the actual bbox query used by Bonsai
    print("\n✓ Testing Bonsai bbox query...")
    try:
        cursor.execute("""
            SELECT m.discipline, r.minX, r.minY, r.minZ, r.maxX, r.maxY, r.maxZ, m.guid
            FROM elements_meta m
            JOIN elements_rtree r ON m.id = r.id
            LIMIT 5
        """)
        rows = cursor.fetchall()
        print(f"   ✅ Bbox query works! Retrieved {len(rows)} samples:")
        for i, row in enumerate(rows[:3], 1):
            discipline, minX, minY, minZ, maxX, maxY, maxZ, guid = row
            print(f"      {i}. {discipline}: [{minX:.1f}, {minY:.1f}, {minZ:.1f}] to [{maxX:.1f}, {maxY:.1f}, {maxZ:.1f}]")
        checks_passed += 1
    except Exception as e:
        print(f"   ❌ Bbox query failed: {e}")
        checks_failed += 1

    # Check 7: Coordinate ranges
    print("\n✓ Checking coordinate ranges...")
    cursor.execute("""
        SELECT
            MIN(center_x), MAX(center_x),
            MIN(center_y), MAX(center_y),
            MIN(center_z), MAX(center_z)
        FROM element_transforms
    """)
    ranges = cursor.fetchone()
    min_x, max_x, min_y, max_y, min_z, max_z = ranges

    extent_x = max_x - min_x
    extent_y = max_y - min_y
    extent_z = max_z - min_z

    print(f"   X: {min_x:.1f}m to {max_x:.1f}m ({extent_x:.1f}m / {extent_x/1000:.2f}km)")
    print(f"   Y: {min_y:.1f}m to {max_y:.1f}m ({extent_y:.1f}m / {extent_y/1000:.2f}km)")
    print(f"   Z: {min_z:.1f}m to {max_z:.1f}m ({extent_z:.1f}m)")

    if extent_x > 1000 or extent_y > 1000:
        print(f"   ⚠️  Large building ({extent_x/1000:.1f}km × {extent_y/1000:.1f}km)")
        print(f"       This is expected for DXF with absolute coordinates")

    checks_passed += 1

    conn.close()

    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Checks passed: {checks_passed}")
    if checks_failed > 0:
        print(f"❌ Checks failed: {checks_failed}")
        print("\n⚠️  Database has issues - not ready for Bonsai!")
        return False
    else:
        print(f"\n🎉 Database is valid and ready for Bonsai Federation!")
        return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        db_path = Path(__file__).parent / "Terminal1_3D_FINAL.db"
    else:
        db_path = Path(sys.argv[1])

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    success = verify_database(db_path)
    sys.exit(0 if success else 1)
