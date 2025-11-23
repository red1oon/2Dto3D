#!/usr/bin/env python3
"""
Placement Artifacts Generator
==============================
Creates permanent, human-readable artifacts from placement process.

WHY THIS MATTERS:
1. User can examine EXACTLY how each object was placed
2. Serves as training data for future AI improvements
3. Documents "ground truth" for validation
4. Enables future releases to eliminate AI dependency

Output Artifacts:
- placement_results.json (machine-readable)
- placement_report.md (human-readable)
- placement_audit_trail.csv (Excel-compatible)
- ground_truth_dataset.json (AI training data)

Author: DeepSeek Integration Team
Date: 2025-11-23
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict


class PlacementArtifactGenerator:
    """Generates comprehensive placement artifacts"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.output_dir = self.project_root / "output_artifacts"
        self.input_dir = self.project_root / "input_templates"

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)

        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def generate_all_artifacts(self,
                               template: Dict,
                               placed_objects: List[Dict],
                               project_name: str = "TB-LKTN"):
        """Generate all artifact types"""

        print("=" * 70)
        print("GENERATING PLACEMENT ARTIFACTS")
        print("=" * 70)
        print()

        # 1. Machine-readable JSON
        json_path = self.generate_json_artifact(placed_objects, project_name)
        print(f"✅ JSON: {json_path}")

        # 2. Human-readable Markdown report
        md_path = self.generate_markdown_report(template, placed_objects, project_name)
        print(f"✅ Markdown: {md_path}")

        # 3. Excel-compatible CSV
        csv_path = self.generate_csv_audit_trail(placed_objects, project_name)
        print(f"✅ CSV: {csv_path}")

        # 4. Ground truth for AI training
        gt_path = self.generate_ground_truth_dataset(template, placed_objects, project_name)
        print(f"✅ Ground Truth: {gt_path}")

        print()
        print("=" * 70)
        print("✅ ALL ARTIFACTS GENERATED")
        print("=" * 70)
        print()

        return {
            'json': str(json_path),
            'markdown': str(md_path),
            'csv': str(csv_path),
            'ground_truth': str(gt_path)
        }

    def generate_json_artifact(self, placed_objects: List[Dict], project_name: str) -> Path:
        """Machine-readable placement results"""

        artifact = {
            'metadata': {
                'project': project_name,
                'generated_at': datetime.now().isoformat(),
                'generator': 'DeepSeek Geometric Rules Engine v1.0',
                'total_objects': len(placed_objects)
            },
            'placements': placed_objects
        }

        output_path = self.output_dir / f"{project_name}_placement_results_{self.timestamp}.json"

        with open(output_path, 'w') as f:
            json.dump(artifact, f, indent=2)

        return output_path

    def generate_markdown_report(self,
                                  template: Dict,
                                  placed_objects: List[Dict],
                                  project_name: str) -> Path:
        """Human-readable placement report"""

        output_path = self.output_dir / f"{project_name}_placement_report_{self.timestamp}.md"

        with open(output_path, 'w') as f:
            f.write(f"# Placement Report: {project_name}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Engine:** DeepSeek Geometric Rules Engine v1.0\n\n")

            f.write("---\n\n")

            # Project summary
            f.write("## Project Summary\n\n")
            project_info = template.get('project', {})
            f.write(f"- **Name:** {project_info.get('name', 'N/A')}\n")
            f.write(f"- **Reference:** {project_info.get('drawing_reference', 'N/A')}\n")
            f.write(f"- **Location:** {project_info.get('location', 'N/A')}\n")
            f.write(f"- **Total Objects:** {len(placed_objects)}\n\n")

            # Statistics
            f.write("## Placement Statistics\n\n")

            type_counts = {}
            for obj in placed_objects:
                t = obj['object_type']
                type_counts[t] = type_counts.get(t, 0) + 1

            f.write("| Object Type | Count |\n")
            f.write("|-------------|-------|\n")
            for obj_type, count in sorted(type_counts.items()):
                f.write(f"| {obj_type} | {count} |\n")
            f.write("\n")

            # Detailed placements by room
            f.write("## Detailed Placements\n\n")

            by_room = {}
            for obj in placed_objects:
                room = obj['room']
                if room not in by_room:
                    by_room[room] = []
                by_room[room].append(obj)

            for room_name, objects in sorted(by_room.items()):
                f.write(f"### {room_name.replace('_', ' ').title()}\n\n")

                for obj in objects:
                    f.write(f"#### {obj['name']}\n\n")
                    f.write(f"- **Type:** {obj['object_type']}\n")
                    f.write(f"- **Pivot:** {obj['pivot_point']}\n")

                    raw_pos = obj['raw_position']
                    final_pos = obj['final_position']

                    f.write(f"- **Position:**\n")
                    f.write(f"  - Raw: X={raw_pos[0]:.3f}m, Y={raw_pos[1]:.3f}m, Z={raw_pos[2]:.3f}m\n")
                    f.write(f"  - Final: X={final_pos[0]:.3f}m, Y={final_pos[1]:.3f}m, Z={final_pos[2]:.3f}m\n")

                    if abs(final_pos[2] - raw_pos[2]) > 0.01:
                        z_change = final_pos[2] - raw_pos[2]
                        f.write(f"  - **Height adjusted:** {z_change:+.3f}m\n")

                    f.write(f"- **Rotation:**\n")
                    f.write(f"  - Wall normal: {obj['rotation_wall_normal_deg']:.1f}°\n")
                    f.write(f"  - Room entrance: {obj['rotation_room_entrance_deg']:.1f}°\n")

                    if obj.get('rules_applied'):
                        f.write(f"- **Rules Applied:**\n")
                        for rule in obj['rules_applied']:
                            f.write(f"  - {rule}\n")

                    f.write("\n")

            # Validation
            f.write("## Validation Results\n\n")

            f.write("### MS 589 Compliance (Malaysian Electrical Standards)\n\n")

            switches = [o for o in placed_objects if 'switch' in o['object_type']]
            outlets = [o for o in placed_objects if 'outlet' in o['object_type']]

            if switches:
                f.write("**Switches (should be @ 1.2m):**\n\n")
                for s in switches:
                    z = s['final_position'][2]
                    status = "✅ PASS" if abs(z - 1.2) < 0.01 else "❌ FAIL"
                    f.write(f"- {s['name']}: Z={z:.3f}m {status}\n")
                f.write("\n")

            if outlets:
                f.write("**Outlets (should be @ 0.3m):**\n\n")
                for o in outlets:
                    z = o['final_position'][2]
                    status = "✅ PASS" if abs(z - 0.3) < 0.01 else "❌ FAIL"
                    f.write(f"- {o['name']}: Z={z:.3f}m {status}\n")
                f.write("\n")

            f.write("### Floor-Mounted Objects (should be @ Z=0)\n\n")

            floor_objects = [o for o in placed_objects if o['object_type'] in ['door_single', 'toilet']]

            for obj in floor_objects:
                z = obj['final_position'][2]
                status = "✅ PASS" if abs(z) < 0.01 else "❌ FAIL"
                f.write(f"- {obj['name']}: Z={z:.3f}m {status}\n")

            f.write("\n---\n\n")
            f.write("**Generated by:** DeepSeek Geometric Rules Engine\n")
            f.write("**Purpose:** Permanent audit trail of object placements\n")

        return output_path

    def generate_csv_audit_trail(self, placed_objects: List[Dict], project_name: str) -> Path:
        """Excel-compatible CSV audit trail"""

        output_path = self.output_dir / f"{project_name}_placement_audit_{self.timestamp}.csv"

        with open(output_path, 'w', newline='') as f:
            fieldnames = [
                'name', 'room', 'object_type', 'pivot_point',
                'raw_x', 'raw_y', 'raw_z',
                'final_x', 'final_y', 'final_z',
                'height_adjusted', 'rotation_wall_normal', 'rotation_room_entrance',
                'rules_count', 'rules_summary'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for obj in placed_objects:
                raw_pos = obj['raw_position']
                final_pos = obj['final_position']

                writer.writerow({
                    'name': obj['name'],
                    'room': obj['room'],
                    'object_type': obj['object_type'],
                    'pivot_point': obj['pivot_point'],
                    'raw_x': f"{raw_pos[0]:.3f}",
                    'raw_y': f"{raw_pos[1]:.3f}",
                    'raw_z': f"{raw_pos[2]:.3f}",
                    'final_x': f"{final_pos[0]:.3f}",
                    'final_y': f"{final_pos[1]:.3f}",
                    'final_z': f"{final_pos[2]:.3f}",
                    'height_adjusted': f"{final_pos[2] - raw_pos[2]:+.3f}",
                    'rotation_wall_normal': f"{obj['rotation_wall_normal_deg']:.1f}",
                    'rotation_room_entrance': f"{obj['rotation_room_entrance_deg']:.1f}",
                    'rules_count': len(obj.get('rules_applied', [])),
                    'rules_summary': '; '.join(obj.get('rules_applied', []))
                })

        return output_path

    def generate_ground_truth_dataset(self,
                                       template: Dict,
                                       placed_objects: List[Dict],
                                       project_name: str) -> Path:
        """Ground truth dataset for future AI training"""

        output_path = self.output_dir / f"{project_name}_ground_truth_{self.timestamp}.json"

        # Format for AI training: input → output pairs
        training_data = {
            'metadata': {
                'purpose': 'Ground truth for AI training - DeepSeek geometric placement',
                'project': project_name,
                'generated_at': datetime.now().isoformat(),
                'description': 'Each example shows: template input → correct placement output',
                'usage': 'Future AI models can learn from these verified correct placements'
            },
            'building_context': {
                'walls': template.get('building', {}).get('walls', []),
                'rooms': template.get('building', {}).get('rooms', [])
            },
            'examples': []
        }

        for obj in placed_objects:
            example = {
                'input': {
                    'object_type': obj['object_type'],
                    'raw_position': obj['raw_position'],
                    'room': obj['room']
                },
                'output': {
                    'final_position': obj['final_position'],
                    'pivot_point': obj['pivot_point'],
                    'rotation': {
                        'wall_normal_deg': obj['rotation_wall_normal_deg'],
                        'room_entrance_deg': obj['rotation_room_entrance_deg']
                    },
                    'rules_applied': obj.get('rules_applied', [])
                },
                'verification': {
                    'height_adjusted': obj['final_position'][2] - obj['raw_position'][2],
                    'malaysian_standards_compliant': self._check_ms589_compliance(obj)
                }
            }

            training_data['examples'].append(example)

        with open(output_path, 'w') as f:
            json.dump(training_data, f, indent=2)

        return output_path

    def _check_ms589_compliance(self, obj: Dict) -> bool:
        """Check if object meets MS 589 standards"""
        obj_type = obj['object_type']
        z = obj['final_position'][2]

        if 'switch' in obj_type:
            return abs(z - 1.2) < 0.01
        elif 'outlet' in obj_type:
            return abs(z - 0.3) < 0.01
        elif obj_type in ['door_single', 'toilet']:
            return abs(z) < 0.01
        elif obj_type == 'basin':
            return abs(z - 0.85) < 0.01

        return True  # Unknown types pass by default


def main():
    """Generate artifacts from latest placement test"""

    # Project structure - use script directory
    script_dir = Path(__file__).parent
    project_root = script_dir

    # Load latest results - relative paths
    results_path = script_dir / "TB_LKTN_placement_results.json"
    template_path = script_dir / "input_templates" / "TB_LKTN_template.json"

    if not results_path.exists():
        print("❌ No placement results found. Run test_full_pipeline.py first.")
        return

    with open(results_path, 'r') as f:
        placed_objects = json.load(f)

    with open(template_path, 'r') as f:
        template = json.load(f)

    # Generate artifacts in new structure
    generator = PlacementArtifactGenerator(str(project_root))

    artifacts = generator.generate_all_artifacts(template, placed_objects, "TB-LKTN")

    print("\nGenerated Artifacts in new structure:")
    print(f"📁 Project root: {project_root}")
    print(f"📄 JSON (machine): {artifacts['json']}")
    print(f"📝 Markdown (human): {artifacts['markdown']}")
    print(f"📊 CSV (Excel): {artifacts['csv']}")
    print(f"🎓 Ground Truth (AI training): {artifacts['ground_truth']}")
    print()
    print("These artifacts serve as:")
    print("1. Permanent record of placement decisions")
    print("2. Validation documentation for users")
    print("3. Training data for future AI improvements")
    print("4. Audit trail for standards compliance")
    print()


if __name__ == "__main__":
    main()
