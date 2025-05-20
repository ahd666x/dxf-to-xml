"""Process panel machining entities from DXF to XML."""
import re
from .machining_operations import (
    create_drilling_xml,
    create_pocket_xml,
    create_groove_xml,
    _extract_depth_from_layer,
    _validate_depth
)
from .coordinates import convert_coords_to_panel_system
from ..utils.config import DXF_LAYER_CONFIG

def process_machining_entities_for_panel(doc, panel_element, panel_group_info, panel_length, panel_width, panel_thickness, config):
    """
    Process machining entities for a panel, handling back-side operations based on mirrored panels.
    For back-capable panels:
    - Right side panels in the _ABF_SHEET_BORDER define both front and back operations
    - Left side panels only get front-side operations
    - Back-side operations are mirrored horizontally
    """
    machines_element = panel_element.find('Machines')
    borders_in_group = panel_group_info['borders']
    panel_type = panel_group_info['type']
    sheet_border_front_bbox = panel_group_info['sheet_border_front_bbox']
    sheet_border_back_bbox = panel_group_info['sheet_border_back_bbox']
    primary_bbox_panel = panel_group_info['primary_bbox']
    secondary_bbox_panel = panel_group_info.get('secondary_bbox')

    # Calculate overall BBox for all borders in this panel group
    group_min_x, group_min_y = float('inf'), float('inf')
    group_max_x, group_max_y = -float('inf'), -float('inf')

    for border_entity_in_group in borders_in_group:
        border_vertices = list(border_entity_in_group.vertices())
        if not border_vertices:
            continue
        min_x = min(v[0] for v in border_vertices)
        max_x = max(v[0] for v in border_vertices)
        min_y = min(v[1] for v in border_vertices)
        max_y = max(v[1] for v in border_vertices)
        group_min_x = min(group_min_x, min_x)
        group_min_y = min(group_min_y, min_y)
        group_max_x = max(group_max_x, max_x)
        group_max_y = max(group_max_y, max_y)

    tolerance = 1.0
    print(f"DEBUG: اسکان و پردازش موجودیت‌های ماشینکاری برای پنل فیزیکی...")

    # Determine if panel is in right side (back) sheet
    is_right_side = False
    is_back_capable = panel_type == 'back_capable'
    if sheet_border_back_bbox and is_back_capable:
        back_sheet_center_x = (sheet_border_back_bbox[0] + sheet_border_back_bbox[2]) / 2
        panel_center_x = (primary_bbox_panel[0] + primary_bbox_panel[2]) / 2
        is_right_side = panel_center_x > back_sheet_center_x
        print(f"DEBUG: Panel position: {'Right side' if is_right_side else 'Left side'} "
              f"of sheet border (center_x: {panel_center_x:.1f}, back_sheet_center: {back_sheet_center_x:.1f})")

    for entity in doc.modelspace():
        # Skip border entities themselves and sheet borders
        if (entity in borders_in_group or 
            (entity.dxftype() == 'LWPOLYLINE' and 
             entity.dxf.layer.upper() == config['sheet_border'].upper())):
            continue

        # Get entity reference point for containment check
        entity_point = _get_entity_reference_point(entity)
        if not _is_point_within_group(entity_point, group_min_x, group_min_y, 
                                    group_max_x, group_max_y, tolerance):
            continue

        layer_name = entity.dxf.layer.upper()
        
        # Handle drilling operations
        if entity.dxftype() == 'CIRCLE':
            drilling_pattern = DXF_LAYER_CONFIG['machining']['drilling']['layer_pattern']
            drilling_match = re.match(drilling_pattern.replace('{depth}', r'\d+'), layer_name, re.IGNORECASE)
            
            if drilling_match:
                print(f"DEBUG: Processing drilling in layer {layer_name}")
                rel_x, rel_y, calculated_face = convert_coords_to_panel_system(
                    entity.dxf.center.x, entity.dxf.center.y,
                    panel_type, panel_length, panel_width,
                    primary_bbox_panel, secondary_bbox_panel,
                    sheet_border_front_bbox, sheet_border_back_bbox,
                    tolerance
                )
                print(f"DEBUG: Drilling coordinates - Original: ({entity.dxf.center.x}, {entity.dxf.center.y}), Converted: ({rel_x}, {rel_y}), Calculated face: {calculated_face}")
                
                if rel_x is None or rel_y is None:
                    print("DEBUG: Invalid coordinates for drilling operation")
                    continue

                # Get drilling parameters from layer name
                layer_name = entity.dxf.layer.upper()
                drilling_config = DXF_LAYER_CONFIG['machining']['drilling']
                depth = _extract_depth_from_layer(layer_name, drilling_config['layer_pattern'])

                if depth is None:
                    print(f"DEBUG: Invalid drilling layer name: {layer_name}")
                    continue

                # Get parent border for the entity
                parent_border = None
                for border in borders_in_group:
                    border_vertices = list(border.vertices())
                    if not border_vertices:
                        continue
                    min_x = min(v[0] for v in border_vertices)
                    max_x = max(v[0] for v in border_vertices)
                    min_y = min(v[1] for v in border_vertices)
                    max_y = max(v[1] for v in border_vertices)
                    
                    # Check if point is inside this border
                    if (min_x - tolerance <= entity.dxf.center.x <= max_x + tolerance and
                        min_y - tolerance <= entity.dxf.center.y <= max_y + tolerance):
                        parent_border = border
                        break

                # Get face from structural_layers config
                force_face = None  # Don't force a face by default
                if parent_border:
                    parent_layer = parent_border.dxf.layer.upper()
                    if parent_layer in DXF_LAYER_CONFIG['structural_layers']:
                        layer_config = DXF_LAYER_CONFIG['structural_layers'][parent_layer]
                        if 'face' in layer_config:  # Only set force_face if configured
                            force_face = layer_config['face']
                            print(f"DEBUG: Setting force_face to {force_face} for entity in layer {parent_layer}")

                create_drilling_xml(machines_element, entity, panel_type, panel_length, 
                                 panel_width, primary_bbox_panel, secondary_bbox_panel,
                                 sheet_border_front_bbox, sheet_border_back_bbox, 
                                 tolerance, DXF_LAYER_CONFIG['machining']['drilling'],
                                 force_face=force_face)

        # Handle pocket operations
        elif entity.dxftype() == 'LWPOLYLINE' and layer_name == 'ABF_DSIDE_8':
            create_pocket_xml(machines_element, entity, panel_length, panel_width,
                            panel_type, primary_bbox_panel, secondary_bbox_panel,
                            sheet_border_front_bbox, sheet_border_back_bbox,
                            tolerance, DXF_LAYER_CONFIG['machining'])

        # Handle groove operations
        elif entity.dxftype() == 'LWPOLYLINE':
            groove_pattern = DXF_LAYER_CONFIG['machining']['groove']['layer_pattern']
            if re.match(groove_pattern.replace('{depth}', r'\d+'), layer_name, re.IGNORECASE):
                create_groove_xml(machines_element, entity, panel_length, panel_width,
                                panel_type, primary_bbox_panel, secondary_bbox_panel,
                                sheet_border_front_bbox, sheet_border_back_bbox,
                                tolerance, panel_thickness, DXF_LAYER_CONFIG['machining']['groove'])

