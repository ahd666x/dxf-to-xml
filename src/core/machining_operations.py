"""XML creation functions for different types of machining operations."""
import math
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional
from .coordinates import convert_coords_to_panel_system
from ..utils.config import DXF_LAYER_CONFIG
from ..utils.helpers import get_bbox

def _extract_depth_from_layer(layer_name: str, pattern: str) -> Optional[int]:
    """Extract depth value from layer name using the configured pattern."""
    try:
        # Convert pattern to regex by escaping special chars and replacing {depth} with capture group
        regex_pattern = (pattern.replace('.', r'\.')
                              .replace('*', r'\*')
                              .replace('{depth}', r'(\d+)'))
        match = re.match(regex_pattern, layer_name, re.IGNORECASE)
        if match:
            return int(match.group(1))
    except Exception as e:
        print(f"DEBUG: Error extracting depth from layer {layer_name}: {e}")
    return None

def _validate_depth(depth: int, config: Dict) -> bool:
    """Validate depth against configuration limits."""
    try:
        min_depth = config['validation']['min_depth']
        max_depth = config['validation']['max_depth']
        return min_depth <= depth <= max_depth
    except KeyError:
        return True  # If validation config is missing, assume valid

def create_drilling_xml(machines_element, entity, panel_type, panel_length, panel_width,
                       primary_bbox_panel, secondary_bbox_panel, sheet_border_front_bbox,
                       sheet_border_back_bbox, tolerance, config, force_face=None, mirror_x=False):
    """Creates XML for drilling operations (Type 2).
    
    Args:
        machines_element: XML element to add the drilling operation to
        entity: DXF entity representing the drilling
        panel_type: Type of panel (back_capable or front_only)
        panel_length: Panel length in mm
        panel_width: Panel width in mm
        primary_bbox_panel: Primary bounding box
        secondary_bbox_panel: Secondary bounding box (for back-capable panels)
        sheet_border_front_bbox: Front sheet border bounding box
        sheet_border_back_bbox: Back sheet border bounding box
        tolerance: Tolerance for coordinate matching
        config: Drilling configuration
        force_face: If provided, use this face number instead of calculated one
        mirror_x: If True, mirror the X coordinate for back-side operations
    """
    center = entity.dxf.center
    rel_x, rel_y, face = convert_coords_to_panel_system(
        center.x, center.y, panel_type, panel_length, panel_width,
        primary_bbox_panel, secondary_bbox_panel,
        sheet_border_front_bbox, sheet_border_back_bbox, tolerance
    )

    if rel_x is None or rel_y is None or face is None:
        print(f"DEBUG: Invalid coordinates for drilling operation")
        return

    layer_name = entity.dxf.layer.upper()
    drilling_config = DXF_LAYER_CONFIG['machining']['drilling']
    
    # Extract and validate depth
    depth = _extract_depth_from_layer(layer_name, drilling_config['layer_pattern'])
    if depth is None or not _validate_depth(depth, drilling_config):
        print(f"DEBUG: Invalid drilling depth in layer {layer_name}")
        return
    
    # Calculate diameter
    if drilling_config.get('diameter_equals_depth', False):
        diameter = float(depth)
    else:
        diameter = round(entity.dxf.radius * 2, 3)

    # Apply mirroring for back-side operations if requested
    final_x = panel_length - rel_x if mirror_x else rel_x
    final_face = force_face if force_face else face

    print(f"DEBUG: Processing drilling - Center: ({center.x:.3f}, {center.y:.3f}) -> "
          f"Panel coords: ({final_x:.3f}, {rel_y:.3f}), Face: {final_face}, "
          f"Depth: {depth}, Diameter: {diameter:.3f}"
          f"{' (mirrored)' if mirror_x else ''}")

    ET.SubElement(machines_element, "Machining",
                 Type=drilling_config['type'],
                 IsGenCode="2",
                 Face=final_face,
                 X=f"{final_x:.3f}",
                 Y=f"{rel_y:.3f}",
                 Diameter=f"{diameter:.3f}",
                 Depth=str(depth))


