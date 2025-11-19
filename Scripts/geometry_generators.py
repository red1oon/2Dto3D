#!/usr/bin/env python3
"""
Geometry Generators for 2Dto3D Conversion
==========================================

Provides geometry generation functions for different element types.
All generators produce world-positioned vertices (not centered templates).

Architecture:
    - GeometryResult: Data class for geometry output
    - Generator functions: One per element type
    - Factory function: Routes element data to appropriate generator

Usage:
    from geometry_generators import generate_element_geometry

    result = generate_element_geometry(element_data)
    vertices, faces, normals = result.vertices, result.faces, result.normals
"""

import math
from typing import List, Tuple, Dict, Optional, NamedTuple
from abc import ABC, abstractmethod


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class GeometryResult(NamedTuple):
    """Result from geometry generation."""
    vertices: List[Tuple[float, float, float]]
    faces: List[Tuple[int, int, int]]
    normals: List[Tuple[float, float, float]]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def compute_face_normal(v0: Tuple, v1: Tuple, v2: Tuple) -> Tuple[float, float, float]:
    """Compute normal vector for a triangle face."""
    # Edge vectors
    e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
    e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
    # Cross product
    nx = e1[1] * e2[2] - e1[2] * e2[1]
    ny = e1[2] * e2[0] - e1[0] * e2[2]
    nz = e1[0] * e2[1] - e1[1] * e2[0]
    # Normalize
    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length > 0:
        return (nx/length, ny/length, nz/length)
    return (0, 0, 1)


# ============================================================================
# GEOMETRY GENERATORS
# ============================================================================

class BoxGenerator:
    """Generate box geometry at world position."""

    @staticmethod
    def generate(width: float, depth: float, height: float,
                 cx: float, cy: float, cz: float) -> GeometryResult:
        """
        Generate axis-aligned box at world position.

        Args:
            width: Size along X axis (meters)
            depth: Size along Y axis (meters)
            height: Size along Z axis (meters)
            cx, cy, cz: World position of box center (bottom center)
        """
        hx, hy = width/2, depth/2
        vertices = [
            (cx-hx, cy-hy, cz), (cx+hx, cy-hy, cz), (cx+hx, cy+hy, cz), (cx-hx, cy+hy, cz),
            (cx-hx, cy-hy, cz+height), (cx+hx, cy-hy, cz+height),
            (cx+hx, cy+hy, cz+height), (cx-hx, cy+hy, cz+height),
        ]
        faces = [
            (0, 1, 2), (0, 2, 3),  # Bottom
            (4, 7, 6), (4, 6, 5),  # Top
            (0, 4, 5), (0, 5, 1),  # Front
            (2, 6, 7), (2, 7, 3),  # Back
            (0, 3, 7), (0, 7, 4),  # Left
            (1, 5, 6), (1, 6, 2),  # Right
        ]
        normals = [compute_face_normal(vertices[f[0]], vertices[f[1]], vertices[f[2]]) for f in faces]
        return GeometryResult(vertices, faces, normals)


class OrientedBoxGenerator:
    """Generate rotated box geometry at world position."""

    @staticmethod
    def generate(length: float, width: float, height: float,
                 cx: float, cy: float, cz: float, rotation: float) -> GeometryResult:
        """
        Generate box oriented along rotation angle.

        Args:
            length: Size along local X axis (meters)
            width: Size along local Y axis (meters)
            height: Size along Z axis (meters)
            cx, cy, cz: World position of box center
            rotation: Rotation angle in radians (CCW from X axis)
        """
        hl, hw = length/2, width/2
        cos_r = math.cos(rotation)
        sin_r = math.sin(rotation)

        # Local corners (length along X, width along Y)
        local_corners = [(-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw)]

        # Transform to world coordinates
        vertices = []
        for lx, ly in local_corners:
            wx = cx + lx * cos_r - ly * sin_r
            wy = cy + lx * sin_r + ly * cos_r
            vertices.append((wx, wy, cz))
        for lx, ly in local_corners:
            wx = cx + lx * cos_r - ly * sin_r
            wy = cy + lx * sin_r + ly * cos_r
            vertices.append((wx, wy, cz + height))

        faces = [
            (0, 1, 2), (0, 2, 3),  # Bottom
            (4, 7, 6), (4, 6, 5),  # Top
            (0, 4, 5), (0, 5, 1),  # Front
            (2, 6, 7), (2, 7, 3),  # Back
            (0, 3, 7), (0, 7, 4),  # Left
            (1, 5, 6), (1, 6, 2),  # Right
        ]
        normals = [compute_face_normal(vertices[f[0]], vertices[f[1]], vertices[f[2]]) for f in faces]
        return GeometryResult(vertices, faces, normals)


