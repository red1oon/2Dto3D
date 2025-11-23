-- Fix Database Schema to Match Working IFC Database
-- Based on comparison with /home/red1/Documents/bonsai/8_IFC/enhanced_federation.db

-- 1. Fix element_transforms (PRIMARY KEY should be guid, not id)
DROP TABLE IF EXISTS element_transforms_old;
ALTER TABLE element_transforms RENAME TO element_transforms_old;

CREATE TABLE element_transforms (
    guid TEXT PRIMARY KEY,
    center_x REAL NOT NULL,
    center_y REAL NOT NULL,
    center_z REAL NOT NULL,
    transform_source TEXT DEFAULT 'dxf_conversion',
    FOREIGN KEY (guid) REFERENCES elements_meta(guid)
);

INSERT INTO element_transforms (guid, center_x, center_y, center_z)
SELECT guid, center_x, center_y, center_z FROM element_transforms_old;

DROP TABLE element_transforms_old;


-- 2. Fix base_geometries (PRIMARY KEY should be geometry_hash, not id)
DROP TABLE IF EXISTS base_geometries_old;
ALTER TABLE base_geometries RENAME TO base_geometries_old;

CREATE TABLE base_geometries (
    geometry_hash TEXT PRIMARY KEY,
    vertices BLOB NOT NULL,
    faces BLOB NOT NULL,
    normals BLOB,
    vertex_count INTEGER NOT NULL,
    face_count INTEGER NOT NULL
);

-- Note: We'll need to recalculate vertex_count and face_count when inserting
-- For now, create empty table - add_geometries.py will populate it


-- 3. Create element_instances table (CRITICAL - was missing!)
DROP TABLE IF EXISTS element_instances;

CREATE TABLE element_instances (
    guid TEXT PRIMARY KEY,
    geometry_hash TEXT NOT NULL,
    FOREIGN KEY (geometry_hash) REFERENCES base_geometries(geometry_hash)
);

CREATE INDEX idx_geom_hash ON element_instances(geometry_hash);


-- 4. Drop old element_geometry VIEW
DROP VIEW IF EXISTS element_geometry;

-- 5. Create correct element_geometry VIEW (joins through element_instances!)
CREATE VIEW element_geometry AS
SELECT
    i.guid,
    g.geometry_hash,
    g.vertices,
    g.faces,
    g.normals
FROM element_instances i
JOIN base_geometries g ON i.geometry_hash = g.geometry_hash;
