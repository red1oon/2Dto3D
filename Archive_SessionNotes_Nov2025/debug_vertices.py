#!/usr/bin/env python3
"""Debug: Check vertex coordinates in databases."""

import sqlite3
import struct

def check_vertices(db_path, db_name):
    """Check first few vertices from a database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get one geometry sample
    cursor.execute("SELECT vertices FROM base_geometries WHERE vertices IS NOT NULL LIMIT 1")
    row = cursor.fetchone()

    if row:
        vertices_blob = row[0]
        vertex_count = len(vertices_blob) // 12  # 3 floats × 4 bytes per vertex

        # Decode first 3 vertices (9 floats)
        vertices = struct.unpack(f'{min(9, vertex_count*3)}f', vertices_blob[:36])

        print(f"\n{db_name}:")
        print(f"  Vertex count: {vertex_count}")
        print(f"  First 3 vertices:")
        for i in range(0, min(9, len(vertices)), 3):
            print(f"    V{i//3}: ({vertices[i]:.3f}, {vertices[i+1]:.3f}, {vertices[i+2]:.3f})")

    conn.close()

# Check both databases
check_vertices("/home/red1/Documents/bonsai/8_IFC/enhanced_federation.db", "8_IFC Database")
check_vertices("/home/red1/Documents/bonsai/2Dto3D/BASE_ARC_STR.db", "2Dto3D Database")
