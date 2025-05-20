"""
Panel mirroring utilities for DXF processing.
"""
import ezdxf
from typing import List, Tuple

def find_right_sheet_border(doc, sheet_border_layer) -> ezdxf.entities.LWPolyline:
    """Find the rightmost border polyline in the given sheet border layer."""
    borders = [e for e in doc.modelspace() if e.dxftype() == 'LWPOLYLINE' and e.dxf.layer.upper() == sheet_border_layer.upper()]
    if not borders:
        raise ValueError(f"No borders found in layer {sheet_border_layer}")
    
    # Sort by right edge (max X) of bounding box
    def max_x(entity):
        points = list(entity.get_points())
        return max(p[0] for p in points)
    
    # Get the rightmost border
    right_border = max(borders, key=max_x)
    print(f"DEBUG: Found right sheet border with bounds: {list(right_border.get_points())}")
    return right_border

def get_entities_within_border(doc, border) -> List:
    """Return all entities whose reference point is inside the border's bounding box."""
    points = list(border.get_points())
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    tolerance = 1.0  # Add tolerance for border detection
    entities = []
    
    print(f"DEBUG: Searching for entities within border bbox: X[{min_x}, {max_x}], Y[{min_y}, {max_y}]")
    
    for e in doc.modelspace():
        if e is border or e.dxf.layer.upper() == '_ABF_SHEET_BORDER':
            continue
            
        entity_points = []
        try:
            if e.dxftype() == 'CIRCLE':
                entity_points = [(e.dxf.center[0], e.dxf.center[1])]
            elif e.dxftype() == 'LWPOLYLINE':
                verts = list(e.vertices())
                if verts:
                    # For polylines, check if any vertex is within bounds
                    entity_points = [(v[0], v[1]) for v in verts]
            elif hasattr(e.dxf, 'center'):
                entity_points = [(e.dxf.center[0], e.dxf.center[1])]
            elif hasattr(e.dxf, 'start'):
                entity_points = [(e.dxf.start[0], e.dxf.start[1])]
        except Exception as ex:
            print(f"DEBUG: Error checking entity {e.dxftype()}: {ex}")
            continue
            
        # Check if any point is within the border (with tolerance)
        for x, y in entity_points:
            if (min_x - tolerance <= x <= max_x + tolerance and 
                min_y - tolerance <= y <= max_y + tolerance):
                entities.append(e)
                print(f"DEBUG: Found entity {e.dxftype()} in layer {e.dxf.layer} at ({x}, {y})")
                break  # One point within border is enough
    return entities

def mirror_entities(entities, border_bbox: Tuple[float, float], axis_x: float):
    """Mirror entities along the given vertical axis (axis_x)."""
    mirrored = []
    print(f"DEBUG: Mirroring {len(entities)} entities around x={axis_x}")
    
    for e in entities:
        try:
            clone = e.copy()
            print(f"DEBUG: Mirroring entity of type {e.dxftype()} in layer {e.dxf.layer}")
            
            if e.dxftype() == 'CIRCLE':
                x, y = e.dxf.center[0], e.dxf.center[1]
                z = e.dxf.center[2] if len(e.dxf.center) > 2 else 0
                clone.dxf.center = (2*axis_x - x, y, z)
                print(f"DEBUG: Mirrored circle from ({x}, {y}) to ({2*axis_x - x}, {y})")
            
            elif e.dxftype() == 'LWPOLYLINE':
                verts = list(e.vertices())
                new_verts = [(2*axis_x - v[0], v[1]) for v in verts]
                if hasattr(clone, 'vertices'):
                    clone.vertices = new_verts
                else:
                    clone.set_points(new_verts)
                print(f"DEBUG: Mirrored polyline with {len(verts)} vertices")
            
            elif hasattr(e.dxf, 'start') and hasattr(e.dxf, 'end'):
                x1, y1 = e.dxf.start[0], e.dxf.start[1]
                x2, y2 = e.dxf.end[0], e.dxf.end[1]
                clone.dxf.start = (2*axis_x - x1, y1)
                clone.dxf.end = (2*axis_x - x2, y2)
                print(f"DEBUG: Mirrored line from ({x1}, {y1})-({x2}, {y2})")
            
            else:
                print(f"DEBUG: Skipping unsupported entity type: {e.dxftype()}")
                continue
                
            # Ensure layers are preserved
            if hasattr(e.dxf, 'layer'):
                clone.dxf.layer = e.dxf.layer
            
            mirrored.append(clone)
        except Exception as ex:
            print(f"DEBUG: Error mirroring entity {e.dxftype()}: {ex}")
            continue
    
    return mirrored

def add_entities_to_doc(doc, entities):
    """Add entities to the DXF document's modelspace."""
    msp = doc.modelspace()
    for e in entities:
        msp.add_entity(e)

def pair_overlapping_panels(panel_list: List[Tuple[float, float, float, float]]):
    """Pair panels whose bounding boxes overlap."""
    pairs = []
    used = set()
    for i, a in enumerate(panel_list):
        if i in used:
            continue
        for j, b in enumerate(panel_list):
            if i == j or j in used:
                continue
            if (a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]):
                pairs.append((a, b))
                used.add(i)
                used.add(j)
                break
    return pairs
