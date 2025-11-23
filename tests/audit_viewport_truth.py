#!/usr/bin/env python3
"""
Viewport Audit - Uses viewport_snapshot.py for rendering

This audit wrapper calls the main viewport_snapshot module to generate
a visual snapshot of the database for autonomous validation.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import viewport_snapshot
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from viewport_snapshot import render_database


def main():
    """Run viewport audit using main renderer."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Viewport audit - render database to PNG for validation'
    )
    parser.add_argument('database', help='Path to federation database (.db)')
    parser.add_argument('--output', '-o', help='Output PNG path')
    parser.add_argument('--angle', '-a', default='iso',
                       choices=['iso', 'top', 'front', 'side', 'se'],
                       help='Camera angle preset')
    parser.add_argument('--distance', '-d', type=float, default=1.0,
                       help='Camera distance multiplier')
    parser.add_argument('--resolution', '-r', default='1920x1080',
                       help='Image resolution WxH')

    args = parser.parse_args()

    db_path = Path(args.database)
    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        sys.exit(1)

    # Parse resolution
    try:
        res_w, res_h = map(int, args.resolution.split('x'))
        resolution = (res_w, res_h)
    except:
        print(f"ERROR: Invalid resolution format: {args.resolution}")
        sys.exit(1)

    # Default output path
    if args.output:
        output_path = args.output
    else:
        screenshots_dir = Path(__file__).parent.parent / "Screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(screenshots_dir / f"{db_path.stem}_{timestamp}.png")

    # Use main renderer
    result = render_database(
        str(db_path),
        output_path,
        args.angle,
        args.distance,
        resolution
    )

    if result:
        print(f"\nSnapshot complete: {result}")
        sys.exit(0)
    else:
        print("\nSnapshot failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