class CylinderGenerator:
    """Generate cylinder geometry at world position."""

    @staticmethod
    def generate(radius: float, height: float, cx: float, cy: float, cz: float,
                 segments: int = 12) -> GeometryResult:
        """
        Generate cylinder at world position.

        Args:
            radius: Cylinder radius (meters)
            height: Cylinder height (meters)
            cx, cy, cz: World position of cylinder center (bottom)
            segments: Number of sides (default 12)
        """
        vertices = [(cx, cy, cz)]  # Bottom center
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            vertices.append((cx + radius * math.cos(angle),
                           cy + radius * math.sin(angle), cz))

        vertices.append((cx, cy, cz + height))  # Top center
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            vertices.append((cx + radius * math.cos(angle),
                           cy + radius * math.sin(angle), cz + height))

        faces = []
        # Bottom cap
        for i in range(segments):
            faces.append((0, 1 + (i + 1) % segments, 1 + i))
        # Top cap
        top_center = segments + 1
        for i in range(segments):
            faces.append((top_center, top_center + 1 + i, top_center + 1 + (i + 1) % segments))
        # Side faces
        for i in range(segments):
            b1 = 1 + i
            b2 = 1 + (i + 1) % segments
            t1 = top_center + 1 + i
            t2 = top_center + 1 + (i + 1) % segments
            faces.append((b1, b2, t2))
            faces.append((b1, t2, t1))

        normals = [compute_face_normal(vertices[f[0]], vertices[f[1]], vertices[f[2]]) for f in faces]
        return GeometryResult(vertices, faces, normals)


class ExtrudedPolylineGenerator:
    """Generate extruded wall geometry from polyline points."""

    @staticmethod
    def generate(points: List[Tuple[float, float]], thickness: float,
                 height: float, cz: float) -> GeometryResult:
        """
        Generate wall by extruding polyline with thickness.

        Args:
            points: List of (x, y) polyline vertices in world coordinates
            thickness: Wall thickness (meters)
            height: Wall height (meters)
            cz: Z elevation of wall base
        """
        if len(points) < 2:
            # Fallback to box for single point
            return BoxGenerator.generate(1.0, thickness, height,
                                        points[0][0], points[0][1], cz)

        vertices = []
        n = len(points)
        ht = thickness / 2

        # For each point, calculate perpendicular offset
        for i in range(n):
            p0 = points[i]

            # Get direction vectors
            if i == 0:
                dx = points[1][0] - points[0][0]
                dy = points[1][1] - points[0][1]
            elif i == n - 1:
                dx = points[n-1][0] - points[n-2][0]
                dy = points[n-1][1] - points[n-2][1]
            else:
                dx = points[i+1][0] - points[i-1][0]
                dy = points[i+1][1] - points[i-1][1]

            # Normalize and get perpendicular
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0.001:
                nx, ny = -dy/length, dx/length
            else:
                nx, ny = 0, 1

            # Offset points (inner and outer)
            vertices.append((p0[0] + nx*ht, p0[1] + ny*ht, cz))
            vertices.append((p0[0] - nx*ht, p0[1] - ny*ht, cz))

        # Add top vertices
        bottom_count = len(vertices)
        for v in vertices[:bottom_count]:
            vertices.append((v[0], v[1], cz + height))

        faces = []
        # Bottom and top caps
        for i in range(n - 1):
            b0, b1 = i*2, i*2 + 1
            b2, b3 = (i+1)*2, (i+1)*2 + 1
            faces.append((b0, b2, b1))
            faces.append((b1, b2, b3))

            t0, t1 = bottom_count + b0, bottom_count + b1
            t2, t3 = bottom_count + b2, bottom_count + b3
            faces.append((t0, t1, t2))
            faces.append((t1, t3, t2))

        # Side faces
        for i in range(n - 1):
            # Outer side
            b0, b2 = i*2, (i+1)*2
            t0, t2 = bottom_count + b0, bottom_count + b2
            faces.append((b0, t0, t2))
            faces.append((b0, t2, b2))

            # Inner side
            b1, b3 = i*2 + 1, (i+1)*2 + 1
            t1, t3 = bottom_count + b1, bottom_count + b3
            faces.append((b1, b3, t3))
            faces.append((b1, t3, t1))

        # End caps
        faces.append((0, 1, bottom_count + 1))
        faces.append((0, bottom_count + 1, bottom_count))
        e0, e1 = (n-1)*2, (n-1)*2 + 1
        faces.append((e0, bottom_count + e0, bottom_count + e1))
        faces.append((e0, bottom_count + e1, e1))

        normals = [compute_face_normal(vertices[f[0]], vertices[f[1]], vertices[f[2]]) for f in faces]
        return GeometryResult(vertices, faces, normals)


