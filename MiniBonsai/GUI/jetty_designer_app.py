#!/usr/bin/env python3
"""
Jetty Designer Desktop App - v1.1
Full featured designer with draggable amenities
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import math

class JettyDesignerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚢 Jetty Designer v1.2 COMPLETE")
        self.root.geometry("1400x900")

        # State
        self.building_width = 90  # meters
        self.building_depth = 70  # meters
        self.num_floors = 4
        self.current_floor = 0
        self.scale = 6  # pixels per meter

        # Fixed amenities (all floors synced)
        self.fixed_amenities = {
            'lift': {'x': 42.25, 'y': -4.42, 'width': 4.5, 'height': 13.5},
            'washroom': {'x': 31.0, 'y': -30.83, 'width': 27.33, 'height': 7.67},
            'staircase': {'x': -1.0, 'y': -19.25, 'width': 27.67, 'height': 5.5}
        }

        # Atrium (L1-L3)
        self.atrium_data = {
            'x': 1.92, 'y': 3.17,
            'width': 48.83, 'height': 37.67,
            'startFloor': 1, 'endFloor': 3,
            'enabled': True
        }

        # Zones per floor
        self.floors_data = []
        for i in range(self.num_floors):
            self.floors_data.append({
                'level': i,
                'zones': {
                    'ticketing': {'label': 'TICKETING' if i == 0 else 'SHOPS', 'x': -20, 'y': 0, 'width': 15, 'height': 20},
                    'waiting': {'label': 'WAITING' if i == 0 else 'SHOPS', 'x': 0, 'y': 0, 'width': 20, 'height': 20},
                    'retail': {'label': 'RETAIL' if i == 0 else 'SHOPS', 'x': 20, 'y': 0, 'width': 15, 'height': 20},
                    'boarding': {'label': 'BOARDING', 'x': 0, 'y': 25, 'width': 40, 'height': 10}
                }
            })

        # Dragging state
        self.dragging = None
        self.drag_offset = (0, 0)

        self.create_ui()
        self.draw()

    def create_ui(self):
        """Create the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel (controls)
        left_panel = ttk.Frame(main_frame, width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_panel.pack_propagate(False)

        # Floor selection
        ttk.Label(left_panel, text="🏢 Floor Selection", font=('Arial', 12, 'bold')).pack(pady=5)
        floor_frame = ttk.Frame(left_panel)
        floor_frame.pack(fill=tk.X, padx=5, pady=5)

        for i in range(self.num_floors):
            btn = ttk.Button(floor_frame, text=f"{'GF' if i == 0 else 'L'+str(i)}",
                           command=lambda f=i: self.switch_floor(f), width=5)
            btn.grid(row=i//2, column=i%2, padx=2, pady=2)

        self.floor_label = ttk.Label(left_panel, text="Current: Ground Floor")
        self.floor_label.pack()

        # File operations
        ttk.Separator(left_panel, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(left_panel, text="📁 File Operations", font=('Arial', 12, 'bold')).pack(pady=5)
        ttk.Button(left_panel, text="📂 Load JSON", command=self.load_json).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(left_panel, text="💾 Save JSON", command=self.save_json).pack(fill=tk.X, padx=5, pady=2)

        # Status
        ttk.Separator(left_panel, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(left_panel, text="ℹ️ Draggable Elements", font=('Arial', 12, 'bold')).pack(pady=5)
        status_text = tk.Text(left_panel, height=15, width=30, wrap=tk.WORD)
        status_text.pack(fill=tk.BOTH, expand=True, padx=5)
        status_text.insert('1.0', """✓ COMPLETE DESIGNER ✓

Amenities (All Floors Synced):
• LIFT (dark gray)
• WASHROOM (purple)
• STAIRCASE (teal)
  → Drag to move ALL floors!

Atrium (L1-L3 Synced):
• ATRIUM (white void)
  → Drag to move on L1-L3!

Zones (Per Floor Independent):
• TICKETING/SHOPS (blue)
• WAITING/SHOPS (green)
• RETAIL/SHOPS (yellow)
• BOARDING (red)
  → Drag per floor!

Grid: 5m spacing
Rulers: Meter by meter""")
        status_text.config(state='disabled')

        # Canvas
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(canvas_frame, bg='white', width=1000, height=800)
        self.canvas.pack()

        # Bind mouse events
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<Motion>', self.on_hover)

    def switch_floor(self, floor):
        """Switch to a different floor"""
        self.current_floor = floor
        floor_names = ['Ground Floor', '1st Floor', '2nd Floor', '3rd Floor', '4th Floor', '5th Floor']
        self.floor_label.config(text=f"Current: {floor_names[floor] if floor < len(floor_names) else f'Floor {floor}'}")
        self.draw()

    def draw(self):
        """Draw the canvas"""
        self.canvas.delete('all')

        # Calculate canvas center
        canvas_width = self.canvas.winfo_width() if self.canvas.winfo_width() > 1 else 1000
        canvas_height = self.canvas.winfo_height() if self.canvas.winfo_height() > 1 else 800
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        # Draw grid
        for x in range(-50, 51, 5):
            px = center_x + x * self.scale
            self.canvas.create_line(px, 0, px, canvas_height, fill='#f0f0f0')
            if x % 5 == 0:
                self.canvas.create_text(px, 15, text=f"{x}m", fill='#95a5a6', font=('Arial', 8))

        for y in range(-50, 51, 5):
            py = center_y + y * self.scale
            self.canvas.create_line(0, py, canvas_width, py, fill='#f0f0f0')
            if y % 5 == 0:
                self.canvas.create_text(15, py, text=f"{y}m", fill='#95a5a6', font=('Arial', 8))

        # Draw building outline
        bx = center_x - (self.building_width * self.scale) / 2
        by = center_y - (self.building_depth * self.scale) / 2
        bw = self.building_width * self.scale
        bh = self.building_depth * self.scale
        self.canvas.create_rectangle(bx, by, bx+bw, by+bh, outline='black', width=3)

        # Draw zones for current floor
        if self.current_floor < len(self.floors_data):
            floor = self.floors_data[self.current_floor]
            zone_colors = {
                'ticketing': '#3498db',
                'waiting': '#2ecc71',
                'retail': '#f1c40f',
                'boarding': '#e74c3c'
            }

            for zone_name, zone in floor['zones'].items():
                zx = center_x + zone['x'] * self.scale
                zy = center_y + zone['y'] * self.scale
                zw = zone['width'] * self.scale
                zh = zone['height'] * self.scale
                color = zone_colors.get(zone_name, 'gray')

                # Check if this zone is being dragged
                is_dragging = (self.dragging and self.dragging[0] == 'zone' and self.dragging[1] == zone_name)

                # Draw zone
                self.canvas.create_rectangle(
                    zx - zw/2, zy - zh/2, zx + zw/2, zy + zh/2,
                    fill=color, outline=color, stipple='gray25', width=4 if is_dragging else 2
                )
                self.canvas.create_text(zx, zy, text=zone['label'], fill='white', font=('Arial', 10, 'bold'))

        # Draw amenities
        self.draw_amenity('lift', '#34495e', 'LIFT', center_x, center_y)
        self.draw_amenity('washroom', '#8e44ad', 'WASHROOM', center_x, center_y)
        self.draw_amenity('staircase', '#16a085', 'STAIRS', center_x, center_y)

        # Draw atrium (if on correct floors)
        if (self.atrium_data.get('enabled', False) and
            self.current_floor >= self.atrium_data.get('startFloor', 1) and
            self.current_floor <= self.atrium_data.get('endFloor', 3)):
            self.draw_atrium(center_x, center_y)

    def draw_amenity(self, name, color, label, center_x, center_y):
        """Draw an amenity"""
        amenity = self.fixed_amenities[name]
        x = center_x + amenity['x'] * self.scale
        y = center_y + amenity['y'] * self.scale
        w = amenity['width'] * self.scale
        h = amenity['height'] * self.scale

        # Check if this amenity is being dragged
        is_dragging = (self.dragging and self.dragging[0] == 'amenity' and self.dragging[1] == name)

        # Box
        self.canvas.create_rectangle(
            x - w/2, y - h/2, x + w/2, y + h/2,
            fill=color, outline=color, stipple='gray25', width=3 if is_dragging else 2,
            tags=name
        )
        self.canvas.create_text(x, y - 5, text=label, fill=color, font=('Arial', 10, 'bold'))
        self.canvas.create_text(x, y + 8, text='(All Floors)', fill=color, font=('Arial', 8))

    def draw_atrium(self, center_x, center_y):
        """Draw the atrium"""
        x = center_x + self.atrium_data['x'] * self.scale
        y = center_y + self.atrium_data['y'] * self.scale
        w = self.atrium_data['width'] * self.scale
        h = self.atrium_data['height'] * self.scale

        # Check if atrium is being dragged
        is_dragging = (self.dragging and self.dragging[0] == 'amenity' and self.dragging[1] == 'atrium')

        self.canvas.create_rectangle(
            x - w/2, y - h/2, x + w/2, y + h/2,
            fill='white', outline='#95a5a6', stipple='gray12',
            width=4 if is_dragging else 2,
            dash=(10, 5), tags='atrium'
        )
        self.canvas.create_text(x, y - 10, text='ATRIUM', fill='#95a5a6', font=('Arial', 12, 'bold'))
        self.canvas.create_text(x, y + 10, text='(Void L1-L3)', fill='#95a5a6', font=('Arial', 9))

    def hit_test(self, x, y):
        """Check if click hits any draggable element"""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        # Check zones first (so they're easier to grab)
        if self.current_floor < len(self.floors_data):
            floor = self.floors_data[self.current_floor]
            for zone_name, zone in floor['zones'].items():
                zx = center_x + zone['x'] * self.scale
                zy = center_y + zone['y'] * self.scale
                zw = zone['width'] * self.scale
                zh = zone['height'] * self.scale
                if zx - zw/2 <= x <= zx + zw/2 and zy - zh/2 <= y <= zy + zh/2:
                    return ('zone', zone_name)

        # Check atrium
        if (self.atrium_data.get('enabled', False) and
            self.current_floor >= self.atrium_data.get('startFloor', 1) and
            self.current_floor <= self.atrium_data.get('endFloor', 3)):
            ax = center_x + self.atrium_data['x'] * self.scale
            ay = center_y + self.atrium_data['y'] * self.scale
            aw = self.atrium_data['width'] * self.scale
            ah = self.atrium_data['height'] * self.scale
            if ax - aw/2 <= x <= ax + aw/2 and ay - ah/2 <= y <= ay + ah/2:
                return ('amenity', 'atrium')

        # Check amenities
        for name, amenity in self.fixed_amenities.items():
            ax = center_x + amenity['x'] * self.scale
            ay = center_y + amenity['y'] * self.scale
            aw = amenity['width'] * self.scale
            ah = amenity['height'] * self.scale
            if ax - aw/2 <= x <= ax + aw/2 and ay - ah/2 <= y <= ay + ah/2:
                return ('amenity', name)

        return None

    def on_click(self, event):
        """Handle mouse click"""
        self.dragging = self.hit_test(event.x, event.y)
        if self.dragging:
            self.drag_offset = (event.x, event.y)
            self.canvas.config(cursor='fleur')

    def on_drag(self, event):
        """Handle mouse drag"""
        if self.dragging:
            dx = (event.x - self.drag_offset[0]) / self.scale
            dy = (event.y - self.drag_offset[1]) / self.scale

            drag_type, drag_name = self.dragging

            if drag_type == 'zone' and self.current_floor < len(self.floors_data):
                # Move zone on current floor only
                self.floors_data[self.current_floor]['zones'][drag_name]['x'] += dx
                self.floors_data[self.current_floor]['zones'][drag_name]['y'] += dy
            elif drag_type == 'amenity':
                if drag_name == 'atrium':
                    self.atrium_data['x'] += dx
                    self.atrium_data['y'] += dy
                elif drag_name in self.fixed_amenities:
                    self.fixed_amenities[drag_name]['x'] += dx
                    self.fixed_amenities[drag_name]['y'] += dy

            self.drag_offset = (event.x, event.y)
            self.draw()

    def on_release(self, event):
        """Handle mouse release"""
        self.dragging = None
        self.canvas.config(cursor='arrow')
        self.draw()

    def on_hover(self, event):
        """Handle mouse hover"""
        if not self.dragging:
            hit = self.hit_test(event.x, event.y)
            self.canvas.config(cursor='fleur' if hit else 'arrow')

    def load_json(self):
        """Load design from JSON"""
        filename = filedialog.askopenfilename(
            title="Open JSON File",
            initialdir="/home/red1/Downloads",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)

                # Migrate old format if needed
                if 'fixedAmenities' in data:
                    self.fixed_amenities = data['fixedAmenities']

                    # If washroom/staircase missing, get from floor 0
                    if 'floorsData' in data and len(data['floorsData']) > 0:
                        floor0_amenities = data['floorsData'][0].get('amenities', {})
                        if 'washroom' not in self.fixed_amenities and 'washroom' in floor0_amenities:
                            self.fixed_amenities['washroom'] = floor0_amenities['washroom']
                        if 'staircase' not in self.fixed_amenities and 'staircase' in floor0_amenities:
                            self.fixed_amenities['staircase'] = floor0_amenities['staircase']

                # Handle atrium
                if 'atrium' in data or 'atriumData' in data:
                    self.atrium_data = data.get('atrium', data.get('atriumData'))
                    # Ensure enabled key exists
                    if 'enabled' not in self.atrium_data:
                        self.atrium_data['enabled'] = True
                    # Fix atrium floors if needed (should be L1-L3, not L0-L1)
                    if self.atrium_data.get('startFloor', 0) == 0:
                        self.atrium_data['startFloor'] = 1
                        self.atrium_data['endFloor'] = 3

                if 'building' in data:
                    self.building_width = data['building'].get('width', 90)
                    self.building_depth = data['building'].get('depth', 70)
                    self.num_floors = data['building'].get('numFloors', 4)
                if 'floorsData' in data:
                    self.floors_data = data['floorsData']

                self.draw()
                messagebox.showinfo("Success", f"JSON loaded successfully!\n\nMigrated {len(self.fixed_amenities)} amenities\nAtrium: L{self.atrium_data.get('startFloor', 1)}-L{self.atrium_data.get('endFloor', 3)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load JSON:\n{e}")

    def save_json(self):
        """Save design to JSON"""
        filename = filedialog.asksaveasfilename(
            title="Save JSON File",
            initialdir="/home/red1/Documents/bonsai/2Dto3D/MiniBonsai",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                data = {
                    'building': {
                        'width': self.building_width,
                        'depth': self.building_depth,
                        'gates': 3,
                        'numFloors': self.num_floors
                    },
                    'structure': {'gridSpacing': 6},
                    'fixedAmenities': self.fixed_amenities,
                    'atrium': self.atrium_data,
                    'floorsData': self.floors_data
                }

                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)

                messagebox.showinfo("Success", f"Saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save JSON:\n{e}")

if __name__ == '__main__':
    root = tk.Tk()
    app = JettyDesignerApp(root)
    root.mainloop()
