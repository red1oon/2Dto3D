-- ============================================================
-- OBJECT BEHAVIOR VALIDATION QUERIES
-- Catches classification errors like basin marked as floor_mounted
-- ============================================================
-- Reference: OBJECT_BEHAVIOR_MATRIX.md
-- Date: 2025-11-23
-- ============================================================

-- ============================================================
-- 1. Find objects with MISSING behavior category
-- ============================================================

SELECT
    '❌ MISSING BEHAVIOR' as issue,
    object_type,
    object_name,
    COUNT(*) as affected_objects
FROM object_catalog
WHERE behavior_category IS NULL
GROUP BY object_type, object_name
ORDER BY COUNT(*) DESC;


-- ============================================================
-- 2. Find SUSPICIOUS behavior assignments
-- ============================================================

-- Basins should be WALL-MOUNTED, not floor-mounted!
SELECT
    '❌ BASIN ERROR' as issue,
    object_type,
    behavior_category as wrong_behavior,
    'wall_mounted' as correct_behavior,
    COUNT(*) as affected_objects
FROM object_catalog
WHERE (object_type LIKE '%basin%' OR object_type LIKE '%sink%')
AND behavior_category = 'floor_mounted';

-- Switches should be WALL-MOUNTED
SELECT
    '❌ SWITCH ERROR' as issue,
    object_type,
    behavior_category as wrong_behavior,
    'wall_mounted' as correct_behavior,
    COUNT(*) as affected_objects
FROM object_catalog
WHERE object_type LIKE '%switch%'
AND behavior_category != 'wall_mounted';

-- Outlets should be WALL-MOUNTED
SELECT
    '❌ OUTLET ERROR' as issue,
    object_type,
    behavior_category as wrong_behavior,
    'wall_mounted' as correct_behavior,
    COUNT(*) as affected_objects
FROM object_catalog
WHERE object_type LIKE '%outlet%'
AND behavior_category != 'wall_mounted';

-- Doors should be FLOOR-MOUNTED
SELECT
    '❌ DOOR ERROR' as issue,
    object_type,
    behavior_category as wrong_behavior,
    'floor_mounted' as correct_behavior,
    COUNT(*) as affected_objects
FROM object_catalog
WHERE object_type LIKE '%door%'
AND behavior_category != 'floor_mounted';

-- Toilets should be FLOOR-MOUNTED
SELECT
    '❌ TOILET ERROR' as issue,
    object_type,
    behavior_category as wrong_behavior,
    'floor_mounted' as correct_behavior,
    COUNT(*) as affected_objects
FROM object_catalog
WHERE (object_type LIKE '%toilet%' OR object_type LIKE '%wc%')
AND object_type NOT LIKE '%wall_hung%'
AND behavior_category != 'floor_mounted';


-- ============================================================
-- 3. Verify MS 589 COMPLIANCE (Malaysian Electrical Standards)
-- ============================================================

-- Switches must be at 1.2m height
SELECT
    '⚠️ MS 589 VIOLATION - Switch Height' as issue,
    pr.object_type,
    pr.standard_height as current_height,
    1.2 as required_height_ms589
FROM placement_rules pr
JOIN object_catalog oc ON pr.object_type = oc.object_type
WHERE oc.object_type LIKE '%switch%'
AND pr.standard_height != 1.2;

-- Outlets must be at 0.3m height
SELECT
    '⚠️ MS 589 VIOLATION - Outlet Height' as issue,
    pr.object_type,
    pr.standard_height as current_height,
    0.3 as required_height_ms589
FROM placement_rules pr
JOIN object_catalog oc ON pr.object_type = oc.object_type
WHERE oc.object_type LIKE '%outlet%'
AND pr.standard_height != 0.3;


-- ============================================================
-- 4. Verify PIVOT POINTS are set correctly
-- ============================================================

-- Floor-mounted objects should have bottom_* pivot
SELECT
    '⚠️ PIVOT MISMATCH' as issue,
    object_type,
    behavior_category,
    pivot_point as current_pivot,
    'bottom_center or bottom_center_back' as expected_pivot
FROM object_catalog
WHERE behavior_category = 'floor_mounted'
AND (pivot_point NOT LIKE 'bottom%' OR pivot_point IS NULL)
AND object_type NOT LIKE '%drain%'; -- floor drains are special case

