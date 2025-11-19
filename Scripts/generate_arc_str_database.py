#!/usr/bin/env python3
"""
ARC/STR Database Generator with World-Positioned Geometry
==========================================================

Generates a federation-compatible database from filtered 2D DXF files.

╔══════════════════════════════════════════════════════════════════════╗
║  CRITICAL: VERTICES MUST BE AT WORLD POSITIONS                       ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  The Bonsai blend_cache.py bake code does NOT apply transforms.      ║
║  It uses vertices directly from element_geometry table.              ║
║                                                                      ║
║  WRONG: Store centered templates + separate transforms               ║
║         → All objects render at origin (0,0,0)                       ║
║                                                                      ║
║  CORRECT: Store vertices at final world positions                    ║
║           → Objects render at correct locations                      ║
║                                                                      ║
║  See: generate_box_at_position() - offsets vertices by (cx, cy, cz)  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

This creates the same database structure as 8_IFC/enhanced_federation.db
for compatibility with Bonsai BBox Preview and Blend bake.

Usage:
    python3 generate_arc_str_database.py

Output:
    DatabaseFiles/Terminal1_ARC_STR.db
"""

import sys
import sqlite3
import struct
import hashlib
import math
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Optional

# Add ezdxf support
try:
    import ezdxf
except ImportError:
    print("ERROR: ezdxf not installed. Run: pip install ezdxf")
    sys.exit(1)

# ============================================================================
# PATHS
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_FILE = BASE_DIR / "arc_str_element_templates.json"
CHEATSHEET_FILE = BASE_DIR / "terminal1_cheatsheet.json"
EXTRACTED_DIR = BASE_DIR / "SourceFiles" / "Terminal1_Extracted"
OUTPUT_DIR = BASE_DIR / "DatabaseFiles"
OUTPUT_DB = OUTPUT_DIR / "Terminal1_ARC_STR.db"

# Also check for any .blend files to delete
BLEND_OUTPUT = OUTPUT_DIR / "Terminal1_ARC_STR.blend"

# ============================================================================
# GEOMETRY UTILITIES
# ============================================================================

def pack_vertices(vertices: List[Tuple[float, float, float]]) -> bytes:
    """Pack list of (x,y,z) tuples into binary BLOB."""
    return struct.pack(f'<{len(vertices)*3}f', *[coord for v in vertices for coord in v])

def pack_faces(faces: List[Tuple[int, int, int]]) -> bytes:
    """Pack list of (i1,i2,i3) tuples into binary BLOB."""
    return struct.pack(f'<{len(faces)*3}I', *[idx for face in faces for idx in face])

def pack_normals(normals: List[Tuple[float, float, float]]) -> bytes:
    """Pack list of normal vectors into binary BLOB."""
    return struct.pack(f'<{len(normals)*3}f', *[coord for n in normals for coord in n])

def compute_hash(vertices_blob: bytes, faces_blob: bytes) -> str:
    """Compute SHA256 hash of geometry for deduplication."""
    hasher = hashlib.sha256()
    hasher.update(vertices_blob)
    hasher.update(faces_blob)
    return hasher.hexdigest()

def compute_face_normal(v0, v1, v2) -> Tuple[float, float, float]:
    """Compute face normal using cross product."""
    e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
    e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
    nx = e1[1] * e2[2] - e1[2] * e2[1]
    ny = e1[2] * e2[0] - e1[0] * e2[2]
    nz = e1[0] * e2[1] - e1[1] * e2[0]
    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length > 0:
        return (nx/length, ny/length, nz/length)
    return (0, 0, 1)

def generate_box_geometry(width: float, depth: float, height: float) -> Tuple[List, List, List]:
    """Generate box geometry centered at origin."""
    hx, hy, hz = width/2, depth/2, height/2
    vertices = [
        (-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0),
        (-hx, -hy, height), (hx, -hy, height), (hx, hy, height), (-hx, hy, height),
    ]
    faces = [
        (0, 1, 2), (0, 2, 3),  # Bottom
        (4, 7, 6), (4, 6, 5),  # Top
        (0, 4, 5), (0, 5, 1),  # Front
        (2, 6, 7), (2, 7, 3),  # Back
        (0, 3, 7), (0, 7, 4),  # Left
        (1, 5, 6), (1, 6, 2),  # Right
    ]
    normals = [compute_face_normal(vertices[f[0]], vertices[f[1]], vertices[f[2]]) for f in faces]
    return vertices, faces, normals

