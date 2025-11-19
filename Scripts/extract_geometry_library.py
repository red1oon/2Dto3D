#!/usr/bin/env python3
"""
Extract fixture geometry library from 8_IFC enhanced_federation.db

Creates a reusable geometry library with:
- Fire protection: sprinklers, alarms, detectors
- Sanitary: toilets, basins, floor traps
- Electrical: switches, data points
"""

import sqlite3
from pathlib import Path
import json

# Paths
SOURCE_DB = Path("/home/red1/Documents/bonsai/8_IFC/enhanced_federation.db")
TARGET_DB = Path("/home/red1/Documents/bonsai/2Dto3D/DatabaseFiles/geometry_library.db")

# Fixture categories to extract
FIXTURE_CLASSES = [
    'IfcFireSuppressionTerminal',  # Sprinklers
    'IfcAlarm',                     # Smoke detectors, break glass
    'IfcFlowTerminal',              # Toilets, basins, floor traps
    'IfcSanitaryTerminal',          # Sanitary fixtures
    'IfcElectricAppliance',         # Data points, switches
    'IfcLightFixture',              # Light fixtures
]

def create_library_db(conn):
    """Create library database schema"""
    cursor = conn.cursor()

    # Geometry storage (same as federation DB)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS base_geometries (
            geometry_hash TEXT PRIMARY KEY,
            vertices BLOB NOT NULL,
            faces BLOB NOT NULL,
            normals BLOB,
            vertex_count INTEGER NOT NULL,
            face_count INTEGER NOT NULL
        )
    ''')

    # Fixture catalog with metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fixture_catalog (
            geometry_hash TEXT PRIMARY KEY,
            ifc_class TEXT NOT NULL,
            fixture_type TEXT NOT NULL,
            fixture_name TEXT NOT NULL,
            description TEXT,
            vertex_count INTEGER,
            face_count INTEGER,
            FOREIGN KEY (geometry_hash) REFERENCES base_geometries(geometry_hash)
        )
    ''')

    conn.commit()

def extract_fixtures():
    """Extract fixture geometries from 8_IFC database"""

    if not SOURCE_DB.exists():
        print(f"ERROR: Source database not found: {SOURCE_DB}")
        return

    # Connect to source
    src_conn = sqlite3.connect(SOURCE_DB)
    src_cursor = src_conn.cursor()

    # Create target
    TARGET_DB.parent.mkdir(parents=True, exist_ok=True)
    tgt_conn = sqlite3.connect(TARGET_DB)
    create_library_db(tgt_conn)
    tgt_cursor = tgt_conn.cursor()

    print(f"Extracting fixture geometries from {SOURCE_DB.name}")
    print(f"Target: {TARGET_DB}")
    print()

    total_extracted = 0

    for ifc_class in FIXTURE_CLASSES:
        # Get unique geometries for this class
        src_cursor.execute('''
            SELECT DISTINCT
                eg.geometry_hash,
                em.ifc_class,
                em.element_name
            FROM element_geometry eg
            JOIN elements_meta em ON eg.guid = em.guid
            WHERE em.ifc_class = ?
        ''', (ifc_class,))

        fixtures = src_cursor.fetchall()

        if not fixtures:
            print(f"  {ifc_class}: 0 fixtures")
            continue

        # Group by geometry hash to avoid duplicates
        unique_geoms = {}
        for geom_hash, cls, name in fixtures:
            if geom_hash not in unique_geoms:
                unique_geoms[geom_hash] = (cls, name)

        print(f"  {ifc_class}: {len(unique_geoms)} unique geometries")

        for geom_hash, (cls, name) in unique_geoms.items():
            # Get geometry data
            src_cursor.execute('''
                SELECT vertices, faces, normals, vertex_count, face_count
                FROM base_geometries
                WHERE geometry_hash = ?
            ''', (geom_hash,))

            geom_data = src_cursor.fetchone()
            if not geom_data:
                continue

            vertices, faces, normals, v_count, f_count = geom_data

            # Parse fixture type from name
            fixture_type = parse_fixture_type(name, cls)
            fixture_name = parse_fixture_name(name)

            # Insert geometry
            try:
                tgt_cursor.execute('''
                    INSERT OR IGNORE INTO base_geometries
                    (geometry_hash, vertices, faces, normals, vertex_count, face_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (geom_hash, vertices, faces, normals, v_count, f_count))

                # Insert catalog entry
                tgt_cursor.execute('''
                    INSERT OR REPLACE INTO fixture_catalog
                    (geometry_hash, ifc_class, fixture_type, fixture_name, vertex_count, face_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (geom_hash, cls, fixture_type, fixture_name, v_count, f_count))

                total_extracted += 1
            except Exception as e:
                print(f"    Error: {e}")

    tgt_conn.commit()

    # Summary
    print()
    print(f"Total geometries extracted: {total_extracted}")

    # Show catalog summary
    tgt_cursor.execute('''
        SELECT fixture_type, COUNT(*) as count
        FROM fixture_catalog
        GROUP BY fixture_type
        ORDER BY count DESC
    ''')

    print("\nFixture Catalog Summary:")
    for row in tgt_cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    src_conn.close()
    tgt_conn.close()

    print(f"\nLibrary saved to: {TARGET_DB}")

def parse_fixture_type(name, ifc_class):
    """Extract fixture type from element name"""
    name_lower = name.lower()

    # Fire protection
    if 'sprinkler' in name_lower:
        if 'upright' in name_lower:
            return 'sprinkler_upright'
        elif 'pendent' in name_lower:
            return 'sprinkler_pendent'
        return 'sprinkler'
    if 'smoke' in name_lower and 'detector' in name_lower:
        return 'smoke_detector'
    if 'heat' in name_lower and 'detector' in name_lower:
        return 'heat_detector'
    if 'break glass' in name_lower or 'emergency' in name_lower:
        return 'break_glass'
    if 'alarm' in name_lower and 'bell' in name_lower:
        return 'alarm_bell'
    if 'flashing' in name_lower:
        return 'alarm_light'
    if 'intercom' in name_lower:
        return 'fireman_intercom'

    # Sanitary
    if 'toilet' in name_lower or 'wc' in name_lower:
        return 'toilet'
    if 'basin' in name_lower or 'sink' in name_lower:
        return 'basin'
    if 'urinal' in name_lower:
        return 'urinal'
    if 'floor trap' in name_lower:
        return 'floor_trap'
    if 'bidet' in name_lower:
        return 'bidet'
    if 'grease' in name_lower:
        return 'grease_trap'

    # Electrical
    if 'rj45' in name_lower or 'data point' in name_lower:
        return 'data_point'
    if 'switch' in name_lower:
        return 'switch'

    # Light fixtures
    if ifc_class == 'IfcLightFixture':
        return 'light_fixture'

    return 'other'

def parse_fixture_name(full_name):
    """Extract clean fixture name"""
    # Take first part before colon
    if ':' in full_name:
        return full_name.split(':')[0]
    return full_name

if __name__ == '__main__':
    extract_fixtures()
