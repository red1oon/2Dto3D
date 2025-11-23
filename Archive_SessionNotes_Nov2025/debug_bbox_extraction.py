#!/usr/bin/env python3
"""
Debug script to test bbox extraction on sample DXF entities.
"""

import ezdxf
from pathlib import Path

def test_bbox_extraction(dxf_path, max_entities=20):
    """Test bbox extraction on sample entities."""
    print(f"Testing bbox extraction on: {dxf_path.name}")
    print("=" * 80)

    doc = ezdxf.readfile(str(dxf_path))
    modelspace = doc.modelspace()

    tested = 0
    for entity in modelspace:
        if tested >= max_entities:
            break

        layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else '0'
        entity_type = entity.dxftype()

        # Only test STR entities
        if not ('BEAM' in layer.upper() or 'COLUMN' in layer.upper() or 'COL' in layer.upper()):
            continue

        print(f"\nEntity {tested + 1}:")
        print(f"  Type: {entity_type}")
        print(f"  Layer: {layer}")

        # Test ezdxf's bounding_box method
        if hasattr(entity, 'bounding_box'):
            try:
                bbox = entity.bounding_box()
                if bbox:
                    print(f"  ✅ Has bounding_box method")
                    print(f"     Min: ({bbox.extmin.x:.2f}, {bbox.extmin.y:.2f}, {bbox.extmin.z:.2f})")
                    print(f"     Max: ({bbox.extmax.x:.2f}, {bbox.extmax.y:.2f}, {bbox.extmax.z:.2f})")
                    length = abs(bbox.extmax.x - bbox.extmin.x)
                    width = abs(bbox.extmax.y - bbox.extmin.y)
                    height = abs(bbox.extmax.z - bbox.extmin.z)
                    print(f"     Dimensions: {length:.2f} × {width:.2f} × {height:.2f}")
                else:
                    print(f"  ⚠️  bounding_box() returned None")
            except Exception as e:
                print(f"  ❌ bounding_box() failed: {e}")
        else:
            print(f"  ❌ No bounding_box method")

        # Test get_points for LWPOLYLINE
        if entity_type in ('LWPOLYLINE', 'POLYLINE'):
            try:
                points = list(entity.get_points())
                print(f"  Points: {len(points)}")
                if points:
                    xs = [pt[0] for pt in points]
                    ys = [pt[1] for pt in points]
                    print(f"     X range: [{min(xs):.2f}, {max(xs):.2f}] = {max(xs)-min(xs):.2f}")
                    print(f"     Y range: [{min(ys):.2f}, {max(ys):.2f}] = {max(ys)-min(ys):.2f}")
            except Exception as e:
                print(f"  ❌ get_points() failed: {e}")

        tested += 1

    print(f"\n{'=' * 80}")
    print(f"Tested {tested} entities")

if __name__ == "__main__":
    # Test on 1F STR DXF
    str_dxf = Path("/home/red1/Documents/bonsai/2Dto3D/SourceFiles/TERMINAL1DXF/02 STRUCTURE/T1-2.1_Lyt_1FB_e1P1_240530.dxf")

    if str_dxf.exists():
        test_bbox_extraction(str_dxf)
    else:
        print(f"File not found: {str_dxf}")