def generate_box_at_position(width: float, depth: float, height: float,
                              cx: float, cy: float, cz: float) -> Tuple[List, List, List]:
    """Generate box geometry at world position (cx, cy, cz)."""
    hx, hy = width/2, depth/2
    vertices = [
        (cx-hx, cy-hy, cz), (cx+hx, cy-hy, cz), (cx+hx, cy+hy, cz), (cx-hx, cy+hy, cz),
        (cx-hx, cy-hy, cz+height), (cx+hx, cy-hy, cz+height), (cx+hx, cy+hy, cz+height), (cx-hx, cy+hy, cz+height),
    ]
    faces = [
        (0, 1, 2), (0, 2, 3),  # Bottom
        (4, 7, 6), (4, 6, 5),  # Top
        (0, 4, 5), (0, 5, 1),  # Front
        (2, 6, 7), (2, 7, 3),  # Back
        (0, 3, 7), (0, 7, 4),  # Left
        (1, 5, 6), (1, 6, 2),  # Right
    ]
    normals = [compute_face_normal(vertices[f[0]], vertices[f[1]], vertices[f[2]]) for f in faces]
    return vertices, faces, normals

def generate_cylinder_geometry(radius: float, height: float, segments: int = 12) -> Tuple[List, List, List]:
    """Generate cylinder geometry centered at origin."""
    vertices = [(0, 0, 0)]  # Bottom center
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        vertices.append((radius * math.cos(angle), radius * math.sin(angle), 0))
    vertices.append((0, 0, height))  # Top center
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        vertices.append((radius * math.cos(angle), radius * math.sin(angle), height))

    faces = []
    # Bottom cap
    for i in range(segments):
        faces.append((0, i + 1, (i + 1) % segments + 1))
    # Sides
    for i in range(segments):
        b1, b2 = i + 1, (i + 1) % segments + 1
        t1, t2 = segments + 2 + i, segments + 2 + (i + 1) % segments
        faces.extend([(b1, t1, t2), (b1, t2, b2)])
    # Top cap
    for i in range(segments):
        faces.append((segments + 1, segments + 2 + (i + 1) % segments, segments + 2 + i))

    normals = [compute_face_normal(vertices[f[0]], vertices[f[1]], vertices[f[2]]) for f in faces]
    return vertices, faces, normals

# ============================================================================
# DATABASE SCHEMA
# ============================================================================

def create_database_schema(conn: sqlite3.Connection):
    """Create federation-compatible database schema."""
    cursor = conn.cursor()

    # Core tables matching 8_IFC structure
    cursor.executescript("""
        -- Base geometries (template shapes, stored once)
        CREATE TABLE IF NOT EXISTS base_geometries (
            geometry_hash TEXT PRIMARY KEY,
            vertices BLOB NOT NULL,
            faces BLOB NOT NULL,
            normals BLOB,
            vertex_count INTEGER NOT NULL,
            face_count INTEGER NOT NULL
        );

        -- Element instances (point to base geometry)
        CREATE TABLE IF NOT EXISTS element_instances (
            guid TEXT PRIMARY KEY,
            geometry_hash TEXT NOT NULL,
            FOREIGN KEY (geometry_hash) REFERENCES base_geometries(geometry_hash)
        );

        -- Element metadata
        CREATE TABLE IF NOT EXISTS elements_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guid TEXT UNIQUE NOT NULL,
            discipline TEXT NOT NULL,
            ifc_class TEXT NOT NULL,
            filepath TEXT,
            element_name TEXT,
            element_type TEXT,
            element_description TEXT,
            storey TEXT,
            material_name TEXT,
            material_rgba TEXT
        );

        -- Element transforms (position in world)
        CREATE TABLE IF NOT EXISTS element_transforms (
            guid TEXT PRIMARY KEY,
            center_x REAL NOT NULL,
            center_y REAL NOT NULL,
            center_z REAL NOT NULL,
            rotation_z REAL DEFAULT 0.0,
            length REAL,
            transform_source TEXT DEFAULT 'dxf_extraction',
            FOREIGN KEY (guid) REFERENCES elements_meta(guid)
        );

        -- Spatial structure
        CREATE TABLE IF NOT EXISTS spatial_structure (
            guid TEXT PRIMARY KEY,
            building TEXT,
            storey TEXT,
            space TEXT,
            FOREIGN KEY (guid) REFERENCES elements_meta(guid)
        );

        -- Global offset for coordinate alignment
        CREATE TABLE IF NOT EXISTS global_offset (
            offset_x REAL NOT NULL,
            offset_y REAL NOT NULL,
            offset_z REAL NOT NULL,
            extent_x REAL,
            extent_y REAL,
            extent_z REAL
        );

        -- Extraction metadata
        CREATE TABLE IF NOT EXISTS extraction_metadata (
            extraction_date TEXT NOT NULL,
            extraction_mode TEXT NOT NULL,
            total_elements INTEGER,
            unique_geometries INTEGER,
            source_files TEXT,
            config_json TEXT
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_elements_discipline ON elements_meta(discipline);
        CREATE INDEX IF NOT EXISTS idx_elements_ifc_class ON elements_meta(ifc_class);
        CREATE INDEX IF NOT EXISTS idx_elements_storey ON elements_meta(storey);
        CREATE INDEX IF NOT EXISTS idx_instances_hash ON element_instances(geometry_hash);

        -- R-tree spatial index for 3D bounding box queries
        CREATE VIRTUAL TABLE IF NOT EXISTS elements_rtree USING rtree(
            id,
            minX, maxX,
            minY, maxY,
            minZ, maxZ
        );
    """)

    conn.commit()
    print("Database schema created")