def create_pocket_xml(machines_element, entity, panel_length, panel_width, panel_type,
                     primary_bbox_panel, secondary_bbox_panel, sheet_border_front_bbox,
                     sheet_border_back_bbox, tolerance, config):
    """Creates XML for pocket operations (Type 1)."""
    vertices = list(entity.vertices())
    if len(vertices) < 4 or not entity.dxf.flags & 1:
        return

    # Calculate pocket dimensions and center
    rect_min_x, rect_min_y, rect_max_x, rect_max_y = get_bbox(vertices)
    center_x = (rect_min_x + rect_max_x) / 2.0
    center_y = (rect_min_y + rect_max_y) / 2.0
    rect_dx = rect_max_x - rect_min_x
    rect_dy = rect_max_y - rect_min_y
    pocket_depth = max(rect_dx, rect_dy)

    # Convert center to panel coordinates
    center_rel_x, center_rel_y, sheet_face = convert_coords_to_panel_system(
        center_x, center_y, panel_type, panel_length, panel_width,
        primary_bbox_panel, secondary_bbox_panel,
        sheet_border_front_bbox, sheet_border_back_bbox, tolerance
    )

    if None in (center_rel_x, center_rel_y, sheet_face):
        return

    # Determine face (1-4) based on proximity to edges
    edge_tolerance = 20.0
    is_close_to_min_y = math.isclose(center_rel_y, 0, abs_tol=edge_tolerance)
    is_close_to_max_y = math.isclose(center_rel_y, panel_width, abs_tol=edge_tolerance)
    is_close_to_min_x = math.isclose(center_rel_x, 0, abs_tol=edge_tolerance)
    is_close_to_max_x = math.isclose(center_rel_x, panel_length, abs_tol=edge_tolerance)

    # Assign face based on proximity
    if is_close_to_max_y:
        face = "1"  # Top edge
    elif is_close_to_min_y:
        face = "2"  # Bottom edge
    elif is_close_to_max_x:
        face = "3"  # Right edge
    elif is_close_to_min_x:
        face = "4"  # Left edge
    else:
        # Find nearest edge if not close to any
        distances = {
            "1": abs(panel_width - center_rel_y),   # Distance to top
            "2": abs(center_rel_y),                 # Distance to bottom
            "3": abs(panel_length - center_rel_x),  # Distance to right
            "4": abs(center_rel_x)                  # Distance to left
        }
        face = min(distances, key=distances.get)

    # Snap coordinates to the assigned edge
    if face == "1":
        center_rel_y = panel_width
    elif face == "2":
        center_rel_y = 0
    elif face == "3":
        center_rel_x = panel_length
    elif face == "4":
        center_rel_x = 0

    ET.SubElement(machines_element, "Machining",
                 Type="1",
                 IsGenCode="2",
                 Face=face,
                 X=f"{center_rel_x:.3f}",
                 Y=f"{center_rel_y:.3f}",
                 Z="8",
                 Diameter="8.000",
                 Depth=f"{pocket_depth:.3f}")