-- Wall-mounted objects should have center or bottom_center pivot
SELECT
    '⚠️ PIVOT MISMATCH' as issue,
    object_type,
    behavior_category,
    pivot_point as current_pivot,
    'center or bottom_center' as expected_pivot
FROM object_catalog
WHERE behavior_category = 'wall_mounted'
AND pivot_point NOT IN ('center', 'bottom_center')
AND pivot_point IS NOT NULL;


-- ============================================================
-- 5. Find objects MISSING placement rules
-- ============================================================

SELECT
    '⚠️ MISSING PLACEMENT RULES' as issue,
    oc.object_type,
    oc.behavior_category,
    COUNT(*) as object_count
FROM object_catalog oc
LEFT JOIN placement_rules pr ON oc.object_type = pr.object_type
WHERE pr.rule_id IS NULL
AND oc.object_type IN (
    'door_single', 'door_double',
    'switch_1gang', 'switch_2gang', 'switch_3gang',
    'outlet_3pin_ms589',
    'toilet', 'basin', 'shower',
    'ceiling_fan', 'ceiling_light'
)
GROUP BY oc.object_type, oc.behavior_category;


-- ============================================================
-- 6. Verify ROTATION methods are appropriate
-- ============================================================

-- Doors should use wall_normal rotation
SELECT
    '⚠️ ROTATION METHOD' as issue,
    object_type,
    rotation_method as current_method,
    'wall_normal' as expected_method
FROM placement_rules
WHERE object_type LIKE '%door%'
AND rotation_method != 'wall_normal';

-- Toilets should use room_entrance rotation
SELECT
    '⚠️ ROTATION METHOD' as issue,
    object_type,
    rotation_method as current_method,
    'room_entrance' as expected_method
FROM placement_rules
WHERE object_type LIKE '%toilet%'
AND rotation_method != 'room_entrance';


-- ============================================================
-- 7. COMPREHENSIVE VALIDATION SUMMARY
-- ============================================================

WITH validation_summary AS (
    SELECT
        object_type,
        behavior_category,
        pivot_point,
        CASE
            WHEN behavior_category IS NULL THEN '❌ Missing behavior'
            WHEN behavior_category = 'floor_mounted' AND pivot_point NOT LIKE 'bottom%' THEN '❌ Wrong pivot'
            WHEN behavior_category = 'wall_mounted' AND pivot_point NOT IN ('center', 'bottom_center') THEN '❌ Wrong pivot'
            ELSE '✅ OK'
        END as validation_status
    FROM object_catalog
    WHERE object_type IN (
        'door_single', 'door_double',
        'switch_1gang', 'switch_2gang', 'switch_3gang',
        'outlet_3pin_ms589',
        'toilet', 'basin',
        'ceiling_fan', 'ceiling_light'
    )
)
SELECT
    validation_status,
    object_type,
    behavior_category,
    pivot_point
FROM validation_summary
ORDER BY
    CASE validation_status
        WHEN '❌ Missing behavior' THEN 1
        WHEN '❌ Wrong pivot' THEN 2
        ELSE 3
    END,
    object_type;


-- ============================================================
-- 8. AUTO-FIX SUGGESTIONS
-- ============================================================

-- Generate UPDATE statements for common fixes
SELECT
    '-- Auto-fix for: ' || object_type as comment,
    'UPDATE object_catalog SET behavior_category = ''wall_mounted'' WHERE object_type = ''' || object_type || ''';' as sql_fix
FROM object_catalog
WHERE (object_type LIKE '%basin%' OR object_type LIKE '%sink%')
AND behavior_category != 'wall_mounted'

UNION ALL

SELECT
    '-- Auto-fix for: ' || object_type,
    'UPDATE object_catalog SET behavior_category = ''wall_mounted'' WHERE object_type = ''' || object_type || ''';'
FROM object_catalog
WHERE object_type LIKE '%switch%'
AND behavior_category != 'wall_mounted'

UNION ALL

SELECT
    '-- Auto-fix for: ' || object_type,
    'UPDATE object_catalog SET behavior_category = ''wall_mounted'' WHERE object_type = ''' || object_type || ''';'
FROM object_catalog
WHERE object_type LIKE '%outlet%'
AND behavior_category != 'wall_mounted';