class SlabGenerator:
    """Generate thin slab/plate geometry at world position."""

    @staticmethod
    def generate(width: float, depth: float, thickness: float,
                 cx: float, cy: float, cz: float) -> GeometryResult:
        """
        Generate horizontal slab (thin box).

        Args:
            width: Size along X axis (meters)
            depth: Size along Y axis (meters)
            thickness: Slab thickness (meters)
            cx, cy, cz: World position of slab center (bottom)
        """
        return BoxGenerator.generate(width, depth, thickness, cx, cy, cz)


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def generate_element_geometry(elem: Dict, templates: Dict) -> GeometryResult:
    """
    Factory function to generate appropriate geometry for an element.

    Args:
        elem: Element dict with keys: ifc_class, discipline, center_x/y/z,
              rotation_z, length, polyline_points (optional)
        templates: Template parameters from arc_str_element_templates.json

    Returns:
        GeometryResult with vertices, faces, normals at world positions
    """
    ifc_class = elem['ifc_class']
    discipline = elem['discipline']
    cx, cy, cz = elem['center_x'], elem['center_y'], elem['center_z']
    rotation = elem.get('rotation_z', 0)
    length = elem.get('length', 0)

    # Get parameters from templates
    if discipline == 'ARC':
        params = templates.get('arc_elements', {}).get(ifc_class, {}).get('parameters', {})
    else:
        params = templates.get('str_elements', {}).get(ifc_class, {}).get('parameters', {})

    width = params.get('width_m', params.get('thickness_m', 0.5))
    depth = params.get('depth_m', width)
    height = params.get('height_m', 3.0)

    # Select generator based on element type
    if ifc_class == 'IfcColumn':
        # Cylinders for columns
        radius = width / 2
        return CylinderGenerator.generate(radius, height, cx, cy, cz)

    elif ifc_class == 'IfcBeam':
        # Oriented boxes for beams
        beam_length = length if length > 0 else width
        beam_width = params.get('width_m', 0.3)
        beam_depth = params.get('depth_m', 0.7)
        return OrientedBoxGenerator.generate(beam_length, beam_width, beam_depth,
                                            cx, cy, cz, rotation)

    elif ifc_class == 'IfcWall':
        # Check if we have polyline points
        if 'polyline_points' in elem and elem['polyline_points']:
            thickness = params.get('thickness_m', 0.2)
            return ExtrudedPolylineGenerator.generate(elem['polyline_points'],
                                                     thickness, height, cz)
        else:
            # Fallback: oriented box using length
            wall_length = length if length > 0 else width
            thickness = params.get('thickness_m', 0.2)
            return OrientedBoxGenerator.generate(wall_length, thickness, height,
                                                cx, cy, cz, rotation)

    elif ifc_class in ['IfcSlab', 'IfcPlate']:
        # Thin horizontal slabs - use length for both dimensions if only one available
        slab_length = length if length > 0 else width
        # For plates/slabs from LINE entities, make them square-ish
        # or use depth from template if reasonable
        slab_depth = params.get('depth_m', slab_length)
        if slab_depth < 1.0:  # If depth is too small (e.g., wall thickness), use length
            slab_depth = slab_length
        thickness = params.get('thickness_m', 0.15)
        return SlabGenerator.generate(slab_length, slab_depth, thickness, cx, cy, cz)

    else:
        # Default: axis-aligned box
        elem_width = length if length > 0 else width
        return BoxGenerator.generate(elem_width, depth, height, cx, cy, cz)
