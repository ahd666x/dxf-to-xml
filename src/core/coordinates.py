"""Coordinate transformation functions for DXF to XML conversion."""

def convert_coords_to_panel_system(entity_x, entity_y, panel_type, panel_xml_length, panel_xml_width,
                                 primary_bbox_panel, secondary_bbox_panel, 
                                 sheet_border_front_bbox, sheet_border_back_bbox, tolerance=0.1):
    """
    Converts DXF coordinates to panel coordinate system.
    Returns (x, y, face) tuple where face is "5" for front or "6" for back.
    Returns (None, None, None) if conversion fails.
    """
    # Use a larger tolerance for checking if entity is within bounds
    check_tolerance = max(1.0, tolerance)
    
    # Function implementation goes here - will copy from original code
    # This is just a placeholder for now
    
    # For coordinates within front sheet
    if (sheet_border_front_bbox is not None and
        sheet_border_front_bbox[0] - tolerance <= entity_x <= sheet_border_front_bbox[2] + tolerance and
        sheet_border_front_bbox[1] - tolerance <= entity_y <= sheet_border_front_bbox[3] + tolerance):
        # Process front sheet coordinates
        face = "5"
        # Convert coordinates relative to panel bbox
        if secondary_bbox_panel:
            rel_x = entity_y - secondary_bbox_panel[1]  # Y in DXF -> X in XML
            rel_y = entity_x - secondary_bbox_panel[0]  # X in DXF -> Y in XML
        else:
            return None, None, None

    # For coordinates within back sheet
    elif (sheet_border_back_bbox is not None and
          sheet_border_back_bbox[0] - tolerance <= entity_x <= sheet_border_back_bbox[2] + tolerance and
          sheet_border_back_bbox[1] - tolerance <= entity_y <= sheet_border_back_bbox[3] + tolerance):
        # Process back sheet coordinates
        face = "6"
        # Convert coordinates relative to panel bbox
        if primary_bbox_panel:
            rel_x = entity_y - primary_bbox_panel[1]  # Y in DXF -> X in XML
            rel_y = entity_x - primary_bbox_panel[0]  # X in DXF -> Y in XML
            # Mirror Y coordinate for back face
            rel_y = panel_xml_width - rel_y
        else:
            return None, None, None
    else:
        # Entity is not within either sheet border
        return None, None, None

    # Check if converted coordinates are within panel bounds (with tolerance)
    is_within_bounds = (-check_tolerance <= rel_x <= panel_xml_length + check_tolerance and
                       -check_tolerance <= rel_y <= panel_xml_width + check_tolerance)

    if not is_within_bounds:
        return None, None, None

    return rel_x, rel_y, face