# ============================================================================
# TEMPLATE GEOMETRY GENERATION
# ============================================================================

def create_template_geometries(conn: sqlite3.Connection, templates: Dict) -> Dict[str, str]:
    """
    Create template geometries in base_geometries table.
    Returns mapping of template_key -> geometry_hash.
    """
    cursor = conn.cursor()
    template_hashes = {}

    # ARC elements
    for ifc_class, template in templates.get('arc_elements', {}).items():
        params = template.get('parameters', {})
        geom_type = template.get('geometry_type', 'box')

        if geom_type == 'box' or geom_type == 'extrusion':
            width = params.get('width_m', params.get('thickness_m', 0.2))
            depth = params.get('depth_m', width)
            height = params.get('height_m', 3.0)
            vertices, faces, normals = generate_box_geometry(width, depth, height)
        elif geom_type == 'cylinder':
            radius = params.get('width_m', 0.4) / 2
            height = params.get('height_m', 4.0)
            vertices, faces, normals = generate_cylinder_geometry(radius, height)
        else:
            # Default box
            vertices, faces, normals = generate_box_geometry(1.0, 1.0, 1.0)

        # Pack and hash
        v_blob = pack_vertices(vertices)
        f_blob = pack_faces(faces)
        n_blob = pack_normals(normals)
        geom_hash = compute_hash(v_blob, f_blob)

        # Store
        cursor.execute("""
            INSERT OR REPLACE INTO base_geometries
            (geometry_hash, vertices, faces, normals, vertex_count, face_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (geom_hash, v_blob, f_blob, n_blob, len(vertices), len(faces)))

        template_hashes[f"ARC_{ifc_class}"] = geom_hash

    # STR elements
    for ifc_class, template in templates.get('str_elements', {}).items():
        params = template.get('parameters', {})
        geom_type = template.get('geometry_type', 'box')

        if ifc_class == 'IfcColumn':
            # Square columns for STR
            size = params.get('width_m', 0.75)
            height = params.get('height_m', 4.0)
            vertices, faces, normals = generate_box_geometry(size, size, height)
        elif ifc_class == 'IfcBeam':
            width = params.get('width_m', 0.3)
            depth = params.get('depth_m', 0.7)
            # Length will be per-instance
            vertices, faces, normals = generate_box_geometry(1.0, width, depth)  # Unit length
        else:
            width = params.get('width_m', params.get('thickness_m', 0.3))
            depth = params.get('depth_m', width)
            height = params.get('height_m', 0.3)
            vertices, faces, normals = generate_box_geometry(width, depth, height)

        v_blob = pack_vertices(vertices)
        f_blob = pack_faces(faces)
        n_blob = pack_normals(normals)
        geom_hash = compute_hash(v_blob, f_blob)

        cursor.execute("""
            INSERT OR REPLACE INTO base_geometries
            (geometry_hash, vertices, faces, normals, vertex_count, face_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (geom_hash, v_blob, f_blob, n_blob, len(vertices), len(faces)))

        template_hashes[f"STR_{ifc_class}"] = geom_hash

    conn.commit()
    print(f"Created {len(template_hashes)} template geometries")
    return template_hashes

# ============================================================================
# DXF EXTRACTION
# ============================================================================

def apply_rotation_transform(x: float, y: float) -> Tuple[float, float]:
    """Apply 90° CCW rotation: (x, y) → (-y, x)"""
    return (-y, x)

def extract_dxf_entities(dxf_path: Path, discipline: str, floor: str,
                        templates: Dict, layer_mapping: Dict) -> List[Dict]:
    """
    Extract entities from DXF file and classify by layer.
    Returns list of element dicts ready for database insertion.
    """
    elements = []

    try:
        doc = ezdxf.readfile(str(dxf_path))
    except Exception as e:
        print(f"  ERROR reading {dxf_path.name}: {e}")
        return elements

    msp = doc.modelspace()

    for entity in msp:
        if entity.dxftype() not in ['LINE', 'LWPOLYLINE', 'CIRCLE', 'ARC', 'INSERT']:
            continue

        # Get layer and map to IFC class
        layer_raw = entity.dxf.layer if hasattr(entity.dxf, 'layer') else ''
        layer_upper = layer_raw.upper()

        # Try exact match first, then uppercase
        mapping = layer_mapping.get(layer_raw) or layer_mapping.get(layer_upper)
        if not mapping:
            continue

        ifc_class = mapping.get('ifc_class', 'IfcBuildingElementProxy')
        elem_discipline = mapping.get('discipline', discipline)

        # Extract position based on entity type
        x, y, z = 0, 0, 0
        length = 0
        rotation = 0

        if entity.dxftype() == 'CIRCLE':
            x, y = entity.dxf.center.x, entity.dxf.center.y
            z = entity.dxf.center.z if hasattr(entity.dxf.center, 'z') else 0
            length = entity.dxf.radius * 2  # Diameter

        elif entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            x = (start.x + end.x) / 2
            y = (start.y + end.y) / 2
            z = (start.z + end.z) / 2 if hasattr(start, 'z') else 0
            length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
            if length > 0.001:
                rotation = math.atan2(end.y - start.y, end.x - start.x)

        elif entity.dxftype() == 'LWPOLYLINE':
            points = list(entity.get_points('xy'))
            if points:
                x = sum(p[0] for p in points) / len(points)
                y = sum(p[1] for p in points) / len(points)
                # Calculate total length
                for i in range(len(points) - 1):
                    length += math.sqrt((points[i+1][0] - points[i][0])**2 +
                                       (points[i+1][1] - points[i][1])**2)

        elif entity.dxftype() == 'INSERT':
            x, y = entity.dxf.insert.x, entity.dxf.insert.y
            z = entity.dxf.insert.z if hasattr(entity.dxf.insert, 'z') else 0
            rotation = math.radians(entity.dxf.rotation) if hasattr(entity.dxf, 'rotation') else 0

        elif entity.dxftype() == 'ARC':
            x, y = entity.dxf.center.x, entity.dxf.center.y
            z = entity.dxf.center.z if hasattr(entity.dxf.center, 'z') else 0
            length = entity.dxf.radius

        # Convert from mm to m
        x_m = x / 1000.0
        y_m = y / 1000.0
        z_m = z / 1000.0
        length_m = length / 1000.0

        # Apply rotation transform (90° CCW)
        x_rot, y_rot = apply_rotation_transform(x_m, y_m)

        # Apply alignment offset to bring all geometry near origin (0, 0)
        # Centers from actual extracted DXF files (after rotation):
        # - ARC: (68.9, -1598.6) m
        # - STR (all floors): (35.7, 44.5) m

        if discipline == 'ARC':
            x_final = x_rot - 68.9
            y_final = y_rot + 1598.6
        else:  # STR - all floors have same coordinate system in extracted files
            x_final = x_rot - 35.7
            y_final = y_rot - 44.5

        # Generate GUID
        guid = str(uuid.uuid4()).replace('-', '')[:22]

        elements.append({
            'guid': guid,
            'discipline': elem_discipline,
            'ifc_class': ifc_class,
            'floor': floor,
            'center_x': x_final,
            'center_y': y_final,
            'center_z': z_m,
            'rotation_z': rotation,
            'length': length_m,
            'layer': layer_raw,
            'source_file': dxf_path.name
        })

    return elements

# ============================================================================
# MAIN GENERATION
# ============================================================================

def main():
    print("="*70)
    print("ARC/STR DATABASE GENERATOR - Instanced Geometry Pattern")
    print("="*70)

    # Clean up existing files
    if BLEND_OUTPUT.exists():
        BLEND_OUTPUT.unlink()
        print(f"Deleted existing: {BLEND_OUTPUT.name}")

    if OUTPUT_DB.exists():
        OUTPUT_DB.unlink()
        print(f"Deleted existing: {OUTPUT_DB.name}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load templates
    if not TEMPLATES_FILE.exists():
        print(f"ERROR: Templates file not found: {TEMPLATES_FILE}")
        sys.exit(1)

    with open(TEMPLATES_FILE) as f:
        templates = json.load(f)
    print(f"Loaded templates from: {TEMPLATES_FILE.name}")

    # Load cheatsheet for alignment info
    if CHEATSHEET_FILE.exists():
        with open(CHEATSHEET_FILE) as f:
            cheatsheet = json.load(f)
        print(f"Loaded cheatsheet from: {CHEATSHEET_FILE.name}")
    else:
        cheatsheet = {}

    # Get layer mapping
    layer_mapping = templates.get('dxf_layer_to_ifc_mapping', {})

    # Create database
    conn = sqlite3.connect(str(OUTPUT_DB))
    create_database_schema(conn)

    # Create template geometries
    template_hashes = create_template_geometries(conn, templates)

    # Define source files
    dxf_sources = [
        ('ARC', '1F', EXTRACTED_DIR / "Terminal1_ARC.dxf"),
        ('STR', '1F', EXTRACTED_DIR / "Terminal1_STR_1F.dxf"),
        ('STR', '3F', EXTRACTED_DIR / "Terminal1_STR_3F.dxf"),
        ('STR', '4F-6F', EXTRACTED_DIR / "Terminal1_STR_4F-6F.dxf"),
    ]

    # Get floor elevations
    floor_elevations = templates.get('floor_elevations_m', {
        '1F': 0.0, '3F': 8.0, '4F-6F': 12.0
    })

    # Extract all entities
    all_elements = []
    cursor = conn.cursor()

    print("\nExtracting DXF entities...")
    for discipline, floor, dxf_path in dxf_sources:
        if not dxf_path.exists():
            print(f"  SKIP: {dxf_path.name} not found")
            continue

        elements = extract_dxf_entities(dxf_path, discipline, floor, templates, layer_mapping)

        # Set Z elevation based on floor
        base_z = floor_elevations.get(floor, 0.0)
        for elem in elements:
            elem['center_z'] = base_z

        all_elements.extend(elements)
        print(f"  {dxf_path.name}: {len(elements)} elements")

    print(f"\nTotal elements extracted: {len(all_elements)}")

    # Insert elements into database
    print("\nPopulating database...")
    stats = {'by_class': {}, 'by_discipline': {}}

    for elem in all_elements:
        guid = elem['guid']

        # Get element dimensions from template
        template_key_lookup = elem['ifc_class']
        if elem['discipline'] == 'ARC':
            params = templates.get('arc_elements', {}).get(template_key_lookup, {}).get('parameters', {})
            material_info = templates.get('arc_elements', {}).get(template_key_lookup, {}).get('material', {})
        else:
            params = templates.get('str_elements', {}).get(template_key_lookup, {}).get('parameters', {})
            material_info = templates.get('str_elements', {}).get(template_key_lookup, {}).get('material', {})

        material_name = material_info.get('name', 'Default')
        material_rgba = json.dumps(material_info.get('rgba', [0.7, 0.7, 0.7, 1.0]))

        # Get dimensions
        width = params.get('width_m', params.get('thickness_m', 0.5))
        depth = params.get('depth_m', width)
        height = params.get('height_m', 3.0)

        # Use length from DXF if available (for walls, beams)
        if elem['length'] and elem['length'] > 0:
            width = max(width, elem['length'])

        # Generate geometry at world position
        cx, cy, cz = elem['center_x'], elem['center_y'], elem['center_z']
        vertices, faces, normals = generate_box_at_position(width, depth, height, cx, cy, cz)

        # Pack and hash
        v_blob = pack_vertices(vertices)
        f_blob = pack_faces(faces)
        n_blob = pack_normals(normals)
        geom_hash = compute_hash(v_blob, f_blob)

        # Store geometry (each element has unique world-positioned geometry)
        cursor.execute("""
            INSERT OR IGNORE INTO base_geometries
            (geometry_hash, vertices, faces, normals, vertex_count, face_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (geom_hash, v_blob, f_blob, n_blob, len(vertices), len(faces)))

        # Insert element metadata
        cursor.execute("""
            INSERT INTO elements_meta
            (guid, discipline, ifc_class, filepath, element_name, storey, material_name, material_rgba)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (guid, elem['discipline'], elem['ifc_class'], elem['source_file'],
              f"{elem['ifc_class']}_{guid[:8]}", elem['floor'], material_name, material_rgba))

        # Insert element instance (points to template geometry)
        cursor.execute("""
            INSERT INTO element_instances (guid, geometry_hash)
            VALUES (?, ?)
        """, (guid, geom_hash))

        # Insert transform
        cursor.execute("""
            INSERT INTO element_transforms
            (guid, center_x, center_y, center_z, rotation_z, length)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (guid, elem['center_x'], elem['center_y'], elem['center_z'],
              elem['rotation_z'], elem['length']))

        # Insert spatial structure
        cursor.execute("""
            INSERT INTO spatial_structure (guid, building, storey)
            VALUES (?, ?, ?)
        """, (guid, 'Terminal 1', elem['floor']))

        # Calculate bounding box half-sizes (width, depth, height already calculated above)
        hw, hd = width / 2, depth / 2

        # Get row id from elements_meta for rtree
        cursor.execute("SELECT id FROM elements_meta WHERE guid = ?", (guid,))
        row_id = cursor.fetchone()[0]

        # Insert into R-tree spatial index
        cursor.execute("""
            INSERT INTO elements_rtree (id, minX, maxX, minY, maxY, minZ, maxZ)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (row_id, cx - hw, cx + hw, cy - hd, cy + hd, cz, cz + height))

        # Track stats
        ifc_class = elem['ifc_class']
        discipline = elem['discipline']
        stats['by_class'][ifc_class] = stats['by_class'].get(ifc_class, 0) + 1
        stats['by_discipline'][discipline] = stats['by_discipline'].get(discipline, 0) + 1

    # Insert extraction metadata
    cursor.execute("""
        INSERT INTO extraction_metadata
        (extraction_date, extraction_mode, total_elements, unique_geometries, source_files, config_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), 'instanced_geometry', len(all_elements),
          len(template_hashes), json.dumps([str(s[2].name) for s in dxf_sources]),
          json.dumps({'templates': TEMPLATES_FILE.name})))

    # Insert global offset (for coordinate alignment)
    cursor.execute("""
        INSERT INTO global_offset (offset_x, offset_y, offset_z)
        VALUES (0, 0, 0)
    """)

    conn.commit()
    conn.close()

    # Print summary
    print("\n" + "="*70)
    print("DATABASE GENERATION COMPLETE")
    print("="*70)
    print(f"Output: {OUTPUT_DB}")
    print(f"Total elements: {len(all_elements)}")
    print(f"Unique geometries: {len(template_hashes)}")
    print(f"Storage optimization: {len(all_elements)/len(template_hashes):.1f}x instances per geometry")

    print("\nBy Discipline:")
    for disc, count in sorted(stats['by_discipline'].items()):
        print(f"  {disc}: {count}")

    print("\nBy IFC Class:")
    for ifc_class, count in sorted(stats['by_class'].items(), key=lambda x: -x[1]):
        print(f"  {ifc_class}: {count}")

    print("\n" + "="*70)
    print("Next: Load in Bonsai BBox Preview or run blend bake")
    print("="*70)

if __name__ == "__main__":
    main()
