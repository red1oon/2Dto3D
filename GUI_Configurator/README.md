# Mini Bonsai GUI Configurator

**Status: Future Development**

This folder is reserved for the Mini Bonsai GUI that will provide visual editing of MEP and zone configurations.

## Concept

The GUI will allow users to:
- Visually edit zone boundaries (toilet zones, AC zones, etc.)
- Adjust MEP parameters via sliders (spacing, counts, Z-offsets)
- Preview element placement before generation
- Enable/disable specific zones or disciplines
- Fine-tune clash clearances

## Configuration Files

The GUI will edit these JSON configs:
- `../zones_config.json` - Zone definitions and placement
- `../building_config.json` - Building parameters and MEP settings

## Integration

The GUI outputs configuration changes that the backend generators consume:
- `Scripts/mep_generator.py` - MEP element generation classes
- `Scripts/generate_arc_str_database.py` - Main generation orchestrator

## Development Notes

- Separate programming effort from backend generators
- Python with tkinter or PyQt recommended
- Real-time preview would require viewport_snapshot integration

## For Now

Use JSON editor to modify configs directly:
```bash
# Edit zone configurations
nano ../zones_config.json

# Edit MEP parameters
nano ../building_config.json
```

Then regenerate:
```bash
python3 ../Scripts/generate_arc_str_database.py
```
