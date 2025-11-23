-- ============================================================
-- PHASE 1: FULL PLACEMENT RULES SCHEMA
-- DeepSeek Geometric Rules Engine - Complete Implementation
-- ============================================================
-- Date: 2025-11-23
-- Purpose: Add semantic placement intelligence to object library
-- ============================================================

BEGIN TRANSACTION;

-- ============================================================
-- TABLE 1: placement_rules
-- Defines how objects should be aligned and rotated
-- ============================================================

CREATE TABLE IF NOT EXISTS placement_rules (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_type TEXT NOT NULL UNIQUE,

    -- Alignment Rules
    alignment_type TEXT,
    -- Values: "bottom", "center", "top", "wall_surface", "floor", "ceiling"

    reference_plane TEXT,
    -- Values: "floor", "wall", "ceiling", "custom"

    offset_z REAL DEFAULT 0.0,
    -- Vertical offset from reference plane (meters)

    standard_height REAL,
    -- For wall-mounted objects (switches: 1.2m, outlets: 0.3m)

    offset_from_wall REAL,
    -- Distance from wall surface (meters, typically 0.02m for surface-mounted)

    -- Rotation Rules
    rotation_method TEXT,
    -- Values: "wall_normal", "room_entrance", "absolute", "custom", "parallel_wall", "perpendicular_wall"

    flip_direction INTEGER DEFAULT 0,
    -- 0=false, 1=true (for left/right handed doors)

    rotation_offset_degrees REAL DEFAULT 0.0,
    -- Additional rotation adjustment

    preferred_orientation TEXT,
    -- Values: "parallel_wall", "perpendicular_wall", "face_room", "face_entrance"

    -- Snapping Configuration
    snapping_enabled INTEGER DEFAULT 1,
    -- 0=false, 1=true

    snapping_targets TEXT,
    -- JSON array of surfaces: '["wall_surface", "floor", "ceiling"]'

    snapping_tolerance REAL DEFAULT 0.01,
    -- Distance tolerance for snapping (meters)

    -- Metadata
    rule_description TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (object_type) REFERENCES object_catalog(object_type)
);

CREATE INDEX IF NOT EXISTS idx_placement_rules_type ON placement_rules(object_type);
CREATE INDEX IF NOT EXISTS idx_placement_alignment ON placement_rules(alignment_type);
CREATE INDEX IF NOT EXISTS idx_placement_rotation ON placement_rules(rotation_method);


-- ============================================================
-- TABLE 2: connection_requirements
-- Defines what surfaces objects connect to and required clearances
-- ============================================================

CREATE TABLE IF NOT EXISTS connection_requirements (
    connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_type TEXT NOT NULL UNIQUE,

    -- Surface Connections
    primary_surface TEXT,
    -- Primary connection: "wall", "floor", "ceiling"

    secondary_surface TEXT,
    -- Optional second connection

    tertiary_surface TEXT,
    -- Optional third connection (e.g., toilet connects to floor, wall, and drainage)

    -- Clearances (in meters)
    clearance_front REAL,
    -- Space needed in front of object

    clearance_rear REAL,
    -- Space needed behind object

    clearance_left REAL,
    -- Space needed on left side

    clearance_right REAL,
    -- Space needed on right side

    clearance_top REAL,
    -- Space needed above object

    clearance_bottom REAL,
    -- Space needed below object

    -- Semantic Rules (Boolean flags)
    must_face_room INTEGER DEFAULT 0,
    -- Object must face into room (toilets, switches)

    must_face_entrance INTEGER DEFAULT 0,
    -- Object must face room entrance

    requires_water_supply INTEGER DEFAULT 0,
    -- Needs water connection (sinks, toilets, basins)

    requires_drainage INTEGER DEFAULT 0,
    -- Needs drainage connection (sinks, toilets, floor drains)

    requires_electrical INTEGER DEFAULT 0,
    -- Needs electrical connection (switches, outlets, appliances)

    requires_ventilation INTEGER DEFAULT 0,
    -- Needs ventilation (HVAC, exhaust)

    -- Accessibility Requirements
    min_approach_distance REAL,
    -- Minimum distance needed to approach/use object

    wheelchair_accessible INTEGER DEFAULT 0,
    -- Must meet wheelchair accessibility standards

    -- Metadata
    requirements_description TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (object_type) REFERENCES object_catalog(object_type)
);