def _get_entity_reference_point(entity):
    """Gets a reference point from an entity for containment checking."""
    try:
        if entity.dxftype() == 'CIRCLE':
            center = entity.dxf.center
            return [center.x, center.y]
        elif entity.dxftype() == 'LWPOLYLINE':
            vertices = list(entity.vertices())
            if vertices:
                return [vertices[0][0], vertices[0][1]]
        elif entity.dxftype() == 'LINE':
            start = entity.dxf.start
            return [start.x, start.y]
        elif entity.dxftype() in ['ARC', 'ELLIPSE']:
            center = entity.dxf.center
            return [center.x, center.y]
        elif entity.dxftype() == 'POINT':
            return [entity.dxf.location.x, entity.dxf.location.y]
    except Exception as e:
        print(f"DEBUG: Error getting reference point for {entity.dxftype()}: {e}")
    return None

def _is_point_within_group(point, min_x, min_y, max_x, max_y, tolerance):
    """Checks if a point is within the group bounding box with tolerance."""
    if point is None or len(point) < 2:
        return False
    result = (min_x - tolerance <= point[0] <= max_x + tolerance and
             min_y - tolerance <= point[1] <= max_y + tolerance)
    if not result:
        print(f"DEBUG: Point ({point[0]}, {point[1]}) outside bounds: X[{min_x - tolerance}, {max_x + tolerance}], Y[{min_y - tolerance}, {max_y + tolerance}]")
    return result
