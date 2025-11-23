# Transit 3D Model Sources

## Free Models to Download

### Priority 1 - Direct Download Available

| Item | Source | URL | License | Format |
|------|--------|-----|---------|--------|
| Bicycle Stand | Sketchfab | https://sketchfab.com/3d-models/cc0-bicycle-stand-4-597656d383f94bca8fa098905a126ee1 | CC0 | OBJ, FBX, glTF |
| Ticket Booth | Sketchfab | https://sketchfab.com/3d-models/ticket-booth-7e12559eed534b5699c4262e7e1a6bb1 | Free | Various |
| Crowd Control Barrier | Sketchfab | https://sketchfab.com/3d-models/crowd-control-barrier-3cb00ccf0a7e4a6ba6aafcce80810fbe | Free | Blender |
| Digital Signage Pylon | Sketchfab | https://sketchfab.com/3d-models/digital-signage-pylon-outdoor-d78e202f273345e4b4411e873ab67d78 | Free | Various |
| Baggage Claim Band | Sketchfab | https://sketchfab.com/3d-models/airport-baggage-claim-band-2254cba114a34dfab0a6e70991a831e6 | Free | Various |
| Life Vest | Sketchfab | https://sketchfab.com/3d-models/life-vest-life-jacket-8481ac383f5348529d366c99cf86ab8e | Free | Various |
| Digital Signage Display | CGTrader | https://www.cgtrader.com/free-3d-models/electronics/other/digital-signage-display | Free | Various |

### Priority 2 - Browse Collections

| Category | Source | URL | Notes |
|----------|--------|-----|-------|
| Vending Machines | Sketchfab | https://sketchfab.com/tags/vending-machine | Filter: downloadable, free |
| Airport Benches | TurboSquid | https://www.turbosquid.com/Search/3D-Models/free/airport-bench | 200+ free models |
| Kiosks | Sketchfab | https://sketchfab.com/tags/kiosk | Filter: downloadable, free |
| Monitors/Displays | Sketchfab | https://sketchfab.com/tags/monitor | Filter: downloadable, free |

## Models to Create (Not Found Free)

These items need to be created as simple parametric models:

1. **Life Jacket Cabinet** - Wall-mounted storage box with handle
2. **USB Charging Station** - Vertical kiosk with ports
3. **Luggage Weighing Scale** - Platform with display
4. **Weather Display Monitor** - Wall-mounted screen
5. **Currency Exchange Booth** - Small enclosed counter
6. **Retractable Belt Stanchion** - Post with belt cassette

## Download Instructions

### Sketchfab
1. Create free account at sketchfab.com
2. Navigate to model URL
3. Click "Download 3D Model"
4. Select OBJ or glTF format
5. Extract to `SourceFiles/3D_Library/`

### CGTrader
1. Create free account at cgtrader.com
2. Navigate to model URL
3. Click "Free Download"
4. Select preferred format
5. Extract to `SourceFiles/3D_Library/`

## Conversion Workflow

1. Download models to `SourceFiles/3D_Library/`
2. Run `python Scripts/convert_models_to_library.py`
3. Models converted and added to `DatabaseFiles/geometry_library.db`

## File Organization

```
SourceFiles/
  3D_Library/
    bicycle_stand/
      model.obj
      model.mtl
      textures/
    ticket_booth/
    vending_machine/
    ...
```
