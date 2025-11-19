#!/usr/bin/env python3
"""
Export all Terminal 1 DXF files to PNG images
Shows exactly what's in each DXF file - raw geometry as modeller would see
"""

import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt
from pathlib import Path

def export_dxf_to_png(dxf_path: str, output_path: str, title: str):
    """Export DXF to PNG showing all geometry"""

    print(f"\nExporting: {Path(dxf_path).name}")

    try:
        # Load DXF
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # Count entities
        entity_count = len(list(msp))
        print(f"  Total entities: {entity_count:,}")

        # Setup matplotlib backend
        fig = plt.figure(figsize=(20, 16))
        ax = fig.add_axes([0.05, 0.05, 0.9, 0.9])
        ctx = RenderContext(doc)
        backend = MatplotlibBackend(ax)

        # Render
        Frontend(ctx, backend).draw_layout(msp, finalize=True)

        # Add title
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)

        # Save
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        print(f"  ✓ Saved: {output_path}")

    except Exception as e:
        print(f"  ✗ Error: {e}")

def main():
    base_path = Path(__file__).parent.parent / 'SourceFiles' / 'TERMINAL1DXF'
    output_dir = Path(__file__).parent.parent / 'SourceFiles' / 'DXF_PlanViews'
    output_dir.mkdir(exist_ok=True)

    # All DXF files
    dxf_files = [
        {
            'path': base_path / '01 ARCHITECT' / '2. BANGUNAN TERMINAL 1.dxf',
            'title': 'Terminal 1 - ARCHITECT (All Floors)',
            'output': 'ARC_AllFloors.png'
        },
        {
            'path': base_path / '02 STRUCTURE' / 'T1-2.0_Lyt_GB_e2P2_240711.dxf',
            'title': 'Terminal 1 - STRUCTURE Ground/Basement (GB)',
            'output': 'STR_GB.png'
        },
        {
            'path': base_path / '02 STRUCTURE' / 'T1-2.1_Lyt_1FB_e1P1_240530.dxf',
            'title': 'Terminal 1 - STRUCTURE 1st Floor (1F)',
            'output': 'STR_1F.png'
        },
        {
            'path': base_path / '02 STRUCTURE' / 'T1-2.3_Lyt_3FB_e1P1_240530.dxf',
            'title': 'Terminal 1 - STRUCTURE 3rd Floor (3F)',
            'output': 'STR_3F.png'
        },
        {
            'path': base_path / '02 STRUCTURE' / 'T1-2.4_Lyt_4FB-6FB_e1P1_240530.dxf',
            'title': 'Terminal 1 - STRUCTURE 4th-6th Floors (4F-6F)',
            'output': 'STR_4F-6F.png'
        },
        {
            'path': base_path / '02 STRUCTURE' / 'T1-2.5_Lyt_5R_Truss_e3P0_29Oct\'23.dxf',
            'title': 'Terminal 1 - STRUCTURE Roof Truss (RF)',
            'output': 'STR_RF.png'
        }
    ]

    print("\n" + "="*80)
    print("EXPORTING ALL TERMINAL 1 DXF FILES TO PNG")
    print("="*80)

    for dxf_info in dxf_files:
        output_path = output_dir / dxf_info['output']
        export_dxf_to_png(
            str(dxf_info['path']),
            str(output_path),
            dxf_info['title']
        )

    print("\n" + "="*80)
    print(f"✓ All DXF files exported to: {output_dir}")
    print("="*80)

if __name__ == '__main__':
    main()