CREATE INDEX IF NOT EXISTS idx_connection_requirements_type ON connection_requirements(object_type);
CREATE INDEX IF NOT EXISTS idx_connection_primary_surface ON connection_requirements(primary_surface);


-- ============================================================
-- TABLE 3: malaysian_standards
-- Malaysian building standards compliance (MS 589, MS 1064, etc.)
-- ============================================================

CREATE TABLE IF NOT EXISTS malaysian_standards (
    standard_id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_type TEXT NOT NULL,

    -- Standard Reference
    ms_code TEXT,
    -- Malaysian Standard code (e.g., "MS 589", "MS 1064", "UBBL")

    standard_title TEXT,
    -- Full standard title

    -- Requirements
    requirement_type TEXT,
    -- Type: "dimension", "height", "clearance", "material", "installation"

    requirement_value TEXT,
    -- The actual requirement (e.g., "1200mm", "300mm", "13A")

    requirement_description TEXT,
    -- Detailed description of requirement

    -- Compliance
    is_mandatory INTEGER DEFAULT 0,
    -- 0=recommended, 1=mandatory

    compliance_notes TEXT,
    -- Additional notes on compliance

    -- Metadata
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_malaysian_standards_type ON malaysian_standards(object_type);
CREATE INDEX IF NOT EXISTS idx_malaysian_standards_code ON malaysian_standards(ms_code);


-- ============================================================
-- TABLE 4: validation_rules (Optional - for debugging)
-- Stores validation rules for quality checking
-- ============================================================

CREATE TABLE IF NOT EXISTS validation_rules (
    validation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_type TEXT NOT NULL,

    rule_name TEXT NOT NULL,
    -- Name of validation rule

    rule_type TEXT,
    -- Type: "must", "should", "optional"

    rule_category TEXT,
    -- Category: "placement", "rotation", "clearance", "connection", "dimension"

    rule_expression TEXT,
    -- Validation expression or SQL query

    error_message TEXT,
    -- Message to show if validation fails

    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_validation_rules_type ON validation_rules(object_type);
CREATE INDEX IF NOT EXISTS idx_validation_rules_category ON validation_rules(rule_category);


-- ============================================================
-- INITIAL DATA: Populate rules for 5 critical objects
-- ============================================================

-- ============================================================
-- 1. door_single - Floor-mounted door
-- ============================================================

INSERT OR REPLACE INTO placement_rules (
    object_type,
    alignment_type,
    reference_plane,
    offset_z,
    rotation_method,
    flip_direction,
    snapping_enabled,
    snapping_targets,
    rule_description
) VALUES (
    'door_single',
    'bottom',
    'floor',
    0.0,
    'wall_normal',
    0,
    1,
    '["wall_surface", "floor"]',
    'Door bottom aligns to floor, rotates perpendicular to wall normal, swings into room'
);

INSERT OR REPLACE INTO connection_requirements (
    object_type,
    primary_surface,
    secondary_surface,
    clearance_front,
    clearance_rear,
    clearance_left,
    clearance_right,
    must_face_room,
    min_approach_distance,
    requirements_description
) VALUES (
    'door_single',
    'wall',
    'floor',
    1.0,
    0.8,
    0.1,
    0.1,
    1,
    0.5,
    'Door connects to wall opening and floor, requires 1m clearance in front for swing'
);

INSERT OR REPLACE INTO malaysian_standards (
    object_type,
    ms_code,
    standard_title,
    requirement_type,
    requirement_value,
    requirement_description,
    is_mandatory
) VALUES
(
    'door_single',
    'MS 1064',
    'Malaysian Standard - Accessible Design',
    'dimension',
    '800mm or 900mm width',
    'Standard door widths for residential buildings. 900mm recommended for accessibility.',
    0
),
(
    'door_single',
    'UBBL',
    'Uniform Building By-Laws',
    'height',
    '2100mm minimum',
    'Minimum door height for habitable rooms',
    1
);


-- ============================================================
-- 2. switch_1gang - Wall-mounted light switch
-- ============================================================

INSERT OR REPLACE INTO placement_rules (
    object_type,
    alignment_type,
    reference_plane,
    standard_height,
    offset_from_wall,
    rotation_method,
    snapping_enabled,
    snapping_targets,
    rule_description
) VALUES (
    'switch_1gang',
    'wall_surface',
    'wall',
    1.2,
    0.02,
    'wall_normal',
    1,
    '["wall_surface"]',
    'Switch mounts on wall at 1.2m height, faces into room'
);

INSERT OR REPLACE INTO connection_requirements (
    object_type,
    primary_surface,
    clearance_front,
    must_face_room,
    requires_electrical,
    min_approach_distance,
    requirements_description
) VALUES (
    'switch_1gang',
    'wall',
    0.3,
    1,
    1,
    0.2,
    'Switch mounts flush to wall, requires electrical connection, 300mm clearance for operation'
);

INSERT OR REPLACE INTO malaysian_standards (
    object_type,
    ms_code,
    standard_title,
    requirement_type,
    requirement_value,
    requirement_description,
    is_mandatory
) VALUES
(
    'switch_1gang',
    'MS 589',
    'Malaysian Standard - Electrical Installations',
    'height',
    '1200mm above finished floor level',
    'Standard installation height for light switches in residential buildings',
    0
),
(
    'switch_1gang',
    'MS 589',
    'Malaysian Standard - Electrical Installations',
    'dimension',
    '86mm x 86mm faceplate',
    'Standard faceplate size (1-gang)',
    1
);


-- ============================================================
-- 3. toilet - Floor-mounted water closet
-- ============================================================

INSERT OR REPLACE INTO placement_rules (
    object_type,
    alignment_type,
    reference_plane,
    offset_z,
    rotation_method,
    preferred_orientation,
    snapping_enabled,
    snapping_targets,
    rule_description
) VALUES (
    'toilet',
    'bottom',
    'floor',
    0.0,
    'room_entrance',
    'face_entrance',
    1,
    '["floor", "wall"]',
    'Toilet sits on floor, typically faces room entrance or opposite wall'
);

INSERT OR REPLACE INTO connection_requirements (
    object_type,
    primary_surface,
    secondary_surface,
    tertiary_surface,
    clearance_front,
    clearance_left,
    clearance_right,
    clearance_rear,
    must_face_entrance,
    requires_water_supply,
    requires_drainage,
    min_approach_distance,
    requirements_description
) VALUES (
    'toilet',
    'floor',
    'wall',
    'drainage',
    0.6,
    0.3,
    0.3,
    0.1,
    1,
    1,
    1,
    0.6,
    'Toilet requires floor mounting, water supply, drainage connection. Minimum 600mm front clearance, 300mm side clearance per building codes.'
);

INSERT OR REPLACE INTO malaysian_standards (
    object_type,
    ms_code,
    standard_title,
    requirement_type,
    requirement_value,
    requirement_description,
    is_mandatory
) VALUES
(
    'toilet',
    'MS 1184',
    'Malaysian Standard - Sanitary Appliances',
    'clearance',
    '600mm front, 300mm sides',
    'Minimum clearances for toilet installation',
    1
),
(
    'toilet',
    'UBBL',
    'Uniform Building By-Laws',
    'dimension',
    '400-450mm width, 600-650mm depth',
    'Standard toilet bowl dimensions',
    0
);


-- ============================================================
-- 4. outlet_3pin_ms589 - Malaysian 3-pin electrical outlet
-- ============================================================

INSERT OR REPLACE INTO placement_rules (
    object_type,
    alignment_type,
    reference_plane,
    standard_height,
    offset_from_wall,
    rotation_method,
    snapping_enabled,
    snapping_targets,
    rule_description
) VALUES (
    'outlet_3pin_ms589',
    'wall_surface',
    'wall',
    0.3,
    0.02,
    'wall_normal',
    1,
    '["wall_surface"]',
    'Outlet mounts on wall at 300mm height (MS 589 standard)'
);

INSERT OR REPLACE INTO connection_requirements (
    object_type,
    primary_surface,
    clearance_front,
    requires_electrical,
    min_approach_distance,
    requirements_description
) VALUES (
    'outlet_3pin_ms589',
    'wall',
    0.2,
    1,
    0.1,
    'MS 589 compliant 13A outlet, mounts flush to wall, requires electrical connection'
);

INSERT OR REPLACE INTO malaysian_standards (
    object_type,
    ms_code,
    standard_title,
    requirement_type,
    requirement_value,
    requirement_description,
    is_mandatory
) VALUES
(
    'outlet_3pin_ms589',
    'MS 589',
    'Malaysian Standard - Plugs and Socket-Outlets',
    'height',
    '300mm above finished floor level',
    'Standard installation height for power outlets',
    0
),
(
    'outlet_3pin_ms589',
    'MS 589',
    'Malaysian Standard - Plugs and Socket-Outlets',
    'specification',
    '13A, 230V AC, BS 1363 type',
    'Malaysian 3-pin outlet specifications (square pin type)',
    1
);


-- ============================================================
-- 5. basin - Wall-mounted or pedestal basin
-- ============================================================

INSERT OR REPLACE INTO placement_rules (
    object_type,
    alignment_type,
    reference_plane,
    standard_height,
    offset_from_wall,
    rotation_method,
    snapping_enabled,
    snapping_targets,
    rule_description
) VALUES (
    'basin',
    'wall_surface',
    'wall',
    0.85,
    0.05,
    'wall_normal',
    1,
    '["wall_surface"]',
    'Basin mounts to wall, rim at 850mm height above floor'
);

INSERT OR REPLACE INTO connection_requirements (
    object_type,
    primary_surface,
    secondary_surface,
    clearance_front,
    clearance_left,
    clearance_right,
    requires_water_supply,
    requires_drainage,
    min_approach_distance,
    requirements_description
) VALUES (
    'basin',
    'wall',
    'drainage',
    0.5,
    0.2,
    0.2,
    1,
    1,
    0.5,
    'Basin requires wall mounting, water supply (hot/cold), drainage connection. Minimum 500mm front clearance for use.'
);

INSERT OR REPLACE INTO malaysian_standards (
    object_type,
    ms_code,
    standard_title,
    requirement_type,
    requirement_value,
    requirement_description,
    is_mandatory
) VALUES
(
    'basin',
    'MS 1184',
    'Malaysian Standard - Sanitary Appliances',
    'height',
    '850mm rim height above floor',
    'Standard basin installation height',
    0
),
(
    'basin',
    'UBBL',
    'Uniform Building By-Laws',
    'clearance',
    '500mm front clearance minimum',
    'Required clearance for basin use',
    1
);


COMMIT;

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

-- Check placement rules
SELECT
    pr.object_type,
    pr.alignment_type,
    pr.reference_plane,
    pr.rotation_method,
    pr.standard_height
FROM placement_rules pr
ORDER BY pr.object_type;

-- Check connection requirements
SELECT
    cr.object_type,
    cr.primary_surface,
    cr.clearance_front,
    cr.requires_water_supply,
    cr.requires_electrical
FROM connection_requirements cr
ORDER BY cr.object_type;

-- Check Malaysian standards
SELECT
    ms.object_type,
    ms.ms_code,
    ms.requirement_type,
    ms.requirement_value
FROM malaysian_standards ms
ORDER BY ms.object_type, ms.ms_code;