def create_groove_xml(machines_element, entity, panel_length, panel_width, panel_type,
                     primary_bbox_panel, secondary_bbox_panel, sheet_border_front_bbox,
                     sheet_border_back_bbox, tolerance, panel_thickness, config):
    """Creates XML for groove operations (Type 4)."""
    if entity.dxftype() != 'LWPOLYLINE' or not entity.dxf.flags & 1:
        print(f"DEBUG: Invalid groove entity - must be closed LWPOLYLINE")
        return

    vertices = list(entity.vertices())
    if len(vertices) < 4:
        print(f"DEBUG: Invalid groove - needs at least 4 vertices")
        return

    # Calculate groove width from rectangle geometry
    width = _calculate_groove_width(vertices)
    if width is None:
        print(f"DEBUG: Unable to determine groove width")
        return

    # Get groove center point
    center_x = sum(v[0] for v in vertices) / len(vertices)
    center_y = sum(v[1] for v in vertices) / len(vertices)

    # Convert to panel coordinates
    rel_x, rel_y, face = convert_coords_to_panel_system(
        center_x, center_y, panel_type, panel_length, panel_width,
        primary_bbox_panel, secondary_bbox_panel,
        sheet_border_front_bbox, sheet_border_back_bbox, tolerance
    )

    if rel_x is None or rel_y is None or face is None:
        print(f"DEBUG: Invalid coordinates for groove operation")
        return

    groove_config = DXF_LAYER_CONFIG['machining']['groove']
    
    # Extract and validate depth
    layer_name = entity.dxf.layer.upper()
    depth = _extract_depth_from_layer(layer_name, groove_config['layer_pattern'])
    if depth is None or not _validate_depth(depth, groove_config):
        print(f"DEBUG: Invalid groove depth in layer {layer_name}")
        return

    # Get start and end points of the groove
    rect_min_x, rect_min_y, rect_max_x, rect_max_y = get_bbox(vertices)
    is_horizontal = (rect_max_x - rect_min_x) > (rect_max_y - rect_min_y)
    
    # Get start and end points in panel coordinates
    if is_horizontal:
        start_x, start_y, _ = convert_coords_to_panel_system(
            rect_min_x, center_y, panel_type, panel_length, panel_width,
            primary_bbox_panel, secondary_bbox_panel,
            sheet_border_front_bbox, sheet_border_back_bbox, tolerance
        )
        end_x, end_y, _ = convert_coords_to_panel_system(
            rect_max_x, center_y, panel_type, panel_length, panel_width,
            primary_bbox_panel, secondary_bbox_panel,
            sheet_border_front_bbox, sheet_border_back_bbox, tolerance
        )
    else:
        start_x, start_y, _ = convert_coords_to_panel_system(
            center_x, rect_min_y, panel_type, panel_length, panel_width,
            primary_bbox_panel, secondary_bbox_panel,
            sheet_border_front_bbox, sheet_border_back_bbox, tolerance
        )
        end_x, end_y, _ = convert_coords_to_panel_system(
            center_x, rect_max_y, panel_type, panel_length, panel_width,
            primary_bbox_panel, secondary_bbox_panel,
            sheet_border_front_bbox, sheet_border_back_bbox, tolerance
        )

    print(f"DEBUG: Processing groove - Start: ({start_x:.3f}, {start_y:.3f}), "
          f"End: ({end_x:.3f}, {end_y:.3f}), Face: {face}, "
          f"Depth: {depth}, Width: {width:.3f}")

    ET.SubElement(machines_element, "Machining",
                 Type=groove_config['type'],
                 IsGenCode="2",
                 Face=face,
                 X=f"{start_x:.3f}",
                 Y=f"{start_y:.3f}",
                 Z=str(panel_thickness),
                 EndX=f"{end_x:.3f}",
                 EndY=f"{end_y:.3f}",
                 EndZ=str(panel_thickness),
                 Width=f"{width:.3f}",
                 Depth=str(depth),
                 ToolOffset=groove_config['tool_offset'])

def _calculate_groove_width(vertices: List[Tuple[float, float]]) -> Optional[float]:
    """Calculate the width of a groove from its vertices (shorter dimension)."""
    try:
        if len(vertices) < 4:
            print("DEBUG: Not enough vertices for groove width calculation")
            return None
            
        # Get bounding box
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        
        # Calculate dimensions
        width_x = max(xs) - min(xs)
        width_y = max(ys) - min(ys)
        
        if width_x <= 0 or width_y <= 0:
            print("DEBUG: Invalid groove dimensions")
            return None
            
        width = min(width_x, width_y)
        return round(width, 3)
    except Exception as e:
        print(f"DEBUG: Error calculating groove width: {e}")
        return None


"""Handle machining operations for DXF to XML conversion."""
import re
from typing import Dict, List, Tuple, Optional

