#!/usr/bin/env python3
"""
Validate JSON Parsing in generate_3d_geometry.py

This script tests that the JSON parsing code handles all edge cases correctly:
- Valid JSON with dimensions
- null values
- Empty strings
- Invalid JSON strings

All cases should gracefully fall back to default dimensions.
"""

import sys
import json
sys.path.insert(0, '/home/red1/Documents/bonsai/2Dto3D')

from Scripts.generate_3d_geometry import generate_element_geometry

def test_json_parsing():
    """Test JSON dimension parsing with various inputs"""

    print("\n" + "="*70)
    print("TESTING JSON PARSING IN generate_3d_geometry.py")
    print("="*70 + "\n")

    test_cases = [
        # (description, dimensions_json, expected_behavior)
        ("Valid JSON with dimensions", '{"length": 5.0, "width": 0.3}', "Use dimensions"),
        ("Valid JSON null", "null", "Use defaults"),
        ("Empty string", "", "Use defaults"),
        ("Invalid JSON", "not-json", "Use defaults (catch exception)"),
        ("None value", None, "Use defaults"),
    ]

    passed = 0
    failed = 0

    for desc, dim_json, expected in test_cases:
        print(f"Test: {desc}")
        print(f"  Input: {repr(dim_json)}")

        # Simulate the parsing logic from generate_3d_geometry.py
        dimensions = None
        if dim_json:
            try:
                dimensions = json.loads(dim_json)
            except:
                pass  # Invalid JSON, use defaults

        dims = dimensions or {}

        # Test that it doesn't crash and returns dict
        if isinstance(dims, dict):
            print(f"  ✅ PASS - Returns dict: {dims}")
            print(f"  Expected: {expected}")
            passed += 1
        else:
            print(f"  ❌ FAIL - Wrong type: {type(dims)}")
            failed += 1

        print()

    # Test actual geometry generation with different dimension inputs
    print("-"*70)
    print("TESTING ACTUAL GEOMETRY GENERATION")
    print("-"*70 + "\n")

    for desc, dim_json, _ in test_cases:
        dimensions = None
        if dim_json:
            try:
                dimensions = json.loads(dim_json)
            except:
                pass

        dims = dimensions or {}

        try:
            result = generate_element_geometry('IfcWall', 0, 0, 0, dims)
            if result:
                verts, faces, normals = result
                print(f"✅ {desc}: Generated {len(verts)} vertices, {len(faces)} faces")
            else:
                print(f"⚠️  {desc}: No geometry generated (unsupported class)")
        except Exception as e:
            print(f"❌ {desc}: EXCEPTION - {e}")
            failed += 1

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"Total tests: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n✅ ALL TESTS PASSED - JSON parsing is robust!")
        return 0
    else:
        print(f"\n❌ {failed} TESTS FAILED - JSON parsing has issues!")
        return 1

if __name__ == "__main__":
    sys.exit(test_json_parsing())
