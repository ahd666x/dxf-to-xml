"""Functions for finding and grouping panels in DXF files."""
from ..utils.helpers import get_bbox, get_bbox_dimensions_sorted

def find_and_group_panels(doc, config):
    """Finds and groups panels based on sheet borders and part borders.
    Returns a list of panel groups, each containing information about 
    borders and bounding boxes.
    """
    # Find all sheet borders
    sheet_borders = [e for e in doc.modelspace() 
                    if e.dxftype() == 'LWPOLYLINE' and 
                    e.dxf.layer.upper() == config['sheet_border'].upper()]
    
    if len(sheet_borders) < 1:
        print("❌ خطا: هیچ مرز ورقی (_ABF_SHEET_BORDER) یافت نشد.")
        return []
    elif len(sheet_borders) > 2:
        print("⚠️ هشدار: بیش از دو مرز ورق یافت شد. فقط دو مورد اول استفاده می‌شود.")
        sheet_borders = sheet_borders[:2]

    # Get bounding boxes for sheet borders
    sheet_bboxes = []
    for border in sheet_borders:
        vertices = list(border.vertices())
        if vertices:
            min_x, min_y, max_x, max_y = get_bbox(vertices)
            sheet_bboxes.append((min_x, min_y, max_x, max_y))
            print(f"DEBUG: مرز ورق شناسایی شد (محدوده: {(min_x, min_y, max_x, max_y)})")

    if len(sheet_bboxes) < 2:
        front_bbox = sheet_bboxes[0] if sheet_bboxes else None
        back_bbox = None
    else:
        # Assume the leftmost sheet is front, rightmost is back
        if sheet_bboxes[0][0] < sheet_bboxes[1][0]:
            front_bbox, back_bbox = sheet_bboxes[0], sheet_bboxes[1]
        else:
            front_bbox, back_bbox = sheet_bboxes[1], sheet_bboxes[0]

    # Find all part borders and cutting lines
    part_borders = [e for e in doc.modelspace() 
                   if e.dxftype() == 'LWPOLYLINE' and 
                   e.dxf.layer.upper() == config['part_border'].upper()]
    
    cutting_lines = [e for e in doc.modelspace() 
                    if e.dxftype() == 'LWPOLYLINE' and 
                    e.dxf.layer.upper() == config['cutting_lines'].upper()]

    # Group panels
    panel_groups = []
    
    # First, handle back-capable panels (those with part borders)
    for part_border in part_borders:
        part_vertices = list(part_border.vertices())
        if not part_vertices:
            continue

        # Find matching cutting line by dimensions
        part_min_dim, part_max_dim = get_bbox_dimensions_sorted(part_vertices)
        matching_cutting_line = None
        
        for cutting_line in cutting_lines:
            cut_vertices = list(cutting_line.vertices())
            if not cut_vertices:
                continue
            
            cut_min_dim, cut_max_dim = get_bbox_dimensions_sorted(cut_vertices)
            if (abs(cut_min_dim - part_min_dim) <= 1.0 and 
                abs(cut_max_dim - part_max_dim) <= 1.0):
                matching_cutting_line = cutting_line
                print(f"DEBUG:   تطابق ابعاد پیدا شد برای مرز {config['part_border']} "
                      f"(ابعاد {part_min_dim:.1f} x {part_max_dim:.1f}) با مرز "
                      f"{config['cutting_lines']} "
                      f"(ابعاد {cut_min_dim:.1f} x {cut_max_dim:.1f}).")
                break

        if matching_cutting_line:
            part_bbox = get_bbox(part_vertices)
            cut_bbox = get_bbox(list(matching_cutting_line.vertices()))
            panel_groups.append({
                'type': 'back_capable',
                'primary_border': part_border,
                'secondary_border': matching_cutting_line,
                'borders': [part_border, matching_cutting_line],
                'primary_bbox': part_bbox,
                'secondary_bbox': cut_bbox,
                'sheet_border_front_bbox': front_bbox,
                'sheet_border_back_bbox': back_bbox
            })
            cutting_lines.remove(matching_cutting_line)
            print(f"DEBUG: پنل back_capable گروه بندی شد (مرز {config['part_border']} "
                  f"در مختصات (np.float64({(part_bbox[0] + part_bbox[2])/2:.13f}), "
                  f"np.float64({(part_bbox[1] + part_bbox[3])/2:.13f}))) با مرز "
                  f"{config['cutting_lines']} در مختصات "
                  f"(np.float64({(cut_bbox[0] + cut_bbox[2])/2:.13f}), "
                  f"np.float64({(cut_bbox[1] + cut_bbox[3])/2:.13f}))) "
                  f"بر اساس تطابق ابعاد.")

    # Handle remaining cutting lines as front-only panels
    for cutting_line in cutting_lines:
        cut_vertices = list(cutting_line.vertices())
        if not cut_vertices:
            continue
        
        cut_bbox = get_bbox(cut_vertices)
        panel_groups.append({
            'type': 'front_only',
            'primary_border': cutting_line,
            'secondary_border': None,
            'borders': [cutting_line],
            'primary_bbox': cut_bbox,
            'secondary_bbox': None,
            'sheet_border_front_bbox': front_bbox,
            'sheet_border_back_bbox': back_bbox
        })
        print(f"DEBUG: مرز {config['cutting_lines']} (مرکز "
              f"({(cut_bbox[0] + cut_bbox[2])/2:.1f}, "
              f"{(cut_bbox[1] + cut_bbox[3])/2:.1f}))) "
              f"به عنوان پنل فیزیکی تنها front_only اضافه شد.")

    print(f"\nDEBUG: تعداد کل پنل‌های فیزیکی شناسایی شده پس از گروه بندی: {len(panel_groups)}\n")
    return panel_groups
