#!/usr/bin/env python3
"""
Jetty Designer COMPLETE - v2.0
Full featured designer with resize, add/delete zones, all settings
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import math

class JettyBuilderComplete:
    def __init__(self, root):
        self.root = root
        self.root.title("🚢 Jetty Builder v2.0 COMPLETE")
        self.root.geometry("1600x1000")

        # State
        self.building_width = 90
        self.building_depth = 70
        self.num_floors = 4
        self.current_floor = 0
        self.scale = 6  # pixels per meter
        self.building_type = 'Transport Hub'  # Transport Hub, Office, Residential

        # Auto doors (generated based on building type)
        self.doors = []  # List of door objects with x, y, width, orientation

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

        # Interaction state
        self.dragging = None
        self.resizing = None
        self.resize_handle = None  # 'nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w'
        self.drag_offset = (0, 0)
        self.selected_zone = None

        self.create_ui()
        self.draw()

    def create_ui(self):
        """Create the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel (controls)
        left_panel = ttk.Frame(main_frame, width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_panel.pack_propagate(False)

        # Building settings
        settings_frame = ttk.LabelFrame(left_panel, text="🏗️ Building Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=5)

        ttk.Label(settings_frame, text="Width (m):").grid(row=0, column=0, sticky='w', pady=2)
        self.width_var = tk.StringVar(value=str(self.building_width))
        width_entry = ttk.Entry(settings_frame, textvariable=self.width_var, width=10)
        width_entry.grid(row=0, column=1, pady=2)
        width_entry.bind('<Return>', lambda e: self.update_building())

        ttk.Label(settings_frame, text="Depth (m):").grid(row=1, column=0, sticky='w', pady=2)
        self.depth_var = tk.StringVar(value=str(self.building_depth))
        depth_entry = ttk.Entry(settings_frame, textvariable=self.depth_var, width=10)
        depth_entry.grid(row=1, column=1, pady=2)
        depth_entry.bind('<Return>', lambda e: self.update_building())

        ttk.Label(settings_frame, text="Floors:").grid(row=2, column=0, sticky='w', pady=2)
        self.floors_var = tk.StringVar(value=str(self.num_floors))
        floors_entry = ttk.Entry(settings_frame, textvariable=self.floors_var, width=10)
        floors_entry.grid(row=2, column=1, pady=2)
        floors_entry.bind('<Return>', lambda e: self.update_building())

        ttk.Label(settings_frame, text="Type:").grid(row=3, column=0, sticky='w', pady=2)
        self.type_var = tk.StringVar(value=self.building_type)
        type_combo = ttk.Combobox(settings_frame, textvariable=self.type_var, width=8,
                                  values=['Transport Hub', 'Office', 'Residential'])
        type_combo.grid(row=3, column=1, pady=2)
        type_combo.bind('<<ComboboxSelected>>', lambda e: self.update_building_type())

        ttk.Button(settings_frame, text="Apply Changes", command=self.update_building).grid(row=4, column=0, columnspan=2, pady=5)

        # Atrium settings
        atrium_frame = ttk.LabelFrame(left_panel, text="⬜ Atrium Settings", padding=10)
        atrium_frame.pack(fill=tk.X, pady=5)

        self.atrium_enabled_var = tk.BooleanVar(value=self.atrium_data.get('enabled', True))
        ttk.Checkbutton(atrium_frame, text="Enable Atrium", variable=self.atrium_enabled_var,
                       command=self.update_atrium).grid(row=0, column=0, columnspan=2, sticky='w', pady=2)

        ttk.Label(atrium_frame, text="Start Floor:").grid(row=1, column=0, sticky='w', pady=2, padx=(0,5))
        self.atrium_start_var = tk.StringVar(value=str(self.atrium_data.get('startFloor', 1)))
        atrium_start = ttk.Spinbox(atrium_frame, from_=0, to=10, width=8, textvariable=self.atrium_start_var)
        atrium_start.grid(row=1, column=1, pady=2)
        atrium_start.bind('<Return>', lambda e: self.update_atrium())

        ttk.Label(atrium_frame, text="End Floor:").grid(row=2, column=0, sticky='w', pady=2, padx=(0,5))
        self.atrium_end_var = tk.StringVar(value=str(self.atrium_data.get('endFloor', 3)))
        atrium_end = ttk.Spinbox(atrium_frame, from_=0, to=10, width=8, textvariable=self.atrium_end_var)
        atrium_end.grid(row=2, column=1, pady=2)
        atrium_end.bind('<Return>', lambda e: self.update_atrium())

        ttk.Button(atrium_frame, text="Apply", command=self.update_atrium).grid(row=3, column=0, columnspan=2, pady=5)

        # Floor selection
        floor_frame = ttk.LabelFrame(left_panel, text="🏢 Floor Selection", padding=10)
        floor_frame.pack(fill=tk.X, pady=5)

        btn_frame = ttk.Frame(floor_frame)
        btn_frame.pack()
        for i in range(self.num_floors):
            btn = ttk.Button(btn_frame, text=f"{'GF' if i == 0 else 'L'+str(i)}",
                           command=lambda f=i: self.switch_floor(f), width=5)
            btn.grid(row=i//2, column=i%2, padx=2, pady=2)

        self.floor_label = ttk.Label(floor_frame, text="Current: Ground Floor")
        self.floor_label.pack(pady=5)

        # Zone tools
        tools_frame = ttk.LabelFrame(left_panel, text="🔧 Zone Tools", padding=10)
        tools_frame.pack(fill=tk.X, pady=5)

        ttk.Button(tools_frame, text="➕ Add New Zone", command=self.add_zone).pack(fill=tk.X, pady=2)
        ttk.Button(tools_frame, text="🗑️ Delete Selected Zone", command=self.delete_zone).pack(fill=tk.X, pady=2)
        ttk.Button(tools_frame, text="🚪 Auto Generate Doors", command=self.auto_generate_doors).pack(fill=tk.X, pady=2)

        self.selected_label = ttk.Label(tools_frame, text="Selected: None", foreground='blue')
        self.selected_label.pack(pady=5)

        # File operations
        file_frame = ttk.LabelFrame(left_panel, text="📁 File Operations", padding=10)
        file_frame.pack(fill=tk.X, pady=5)
        ttk.Button(file_frame, text="📂 Load JSON", command=self.load_json).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="💾 Save JSON", command=self.save_json).pack(fill=tk.X, pady=2)

        # Export operations
        export_frame = ttk.LabelFrame(left_panel, text="📤 Export", padding=10)
        export_frame.pack(fill=tk.X, pady=5)
        ttk.Button(export_frame, text="📐 Export to DXF", command=self.export_dxf).pack(fill=tk.X, pady=2)
        ttk.Button(export_frame, text="📄 Export to PDF", command=self.export_pdf).pack(fill=tk.X, pady=2)
        ttk.Button(export_frame, text="🗄️ Export to Bonsai DB", command=self.export_bonsai_db).pack(fill=tk.X, pady=2)

        # Canvas
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(canvas_frame, bg='white', width=1000, height=800)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind mouse events
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag_motion)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<Motion>', self.on_hover)

        # Right panel (info)
        right_panel = ttk.Frame(main_frame, width=280)
        right_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        right_panel.pack_propagate(False)

        info_frame = ttk.LabelFrame(right_panel, text="ℹ️ Instructions", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True)

        info_text = tk.Text(info_frame, wrap=tk.WORD, height=30, width=30)
        info_text.pack(fill=tk.BOTH, expand=True)
        info_text.insert('1.0', """✓ COMPLETE BUILDER ✓

AMENITIES (All Floors):
• LIFT, WASHROOM, STAIRS
• Drag body to MOVE
• Changes sync to all floors

ATRIUM (L1-L3):
• Drag body to MOVE
• Changes sync L1-L3

ZONES (Per Floor):
• Drag body to MOVE
• Drag corners/edges to RESIZE
• Click to SELECT
• Use Zone Tools to add/delete

BUILDING:
• Set width, depth, floors
• Click "Apply Changes"

GRID:
• 5m spacing
• Meter markings

TIP: Resize by dragging
corner or edge handles!""")
        info_text.config(state='disabled')

    def update_atrium(self):
        """Update atrium settings"""
        try:
            self.atrium_data['enabled'] = self.atrium_enabled_var.get()
            self.atrium_data['startFloor'] = int(self.atrium_start_var.get())
            self.atrium_data['endFloor'] = int(self.atrium_end_var.get())
            self.draw()
            messagebox.showinfo("Success", f"Atrium updated: {'Enabled' if self.atrium_data['enabled'] else 'Disabled'}\nFloors: L{self.atrium_data['startFloor']}-L{self.atrium_data['endFloor']}")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid floor numbers")

    def update_building_type(self):
        """Update building type and regenerate features"""
        self.building_type = self.type_var.get()
        self.auto_generate_doors()  # Regenerate doors for new type
        self.draw()
        messagebox.showinfo("Success", f"Building type changed to: {self.building_type}\nDoors auto-generated!")

    def auto_generate_doors(self):
        """Auto generate doors based on building type"""
        self.doors = []
        half_width = self.building_width / 2
        half_depth = self.building_depth / 2

        if self.building_type == 'Transport Hub':
            # Main entrance (front, center)
            self.doors.append({
                'x': 0, 'y': -half_depth,
                'width': 12, 'height': 0.3,
                'type': 'sliding_glass', 'label': 'Main Entrance'
            })

            # Boarding gates (rear)
            gate_spacing = self.building_width / 4
            for i in range(3):
                gate_x = -half_width + gate_spacing * (i + 0.5)
                self.doors.append({
                    'x': gate_x, 'y': half_depth,
                    'width': 4, 'height': 0.3,
                    'type': 'boarding_gate', 'label': f'Gate {i+1}'
                })

        elif self.building_type == 'Office':
            # Main entrance (front)
            self.doors.append({
                'x': 0, 'y': -half_depth,
                'width': 3, 'height': 0.3,
                'type': 'revolving', 'label': 'Main Entrance'
            })

            # Side emergency exits
            self.doors.append({
                'x': -half_width, 'y': 0,
                'width': 2, 'height': 0.3,
                'type': 'emergency', 'label': 'Emergency Exit'
            })
            self.doors.append({
                'x': half_width, 'y': 0,
                'width': 2, 'height': 0.3,
                'type': 'emergency', 'label': 'Emergency Exit'
            })

        elif self.building_type == 'Residential':
            # Lobby entrance
            self.doors.append({
                'x': 0, 'y': -half_depth,
                'width': 2.5, 'height': 0.3,
                'type': 'standard', 'label': 'Lobby'
            })

        messagebox.showinfo("Doors Generated", f"{len(self.doors)} doors created for {self.building_type}")

    def update_building(self):
        """Update building dimensions"""
        try:
            self.building_width = float(self.width_var.get())
            self.building_depth = float(self.depth_var.get())
            new_floors = int(self.floors_var.get())

            # Add or remove floors
            while len(self.floors_data) < new_floors:
                level = len(self.floors_data)
                self.floors_data.append({
                    'level': level,
                    'zones': {
                        'ticketing': {'label': 'SHOPS', 'x': -20, 'y': 0, 'width': 15, 'height': 20},
                        'waiting': {'label': 'SHOPS', 'x': 0, 'y': 0, 'width': 20, 'height': 20},
                        'retail': {'label': 'SHOPS', 'x': 20, 'y': 0, 'width': 15, 'height': 20},
                        'boarding': {'label': 'BOARDING', 'x': 0, 'y': 25, 'width': 40, 'height': 10}
                    }
                })

            while len(self.floors_data) > new_floors:
                self.floors_data.pop()

            self.num_floors = new_floors
            self.draw()
            messagebox.showinfo("Success", "Building settings updated!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")

    def switch_floor(self, floor):
        """Switch to a different floor"""
        self.current_floor = floor
        floor_names = ['Ground Floor', '1st Floor', '2nd Floor', '3rd Floor', '4th Floor', '5th Floor']
        self.floor_label.config(text=f"Current: {floor_names[floor] if floor < len(floor_names) else f'Floor {floor}'}")
        self.selected_zone = None
        self.selected_label.config(text="Selected: None")
        self.draw()

    def add_zone(self):
        """Add a new zone to current floor"""
        if self.current_floor >= len(self.floors_data):
            return

        # Generate unique zone name
        zone_num = len(self.floors_data[self.current_floor]['zones']) + 1
        zone_name = f"zone{zone_num}"

        # Add zone at center
        self.floors_data[self.current_floor]['zones'][zone_name] = {
            'label': f'ZONE {zone_num}',
            'x': 0, 'y': 0,
            'width': 15, 'height': 15
        }

        self.draw()
        messagebox.showinfo("Added", f"New zone added: ZONE {zone_num}")

    def delete_zone(self):
        """Delete selected zone"""
        if not self.selected_zone or self.current_floor >= len(self.floors_data):
            messagebox.showwarning("Warning", "No zone selected")
            return

        if self.selected_zone in ['lift', 'washroom', 'staircase', 'atrium']:
            messagebox.showwarning("Warning", "Cannot delete amenities/atrium")
            return

        floor = self.floors_data[self.current_floor]
        if self.selected_zone in floor['zones']:
            del floor['zones'][self.selected_zone]
            self.selected_zone = None
            self.selected_label.config(text="Selected: None")
            self.draw()
            messagebox.showinfo("Deleted", "Zone deleted")

    def draw(self):
        """Draw the canvas"""
        self.canvas.delete('all')

        canvas_width = self.canvas.winfo_width() if self.canvas.winfo_width() > 1 else 1000
        canvas_height = self.canvas.winfo_height() if self.canvas.winfo_height() > 1 else 800
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        # Draw grid (5m spacing)
        for x in range(-50, 51, 5):
            px = center_x + x * self.scale
            self.canvas.create_line(px, 0, px, canvas_height, fill='#f0f0f0')
            if x % 10 == 0:
                self.canvas.create_text(px, 15, text=f"{x}m", fill='#95a5a6', font=('Arial', 8))

        for y in range(-50, 51, 5):
            py = center_y + y * self.scale
            self.canvas.create_line(0, py, canvas_width, py, fill='#f0f0f0')
            if y % 10 == 0:
                self.canvas.create_text(15, py, text=f"{y}m", fill='#95a5a6', font=('Arial', 8))

        # Draw building outline
        bx = center_x - (self.building_width * self.scale) / 2
        by = center_y - (self.building_depth * self.scale) / 2
        bw = self.building_width * self.scale
        bh = self.building_depth * self.scale

        # Glass walls for Transport Hub (curtain wall style)
        if self.building_type == 'Transport Hub':
            # Draw glass effect (light blue tint on all walls)
            glass_color = '#e3f2fd'
            self.canvas.create_rectangle(bx, by, bx+bw, by+bh, outline='', fill=glass_color, stipple='gray12')

            # Mullions (vertical glass supports every 3m)
            mullion_spacing = 3 * self.scale  # 3 meters
            for x_offset in range(0, int(bw), int(mullion_spacing)):
                self.canvas.create_line(bx + x_offset, by, bx + x_offset, by + bh, fill='#90a4ae', width=1)
            for y_offset in range(0, int(bh), int(mullion_spacing)):
                self.canvas.create_line(bx, by + y_offset, bx + bw, by + y_offset, fill='#90a4ae', width=1)

            # Thick outline for structure
            self.canvas.create_rectangle(bx, by, bx+bw, by+bh, outline='#607d8b', width=4)
        else:
            # Standard outline for non-Transport Hub
            self.canvas.create_rectangle(bx, by, bx+bw, by+bh, outline='black', width=3)

        # Draw doors
        for door in self.doors:
            self.draw_door(door, center_x, center_y)

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
                self.draw_zone(zone_name, zone, zone_colors.get(zone_name, '#95a5a6'), center_x, center_y)

        # Draw amenities
        self.draw_amenity('lift', '#34495e', 'LIFT', center_x, center_y)
        self.draw_amenity('washroom', '#8e44ad', 'WASHROOM', center_x, center_y)
        self.draw_amenity('staircase', '#16a085', 'STAIRS', center_x, center_y)

        # Draw atrium (if on correct floors)
        if (self.atrium_data.get('enabled', False) and
            self.current_floor >= self.atrium_data.get('startFloor', 1) and
            self.current_floor <= self.atrium_data.get('endFloor', 3)):
            self.draw_atrium(center_x, center_y)

    def draw_zone(self, name, zone, color, center_x, center_y):
        """Draw a zone with resize handles"""
        zx = center_x + zone['x'] * self.scale
        zy = center_y + zone['y'] * self.scale
        zw = zone['width'] * self.scale
        zh = zone['height'] * self.scale

        is_selected = (self.selected_zone == name)
        is_dragging = (self.dragging and self.dragging[0] == 'zone' and self.dragging[1] == name)
        is_resizing = (self.resizing and self.resizing[0] == 'zone' and self.resizing[1] == name)

        # Zone fill
        self.canvas.create_rectangle(
            zx - zw/2, zy - zh/2, zx + zw/2, zy + zh/2,
            fill=color, outline=color, stipple='gray25',
            width=4 if (is_selected or is_dragging or is_resizing) else 2
        )

        # Label
        self.canvas.create_text(zx, zy, text=zone['label'], fill='white', font=('Arial', 10, 'bold'))

        # Resize handles (if selected)
        if is_selected or is_resizing:
            handle_size = 8
            handles = [
                ('nw', zx - zw/2, zy - zh/2),
                ('ne', zx + zw/2, zy - zh/2),
                ('sw', zx - zw/2, zy + zh/2),
                ('se', zx + zw/2, zy + zh/2),
                ('n', zx, zy - zh/2),
                ('s', zx, zy + zh/2),
                ('w', zx - zw/2, zy),
                ('e', zx + zw/2, zy)
            ]
            for handle, hx, hy in handles:
                self.canvas.create_rectangle(
                    hx - handle_size/2, hy - handle_size/2,
                    hx + handle_size/2, hy + handle_size/2,
                    fill='white', outline=color, width=2
                )

    def draw_amenity(self, name, color, label, center_x, center_y):
        """Draw an amenity"""
        amenity = self.fixed_amenities[name]
        x = center_x + amenity['x'] * self.scale
        y = center_y + amenity['y'] * self.scale
        w = amenity['width'] * self.scale
        h = amenity['height'] * self.scale

        is_dragging = (self.dragging and self.dragging[0] == 'amenity' and self.dragging[1] == name)

        self.canvas.create_rectangle(
            x - w/2, y - h/2, x + w/2, y + h/2,
            fill=color, outline=color, stipple='gray25', width=3 if is_dragging else 2
        )
        self.canvas.create_text(x, y - 5, text=label, fill=color, font=('Arial', 10, 'bold'))
        self.canvas.create_text(x, y + 8, text='(All Floors)', fill=color, font=('Arial', 8))

    def draw_atrium(self, center_x, center_y):
        """Draw the atrium"""
        x = center_x + self.atrium_data['x'] * self.scale
        y = center_y + self.atrium_data['y'] * self.scale
        w = self.atrium_data['width'] * self.scale
        h = self.atrium_data['height'] * self.scale

        is_dragging = (self.dragging and self.dragging[0] == 'amenity' and self.dragging[1] == 'atrium')

        self.canvas.create_rectangle(
            x - w/2, y - h/2, x + w/2, y + h/2,
            fill='white', outline='#95a5a6', stipple='gray12',
            width=4 if is_dragging else 2, dash=(10, 5)
        )
        self.canvas.create_text(x, y - 10, text='ATRIUM', fill='#95a5a6', font=('Arial', 12, 'bold'))
        self.canvas.create_text(x, y + 10, text='(Void L1-L3)', fill='#95a5a6', font=('Arial', 9))

    def draw_door(self, door, center_x, center_y):
        """Draw a door"""
        x = center_x + door['x'] * self.scale
        y = center_y + door['y'] * self.scale
        w = door['width'] * self.scale
        h = door.get('height', 0.3) * self.scale

        door_type = door.get('type', 'standard')

        # Determine door orientation (on which wall)
        half_width = self.building_width * self.scale / 2
        half_depth = self.building_depth * self.scale / 2

        if door_type == 'sliding_glass':
            # Wide glass sliding doors (Transport Hub entrance)
            self.canvas.create_rectangle(x - w/2, y - 2, x + w/2, y + 2,
                                        fill='#64b5f6', outline='#1976d2', width=2)
            # Sliding panels indication
            for i in range(int(w / (self.scale * 2))):
                panel_x = x - w/2 + i * (self.scale * 2)
                self.canvas.create_line(panel_x, y - 2, panel_x, y + 2, fill='#1976d2', width=1)

        elif door_type == 'boarding_gate':
            # Boarding gate (double doors)
            self.canvas.create_rectangle(x - w/2, y - 2, x + w/2, y + 2,
                                        fill='#ff9800', outline='#e65100', width=2)
            # Center split line
            self.canvas.create_line(x, y - 2, x, y + 2, fill='#e65100', width=2)

        elif door_type == 'revolving':
            # Revolving door (circle)
            radius = w / 2
            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                   fill='#81c784', outline='#388e3c', width=2)

        elif door_type == 'emergency':
            # Emergency exit (red)
            self.canvas.create_rectangle(x - w/2, y - 2, x + w/2, y + 2,
                                        fill='#e57373', outline='#c62828', width=2)

        else:
            # Standard door
            self.canvas.create_rectangle(x - w/2, y - 2, x + w/2, y + 2,
                                        fill='#a1887f', outline='#5d4037', width=2)

        # Label (small)
        if door.get('label'):
            self.canvas.create_text(x, y - 10, text=door['label'],
                                   fill='#424242', font=('Arial', 7))

    def get_resize_handle(self, x, y, zx, zy, zw, zh):
        """Check if click is on a resize handle"""
        threshold = 8

        # Corners
        if abs(x - (zx - zw/2)) < threshold and abs(y - (zy - zh/2)) < threshold:
            return 'nw'
        if abs(x - (zx + zw/2)) < threshold and abs(y - (zy - zh/2)) < threshold:
            return 'ne'
        if abs(x - (zx - zw/2)) < threshold and abs(y - (zy + zh/2)) < threshold:
            return 'sw'
        if abs(x - (zx + zw/2)) < threshold and abs(y - (zy + zh/2)) < threshold:
            return 'se'

        # Edges
        if abs(x - zx) < threshold and abs(y - (zy - zh/2)) < threshold:
            return 'n'
        if abs(x - zx) < threshold and abs(y - (zy + zh/2)) < threshold:
            return 's'
        if abs(x - (zx - zw/2)) < threshold and abs(y - zy) < threshold:
            return 'w'
        if abs(x - (zx + zw/2)) < threshold and abs(y - zy) < threshold:
            return 'e'

        return None

    def hit_test(self, x, y):
        """Check what element is under the cursor"""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        # Check zones (for resize handles first if selected)
        if self.current_floor < len(self.floors_data):
            floor = self.floors_data[self.current_floor]
            for zone_name, zone in floor['zones'].items():
                zx = center_x + zone['x'] * self.scale
                zy = center_y + zone['y'] * self.scale
                zw = zone['width'] * self.scale
                zh = zone['height'] * self.scale

                # Check resize handles if this zone is selected
                if self.selected_zone == zone_name:
                    handle = self.get_resize_handle(x, y, zx, zy, zw, zh)
                    if handle:
                        return ('resize', zone_name, handle)

                # Check zone body
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
        hit = self.hit_test(event.x, event.y)

        if hit:
            if hit[0] == 'resize':
                # Start resizing
                self.resizing = (hit[0], hit[1])
                self.resize_handle = hit[2]
                self.drag_offset = (event.x, event.y)
                self.canvas.config(cursor='crosshair')
            elif hit[0] == 'zone':
                # Select and start dragging zone
                self.selected_zone = hit[1]
                self.selected_label.config(text=f"Selected: {hit[1].upper()}")
                self.dragging = hit
                self.drag_offset = (event.x, event.y)
                self.canvas.config(cursor='fleur')
                self.draw()
            else:
                # Dragging amenity
                self.dragging = hit
                self.drag_offset = (event.x, event.y)
                self.canvas.config(cursor='fleur')
        else:
            self.selected_zone = None
            self.selected_label.config(text="Selected: None")
            self.draw()

    def on_drag_motion(self, event):
        """Handle mouse drag"""
        if self.resizing:
            # Handle resizing
            _, zone_name = self.resizing
            if self.current_floor >= len(self.floors_data):
                return

            zone = self.floors_data[self.current_floor]['zones'].get(zone_name)
            if not zone:
                return

            dx = (event.x - self.drag_offset[0]) / self.scale
            dy = (event.y - self.drag_offset[1]) / self.scale

            # Apply resize based on handle
            if 'e' in self.resize_handle:
                zone['width'] += dx
            if 'w' in self.resize_handle:
                zone['width'] -= dx
                zone['x'] += dx / 2
            if 's' in self.resize_handle:
                zone['height'] += dy
            if 'n' in self.resize_handle:
                zone['height'] -= dy
                zone['y'] += dy / 2

            # Minimum size
            zone['width'] = max(5, zone['width'])
            zone['height'] = max(5, zone['height'])

            self.drag_offset = (event.x, event.y)
            self.draw()

        elif self.dragging:
            # Handle dragging
            dx = (event.x - self.drag_offset[0]) / self.scale
            dy = (event.y - self.drag_offset[1]) / self.scale

            drag_type, drag_name = self.dragging

            if drag_type == 'zone' and self.current_floor < len(self.floors_data):
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
        self.resizing = None
        self.resize_handle = None
        self.canvas.config(cursor='arrow')
        self.draw()

    def on_hover(self, event):
        """Handle mouse hover for cursor feedback"""
        if not self.dragging and not self.resizing:
            hit = self.hit_test(event.x, event.y)
            if hit:
                if hit[0] == 'resize':
                    handle = hit[2]
                    cursors = {
                        'nw': 'top_left_corner', 'ne': 'top_right_corner',
                        'sw': 'bottom_left_corner', 'se': 'bottom_right_corner',
                        'n': 'sb_v_double_arrow', 's': 'sb_v_double_arrow',
                        'w': 'sb_h_double_arrow', 'e': 'sb_h_double_arrow'
                    }
                    self.canvas.config(cursor=cursors.get(handle, 'crosshair'))
                else:
                    self.canvas.config(cursor='fleur')
            else:
                self.canvas.config(cursor='arrow')

    def load_json(self):
        """Load design from JSON with full migration support"""
        filename = filedialog.askopenfilename(
            title="Open JSON File",
            initialdir="/home/red1/Downloads",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)

                # Load building settings
                if 'building' in data:
                    self.building_width = data['building'].get('width', 90)
                    self.building_depth = data['building'].get('depth', 70)
                    self.num_floors = data['building'].get('numFloors', 4)
                    self.building_type = data['building'].get('type', 'Transport Hub')
                    self.width_var.set(str(self.building_width))
                    self.depth_var.set(str(self.building_depth))
                    self.floors_var.set(str(self.num_floors))
                    self.type_var.set(self.building_type)

                # Load fixed amenities
                if 'fixedAmenities' in data:
                    self.fixed_amenities.update(data['fixedAmenities'])

                # Migrate old format: extract washroom/staircase from floor 0
                if 'floorsData' in data and len(data['floorsData']) > 0:
                    floor0_amenities = data['floorsData'][0].get('amenities', {})
                    if 'washroom' in floor0_amenities:
                        self.fixed_amenities['washroom'] = floor0_amenities['washroom']
                    if 'staircase' in floor0_amenities:
                        self.fixed_amenities['staircase'] = floor0_amenities['staircase']

                # Load atrium
                if 'atrium' in data or 'atriumData' in data:
                    self.atrium_data = data.get('atrium', data.get('atriumData'))
                    if 'enabled' not in self.atrium_data:
                        self.atrium_data['enabled'] = True
                    # Auto-fix atrium floors
                    if self.atrium_data.get('startFloor', 0) == 0:
                        self.atrium_data['startFloor'] = 1
                        self.atrium_data['endFloor'] = 3

                # Load floors data
                if 'floorsData' in data:
                    self.floors_data = data['floorsData']

                # Load doors
                if 'doors' in data:
                    self.doors = data['doors']
                else:
                    # Auto-generate if not present
                    self.auto_generate_doors()

                # Update atrium UI
                self.atrium_enabled_var.set(self.atrium_data.get('enabled', True))
                self.atrium_start_var.set(str(self.atrium_data.get('startFloor', 1)))
                self.atrium_end_var.set(str(self.atrium_data.get('endFloor', 3)))

                self.draw()
                messagebox.showinfo("Success", f"✓ JSON loaded!\n\nBuilding: {self.building_width}m × {self.building_depth}m\nFloors: {self.num_floors}\nAmenities: {len(self.fixed_amenities)}\nAtrium: L{self.atrium_data.get('startFloor', 1)}-L{self.atrium_data.get('endFloor', 3)}")
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
                        'numFloors': self.num_floors,
                        'type': self.building_type
                    },
                    'structure': {'gridSpacing': 6},
                    'fixedAmenities': self.fixed_amenities,
                    'atrium': self.atrium_data,
                    'floorsData': self.floors_data,
                    'doors': self.doors
                }

                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)

                messagebox.showinfo("Success", f"✓ Saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save JSON:\n{e}")

    def export_dxf(self):
        """Export to DXF format (AutoCAD 2D drawing)"""
        filename = filedialog.asksaveasfilename(
            title="Export to DXF",
            initialdir="/home/red1/Documents/bonsai/2Dto3D/MiniBonsai",
            defaultextension=".dxf",
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")]
        )

        if filename:
            try:
                import ezdxf
                doc = ezdxf.new('R2010')
                msp = doc.modelspace()

                # Draw building outline
                half_w = self.building_width / 2
                half_d = self.building_depth / 2
                msp.add_lwpolyline([
                    (-half_w, -half_d),
                    (half_w, -half_d),
                    (half_w, half_d),
                    (-half_w, half_d),
                    (-half_w, -half_d)
                ], close=True)

                # Draw doors
                for door in self.doors:
                    dx = door['x']
                    dy = door['y']
                    dw = door['width']
                    msp.add_line((dx - dw/2, dy), (dx + dw/2, dy))
                    msp.add_text(door.get('label', 'Door'), dxfattribs={'height': 0.5}).set_placement((dx, dy + 0.5))

                # Draw amenities
                for name, amenity in self.fixed_amenities.items():
                    x, y = amenity['x'], amenity['y']
                    w, h = amenity['width'], amenity['height']
                    msp.add_lwpolyline([
                        (x - w/2, y - h/2),
                        (x + w/2, y - h/2),
                        (x + w/2, y + h/2),
                        (x - w/2, y + h/2),
                        (x - w/2, y - h/2)
                    ], close=True)
                    msp.add_text(name.upper(), dxfattribs={'height': 1.0}).set_placement((x, y))

                # Draw atrium
                if self.atrium_data.get('enabled'):
                    x, y = self.atrium_data['x'], self.atrium_data['y']
                    w, h = self.atrium_data['width'], self.atrium_data['height']
                    msp.add_lwpolyline([
                        (x - w/2, y - h/2),
                        (x + w/2, y - h/2),
                        (x + w/2, y + h/2),
                        (x - w/2, y + h/2),
                        (x - w/2, y - h/2)
                    ], close=True, dxfattribs={'linetype': 'DASHED'})

                # Draw zones for all floors
                for floor_idx, floor in enumerate(self.floors_data):
                    layer_name = f"FLOOR_{floor_idx}"
                    doc.layers.add(layer_name)
                    for zone_name, zone in floor['zones'].items():
                        x, y = zone['x'], zone['y']
                        w, h = zone['width'], zone['height']
                        msp.add_lwpolyline([
                            (x - w/2, y - h/2),
                            (x + w/2, y - h/2),
                            (x + w/2, y + h/2),
                            (x - w/2, y + h/2),
                            (x - w/2, y - h/2)
                        ], close=True, dxfattribs={'layer': layer_name})

                doc.saveas(filename)
                messagebox.showinfo("Success", f"✓ Exported to DXF:\n{filename}")
            except ImportError:
                messagebox.showerror("Error", "ezdxf not installed.\n\nInstall with:\npip3 install ezdxf")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export DXF:\n{e}")

    def export_pdf(self):
        """Export to PDF (2D standard drawing format like TASBLOCK)"""
        filename = filedialog.asksaveasfilename(
            title="Export to PDF",
            initialdir="/home/red1/Documents/bonsai/2Dto3D/MiniBonsai",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if filename:
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A3, landscape
                from reportlab.lib.units import mm

                c = canvas.Canvas(filename, pagesize=landscape(A3))
                width, height = landscape(A3)

                # Title
                c.setFont("Helvetica-Bold", 16)
                c.drawString(30, height - 30, f"{self.building_type} - Floor Plans")

                # Draw each floor
                floors_per_row = 2
                floor_width = width / 2.5
                floor_height = height / 3

                for idx, floor in enumerate(self.floors_data):
                    row = idx // floors_per_row
                    col = idx % floors_per_row

                    offset_x = 50 + col * floor_width
                    offset_y = height - 100 - row * floor_height

                    # Floor label
                    c.setFont("Helvetica-Bold", 12)
                    floor_name = "Ground Floor" if idx == 0 else f"Floor {idx}"
                    c.drawString(offset_x, offset_y + 20, floor_name)

                    # Scale
                    scale_factor = min(floor_width / self.building_width, floor_height / self.building_depth) * 0.8

                    # Building outline
                    c.setLineWidth(2)
                    c.rect(offset_x, offset_y - self.building_depth * scale_factor,
                          self.building_width * scale_factor, self.building_depth * scale_factor)

                    # Zones
                    c.setLineWidth(1)
                    for zone_name, zone in floor['zones'].items():
                        zx = offset_x + (zone['x'] + self.building_width/2) * scale_factor
                        zy = offset_y - (zone['y'] + self.building_depth/2) * scale_factor
                        zw = zone['width'] * scale_factor
                        zh = zone['height'] * scale_factor
                        c.rect(zx - zw/2, zy - zh/2, zw, zh)
                        c.setFont("Helvetica", 8)
                        c.drawString(zx - 10, zy, zone['label'])

                    # Amenities
                    c.setFont("Helvetica", 7)
                    for name, amenity in self.fixed_amenities.items():
                        ax = offset_x + (amenity['x'] + self.building_width/2) * scale_factor
                        ay = offset_y - (amenity['y'] + self.building_depth/2) * scale_factor
                        aw = amenity['width'] * scale_factor
                        ah = amenity['height'] * scale_factor
                        c.rect(ax - aw/2, ay - ah/2, aw, ah)
                        c.drawString(ax - 10, ay, name[:4].upper())

                c.save()
                messagebox.showinfo("Success", f"✓ Exported to PDF:\n{filename}")
            except ImportError:
                messagebox.showerror("Error", "reportlab not installed.\n\nInstall with:\npip3 install reportlab")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export PDF:\n{e}")

    def export_bonsai_db(self):
        """Export to Bonsai database (ARC/STR disciplines with preset beams - POC)"""
        filename = filedialog.asksaveasfilename(
            title="Export to Bonsai DB",
            initialdir="/home/red1/Documents/bonsai/DatabaseFiles",
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db"), ("All files", "*.*")]
        )

        if filename:
            try:
                import sqlite3

                conn = sqlite3.connect(filename)
                cursor = conn.cursor()

                # Create tables (simplified POC structure)
                cursor.execute('''CREATE TABLE IF NOT EXISTS elements (
                    id INTEGER PRIMARY KEY,
                    discipline TEXT,
                    type TEXT,
                    floor INTEGER,
                    x REAL,
                    y REAL,
                    z REAL,
                    width REAL,
                    height REAL,
                    depth REAL,
                    label TEXT
                )''')

                element_id = 1

                # Standard beam preset (POC - 300x600mm RC beams on 6m grid)
                beam_width = 0.3
                beam_depth = 0.6
                grid_spacing = 6.0

                # Add structure (STR discipline) - Grid beams
                for floor_idx in range(self.num_floors):
                    floor_height = floor_idx * 3.0  # 3m per floor

                    # Longitudinal beams (along building width)
                    for y_pos in range(int(-self.building_depth/2), int(self.building_depth/2), int(grid_spacing)):
                        cursor.execute('''INSERT INTO elements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                     (element_id, 'STR', 'BEAM', floor_idx,
                                      0, y_pos, floor_height + 2.4,  # Beams at ceiling level
                                      self.building_width, beam_depth, beam_width,
                                      f'B-L{floor_idx}-{abs(y_pos)}'))
                        element_id += 1

                    # Transverse beams (along building depth)
                    for x_pos in range(int(-self.building_width/2), int(self.building_width/2), int(grid_spacing)):
                        cursor.execute('''INSERT INTO elements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                     (element_id, 'STR', 'BEAM', floor_idx,
                                      x_pos, 0, floor_height + 2.4,
                                      beam_width, beam_depth, self.building_depth,
                                      f'B-T{floor_idx}-{abs(x_pos)}'))
                        element_id += 1

                # Add architecture (ARC discipline)
                # Walls
                cursor.execute('''INSERT INTO elements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (element_id, 'ARC', 'WALL', -1,  # All floors
                              0, -self.building_depth/2, 0, self.building_width, 2.7, 0.2, 'WALL-NORTH'))
                element_id += 1

                # Doors
                for door in self.doors:
                    cursor.execute('''INSERT INTO elements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                 (element_id, 'ARC', 'DOOR', 0,  # Ground floor
                                  door['x'], door['y'], 0, door['width'], 2.1, 0.05, door.get('label', 'DOOR')))
                    element_id += 1

                # Amenities
                for name, amenity in self.fixed_amenities.items():
                    for floor_idx in range(self.num_floors):
                        cursor.execute('''INSERT INTO elements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                     (element_id, 'ARC', name.upper(), floor_idx,
                                      amenity['x'], amenity['y'], floor_idx * 3.0,
                                      amenity['width'], 2.7, amenity['height'], name.upper()))
                        element_id += 1

                # Atrium void
                if self.atrium_data.get('enabled'):
                    for floor_idx in range(self.atrium_data.get('startFloor', 1),
                                          self.atrium_data.get('endFloor', 3) + 1):
                        cursor.execute('''INSERT INTO elements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                     (element_id, 'ARC', 'VOID', floor_idx,
                                      self.atrium_data['x'], self.atrium_data['y'], floor_idx * 3.0,
                                      self.atrium_data['width'], 3.0, self.atrium_data['height'], 'ATRIUM'))
                        element_id += 1

                conn.commit()
                conn.close()

                messagebox.showinfo("Success", f"✓ Exported to Bonsai DB:\n{filename}\n\nElements: {element_id-1}\n- STR beams: {grid_spacing}m grid, 300x600mm\n- ARC walls, doors, amenities\n- Atrium voids")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export to Bonsai DB:\n{e}")

if __name__ == '__main__':
    root = tk.Tk()
    app = JettyBuilderComplete(root)
    root.mainloop()
