"""Utility functions for DXF to XML conversion."""
import math
import re

def get_bbox(vertices):
    """Calculates the bounding box coordinates from vertices."""
    if not vertices:
        return float('inf'), float('inf'), -float('inf'), -float('inf')
    
    min_x = min(v[0] for v in vertices)
    max_x = max(v[0] for v in vertices)
    min_y = min(v[1] for v in vertices)
    max_y = max(v[1] for v in vertices)
    return min_x, min_y, max_x, max_y

def get_bbox_center(vertices):
    """Calculates the center point of a bounding box from vertices."""
    if not vertices:
        return None, None
    min_x = min(v[0] for v in vertices)
    max_x = max(v[0] for v in vertices)
    min_y = min(v[1] for v in vertices)
    max_y = max(v[1] for v in vertices)
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    return center_x, center_y

def get_bbox_dimensions_sorted(vertices):
    """Calculates bounding box dimensions and returns them sorted (smallest, largest)."""
    min_x, min_y, max_x, max_y = get_bbox(vertices)
    if min_x == float('inf'):
        return 0.0, 0.0
    width = max_x - min_x
    height = max_y - min_y
    return round(min(width, height), 3), round(max(width, height), 3)

def get_number_from_layer_name_after_D(layer_name, drilling_prefix):
    """Extracts the number after the specified drilling prefix from layer names."""
    escaped_prefix = re.escape(drilling_prefix)
    match = re.search(rf'{escaped_prefix}(\d+)', layer_name.upper())
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None
