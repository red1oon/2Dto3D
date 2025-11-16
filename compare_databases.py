#!/usr/bin/env python3
"""
Compare working IFC database with our DXF database to find critical differences
"""

import sqlite3
from pathlib import Path

WORKING_DB = "/home/red1/Documents/bonsai/8_IFC/enhanced_federation.db"
OUR_DB = "/home/red1/Documents/bonsai/2Dto3D/Terminal1_3D_FINAL.db"

def compare_databases():
    print("="*80)
    print("DATABASE COMPARISON: Working IFC vs Our DXF")
    print("="*80)

    conn_working = sqlite3.connect(WORKING_DB)
    conn_ours = sqlite3.connect(OUR_DB)

    # 1. Compare table list
    print("\n1. TABLE COMPARISON")
    print("-" * 80)

    working_tables = set(row[0] for row in conn_working.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ))

    our_tables = set(row[0] for row in conn_ours.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ))

    print(f"Working DB tables: {len(working_tables)}")
    print(f"Our DB tables: {len(our_tables)}")

    missing = working_tables - our_tables
    extra = our_tables - working_tables
    common = working_tables & our_tables

    if missing:
        print(f"\n⚠️  MISSING in our DB ({len(missing)}):")
        for table in sorted(missing):
            print(f"   - {table}")

    if extra:
        print(f"\n✓ Extra in our DB ({len(extra)}):")
        for table in sorted(extra):
            print(f"   + {table}")

    print(f"\n✓ Common tables ({len(common)}): {', '.join(sorted(common)[:10])}...")

    # 2. Compare critical table schemas
    print("\n\n2. SCHEMA COMPARISON (Critical Tables)")
    print("-" * 80)

    critical_tables = ['elements_meta', 'element_transforms', 'base_geometries',
                       'elements_rtree', 'global_offset']

    for table in critical_tables:
        if table not in common:
            print(f"\n⚠️  {table}: NOT IN BOTH DATABASES")
            continue

        print(f"\n{table}:")

        # Get schema
        working_schema = list(conn_working.execute(f"PRAGMA table_info({table})"))
        our_schema = list(conn_ours.execute(f"PRAGMA table_info({table})"))

        working_cols = {row[1]: row[2] for row in working_schema}  # name: type
        our_cols = {row[1]: row[2] for row in our_schema}

        if working_cols == our_cols:
            print(f"   ✓ Schema matches ({len(working_cols)} columns)")
        else:
            print(f"   ⚠️  Schema differs!")
            print(f"      Working: {list(working_cols.keys())}")
            print(f"      Ours:    {list(our_cols.keys())}")

    # 3. Compare data counts
    print("\n\n3. ROW COUNT COMPARISON")
    print("-" * 80)

    for table in sorted(common):
        if table.endswith('_rtree_node') or table.endswith('_rtree_parent') or table.endswith('_rtree_rowid'):
            continue  # Skip R-tree internal tables

        try:
            working_count = conn_working.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            our_count = conn_ours.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

            if working_count > 0 or our_count > 0:
                match = "✓" if working_count == our_count else "⚠️"
                print(f"{match} {table:30s}: Working={working_count:6d}, Ours={our_count:6d}")
        except:
            pass

    # 4. Compare element_transforms structure (PRIMARY KEY!)
    print("\n\n4. ELEMENT_TRANSFORMS PRIMARY KEY")
    print("-" * 80)

    working_pk = [row for row in conn_working.execute("PRAGMA table_info(element_transforms)") if row[5] == 1]
    our_pk = [row for row in conn_ours.execute("PRAGMA table_info(element_transforms)") if row[5] == 1]

    print(f"Working DB PRIMARY KEY: {working_pk[0][1] if working_pk else 'NONE'}")
    print(f"Our DB PRIMARY KEY:     {our_pk[0][1] if our_pk else 'NONE'}")

    if working_pk and our_pk:
        if working_pk[0][1] == our_pk[0][1]:
            print("   ✓ PRIMARY KEY matches")
        else:
            print("   ⚠️  PRIMARY KEY MISMATCH! This is CRITICAL!")

    # 5. Compare base_geometries structure (PRIMARY KEY!)
    print("\n\n5. BASE_GEOMETRIES PRIMARY KEY")
    print("-" * 80)

    working_pk = [row for row in conn_working.execute("PRAGMA table_info(base_geometries)") if row[5] == 1]
    our_pk = [row for row in conn_ours.execute("PRAGMA table_info(base_geometries)") if row[5] == 1]

    print(f"Working DB PRIMARY KEY: {working_pk[0][1] if working_pk else 'NONE'}")
    print(f"Our DB PRIMARY KEY:     {our_pk[0][1] if our_pk else 'NONE'}")

    if working_pk and our_pk:
        if working_pk[0][1] == our_pk[0][1]:
            print("   ✓ PRIMARY KEY matches")
        else:
            print("   ⚠️  PRIMARY KEY MISMATCH! This is CRITICAL!")
            print(f"      Working uses: {working_pk[0][1]}")
            print(f"      Ours uses:    {our_pk[0][1]}")

    # 6. Check element_instances table
    print("\n\n6. ELEMENT_INSTANCES TABLE")
    print("-" * 80)

    if 'element_instances' in working_tables:
        print("✓ Working DB has element_instances")
        count = conn_working.execute("SELECT COUNT(*) FROM element_instances").fetchone()[0]
        print(f"  Row count: {count:,}")
    else:
        print("⚠️  Working DB does NOT have element_instances")

    if 'element_instances' in our_tables:
        print("✓ Our DB has element_instances")
        count = conn_ours.execute("SELECT COUNT(*) FROM element_instances").fetchone()[0]
        print(f"  Row count: {count:,}")
    else:
        print("❌ Our DB does NOT have element_instances - THIS IS MISSING!")

    # 7. Check element_geometry VIEW
    print("\n\n7. ELEMENT_GEOMETRY VIEW")
    print("-" * 80)

    working_view = conn_working.execute(
        "SELECT sql FROM sqlite_master WHERE type='view' AND name='element_geometry'"
    ).fetchone()

    our_view = conn_ours.execute(
        "SELECT sql FROM sqlite_master WHERE type='view' AND name='element_geometry'"
    ).fetchone()

    if working_view:
        print("Working DB element_geometry VIEW:")
        print(working_view[0])

    if our_view:
        print("\nOur DB element_geometry VIEW:")
        print(our_view[0])

    if working_view and our_view:
        if working_view[0] == our_view[0]:
            print("\n✓ VIEW definitions match")
        else:
            print("\n⚠️  VIEW definitions DIFFER!")

    conn_working.close()
    conn_ours.close()

    print("\n" + "="*80)
    print("COMPARISON COMPLETE")
    print("="*80)

if __name__ == '__main__':
    compare_databases()