class MachiningOperations:
    def __init__(self):
        self.config = DXF_LAYER_CONFIG['machining']
        self._drilling_pattern = self.config['drilling']['layer_pattern']
        self._drill_regex = re.compile(
            self._drilling_pattern.format(depth=r'(\d+)')
        )

    def identify_layer_type(self, layer_name: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Identify the type of machining operation from the layer name.
        Returns (operation_type, config) tuple.
        """
        # Check if it's a drilling layer
        drill_match = self._drill_regex.match(layer_name)
        if drill_match:
            depth = int(drill_match.group(1))
            if not self._validate_drilling_depth(depth):
                return None, None
            return 'drilling', self._get_drilling_config(depth)

        # Check other layer types
        for layer_name_pattern, config in self.config.items():
            if layer_name == layer_name_pattern:
                return layer_name_pattern, config

        return None, None

    def _validate_drilling_depth(self, depth: int) -> bool:
        """
        Validate that the drilling depth is within allowed range.
        """
        drill_config = self.config['drilling']
        min_depth = drill_config['validation']['min_depth']
        max_depth = drill_config['validation']['max_depth']
        return min_depth <= depth <= max_depth

    def _get_drilling_config(self, depth: int) -> Dict:
        """
        Get drilling configuration for the specified depth.
        """
        base_config = self.config['drilling'].copy()
        config = {
            'type': base_config['type'],
            'faces': base_config['faces'],
            'depth': depth,
        }
        
        if base_config.get('diameter_equals_depth', False):
            config['diameter'] = float(depth)
            
        return config

    def get_xml_type(self, operation_type: str, config: Dict) -> str:
        """Get the XML type code for the operation."""
        return config['type']

    def get_face(self, operation_type: str, config: Dict, position: Dict) -> str:
        """
        Determine the appropriate face number based on operation type and position.
        """
        if operation_type == 'drilling':
            # For drilling, determine front/back based on sheet position
            return (config['faces']['front'] 
                   if position.get('is_front', True) 
                   else config['faces']['back'])
        
        elif 'faces' in config:
            # For operations with position-dependent faces (like pockets)
            if position.get('near_left', False):
                return config['faces']['near_left']
            elif position.get('near_right', False):
                return config['faces']['near_right']
            elif position.get('near_top', False):
                return config['faces']['near_top']
            elif position.get('near_bottom', False):
                return config['faces']['near_bottom']
                
        # Default to the single face if specified
        return config.get('face', '5')  # Default to front face

    def get_operation_parameters(self, operation_type: str, config: Dict) -> Dict:
        """
        Get the parameters for the operation (depth, diameter, etc).
        """
        params = {}
        
        if 'depth' in config:
            params['depth'] = config['depth']
        if 'diameter' in config:
            params['diameter'] = config['diameter']
        if 'width' in config:
            params['width'] = config['width']
        if 'tool_offset' in config:
            params['tool_offset'] = config['tool_offset']
            
        return params

    def get_groove_parameters(self, groove_entity, panel_bounds) -> Dict:
        """
        Calculate groove parameters from the DXF entity and panel bounds.
        
        Args:
            groove_entity: The DXF entity representing the groove (rectangle)
            panel_bounds: The bounding box of the panel
            
        Returns:
            Dict containing:
            - width: The width of the groove (shorter dimension of rectangle)
            - depth: The depth extracted from layer name
            - position: Distance from groove center to panel edge
            - tool_offset: The tool offset direction
        """
        # Get the width from the rectangle geometry
        width = self._calculate_groove_width(groove_entity)
        
        # Validate groove width
        if not self._validate_groove_width(width):
            raise ValueError(f"Invalid groove width: {width}mm")
            
        # Calculate position from center of groove to panel edge
        position = self._calculate_groove_position(groove_entity, panel_bounds)
        
        # Get tool offset based on position relative to panel edges
        tool_offset = self._determine_tool_offset(position, panel_bounds)
        
        return {
            'width': width,
            'position': position,
            'tool_offset': tool_offset
        }

    def _calculate_groove_width(self, groove_entity) -> float:
        """Calculate the width of the groove from its geometry."""
        # Get the rectangle's vertices
        vertices = groove_entity.vertices
        
        # Calculate lengths of both dimensions
        dim1 = abs(vertices[1][0] - vertices[0][0])
        dim2 = abs(vertices[1][1] - vertices[0][1])
        
        # Width is the shorter dimension
        return min(dim1, dim2)

    def _validate_groove_width(self, width: float) -> bool:
        """Validate that the groove width is within allowed range."""
        groove_config = self.config['groove']
        min_width = groove_config['validation']['min_width']
        max_width = groove_config['validation']['max_width']
        return min_width <= width <= max_width

    def _calculate_groove_position(self, groove_entity, panel_bounds) -> float:
        """Calculate the distance from groove center to panel edge."""
        # Get groove center coordinates
        center_x = (groove_entity.vertices[0][0] + groove_entity.vertices[1][0]) / 2
        center_y = (groove_entity.vertices[0][1] + groove_entity.vertices[1][1]) / 2
        
        # Calculate distances to panel edges
        dist_left = abs(center_x - panel_bounds.min_x)
        dist_right = abs(panel_bounds.max_x - center_x)
        dist_top = abs(panel_bounds.max_y - center_y)
        dist_bottom = abs(center_y - panel_bounds.min_y)
        
        # Return the smallest distance (closest edge)
        return min(dist_left, dist_right, dist_top, dist_bottom)

    def _determine_tool_offset(self, position: float, panel_bounds) -> str:
        """Determine tool offset direction based on groove position."""
        # Default to center offset
        return '中'  # Center offset
