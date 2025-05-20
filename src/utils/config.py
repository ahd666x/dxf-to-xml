"""Configuration settings for the DXF to XML converter."""

# Layer configurations for DXF to XML mapping
DXF_LAYER_CONFIG = {
    # Structural layers for panel identification and their face assignments
    'structural_layers': {
        '_ABF_PART_BORDER': {
            'face': '6'    # All holes in part border are on back face
        },
        '_ABF_CUTTING_LINES': {
            'face': '5'    # All holes in cutting lines are on front face
        },
        '_ABF_SHEET_BORDER': {}  # Sheet border is just a boundary marker, no face assignment
    },
    
    'part_border': '_ABF_PART_BORDER',
    'cutting_lines': '_ABF_CUTTING_LINES',
    'sheet_border': '_ABF_SHEET_BORDER',

    # Machining operation layers and their XML mappings
    'machining': {
        # Dynamic drilling configuration
        'drilling': {
            'layer_pattern': 'ABF_D{depth}',  # Dynamic pattern where depth is provided by user
            'type': '2',                      # Type 2 in XML = drilling
            'faces': {
                'front': '5',                 # When in front sheet
                'back': '6'                   # When in back sheet
            },
            'diameter_equals_depth': True,    # Diameter matches the depth value
            'validation': {
                'min_depth': 1,              # Minimum allowed depth in mm
                'max_depth': 16              # Maximum allowed depth in mm
            }
        },
        
        # Pocket operations
        'ABF_DSIDE_8': {
            'type': '1',        # Type 1 in XML = pocket/routing
            'faces': {
                'near_left': '4',    # When pocket is near left edge
                'near_right': '3',   # When pocket is near right edge
                'near_top': '1',     # When pocket is near top edge
                'near_bottom': '2'   # When pocket is near bottom edge
            },
            'diameter': 8.0,
            'edge_tolerance': 20.0  # Distance to consider "near" edge in mm
        },
        
        # Groove operations with dynamic depth
        'groove': {
            'layer_pattern': 'ABF_GROOVE{depth}',  # Dynamic pattern where depth is provided by user
            'type': '4',        # Type 4 in XML = groove
            'faces': {
                'front': '5',   # When in front sheet
                'back': '6'     # When in back sheet
            },
            'tool_offset': '中', # Default tool offset
            'validation': {
                'min_depth': 1,  # Minimum allowed depth in mm
                'max_depth': 16,  # Maximum allowed depth in mm
                'min_width': 2,  # Minimum allowed width in mm
                'max_width': 20  # Maximum allowed width in mm
            }
        }
    }
}
