import ezdxf
import os

def    # Check each layer's entity count and properties
    for layer, expected_count in expected_counts.items():
        entities = [e for e in msp if e.dxf.layer == layer]
        count = len(entities)
        print(f"- {layer}: found {count} entities (expected {expected_count})")
        
        if count != expected_count:
            raise ValueError(f"Layer {layer}: expected {expected_count} entities, found {count}")
            
        # Validate entity types and dimensions
        if layer == '_ABF_SHEET_BORDER' or layer == '_ABF_PART_BORDER':
            if not all(e.dxftype() == 'LWPOLYLINE' for e in entities):
                raise ValueError(f"All entities in {layer} should be polylines")
                
            # Check dimensions if defined
            if layer in expected_geometries:
                for entity in entities:
                    points = list(entity.get_points())
                    width = max(p[0] for p in points) - min(p[0] for p in points)
                    height = max(p[1] for p in points) - min(p[1] for p in points)
                    expected = expected_geometries[layer]
                    
                    if abs(width - expected['width']) > 1 or abs(height - expected['height']) > 1:
                        raise ValueError(
                            f"{layer} dimensions mismatch: "
                            f"expected {expected['width']}x{expected['height']}, "
                            f"got {width}x{height}"
                        )
                        
        elif layer.startswith('ABF_D'):
            if not all(e.dxftype() == 'CIRCLE' for e in entities):
                raise ValueError(f"All entities in {layer} should be circles")
                
            # Extract diameter from layer name and validate
            try:
                expected_diameter = float(layer.replace('ABF_D', ''))
                for entity in entities:
                    if abs(entity.dxf.radius * 2 - expected_diameter) > 0.1:
                        raise ValueError(
                            f"Hole diameter mismatch in {layer}: "
                            f"expected {expected_diameter}, got {entity.dxf.radius * 2}"
                        )
            except ValueError:
                pass  # Skip diameter check if layer name doesn't contain valid diameterdrawing(doc):
    """Validate that all required entities were created."""
    msp = doc.modelspace()
    print("\nValidating drawing contents:")
    
    # Define expected counts and specifications
    expected_counts = {
        '_ABF_SHEET_BORDER': 1,        # Sheet border
        '_ABF_PART_BORDER': 1,         # Panel border
        '_ABF_CUTTING_LINES': 6,       # Edge cuts, T-slot, and cable groove
        'ABF_D10': 6,                  # Corner mounting holes + small cable holes
        'ABF_D5': 10,                  # Shelf support holes
        'ABF_D8': 20,                  # Hinge holes (12) + circular pattern (8)
        'ABF_D20': 2,                  # Medium cable holes
        'ABF_D6': 13,                  # Ventilation holes (diamond pattern)
        'ABF_D30': 2,                  # Large cable holes
    }
    
    # Define expected geometries
    expected_geometries = {
        '_ABF_SHEET_BORDER': {'width': 400, 'height': 1000},
        '_ABF_PART_BORDER': {'width': 300, 'height': 900},
    }
    
    # Check each layer
    for layer, expected_count in expected_counts.items():
        entities = [e for e in msp if e.dxf.layer == layer]
        count = len(entities)
        print(f"- {layer}: found {count} entities (expected {expected_count})")
        
        if count != expected_count:
            raise ValueError(f"Layer {layer}: expected {expected_count} entities, found {count}")
            
        # Validate entity types
        if layer.startswith('ABF_D'):
            if not all(e.dxftype() == 'CIRCLE' for e in entities):
                raise ValueError(f"All entities in {layer} should be circles")
        elif layer == '_ABF_SHEET_BORDER' or layer == '_ABF_PART_BORDER':
            if not all(e.dxftype() == 'LWPOLYLINE' for e in entities):
                raise ValueError(f"All entities in {layer} should be polylines")
    
    # Count all entities by layer and type
    print("\nDetailed entity breakdown:")
    layers = {}
    for e in msp:
        layer = e.dxf.layer
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(e.dxftype())
    
    for layer, entities in layers.items():
        print(f"- {layer}: {len(entities)} entities ({', '.join(set(entities))})")
    
    return True

def create_test_dxf():
    """Create a comprehensive test drawing with various patterns and hole types."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create sheet borders (right side is source, will be mirrored to left)
    right_sheet = msp.add_lwpolyline([
        (500, 0), (900, 0),     # Bottom edge
        (900, 0), (900, 1000),  # Right edge
        (900, 1000), (500, 1000),  # Top edge
        (500, 1000), (500, 0)   # Left edge
    ])
    right_sheet.dxf.layer = '_ABF_SHEET_BORDER'
    
    # Panel border in right sheet with detailed edge processing
    panel = msp.add_lwpolyline([
        # Main rectangle with notched corners
        (550, 50), (850, 50),    # Bottom edge
        (850, 50), (850, 950),   # Right edge
        (850, 950), (550, 950),  # Top edge
        (550, 950), (550, 50)    # Left edge
    ])
    panel.dxf.layer = '_ABF_PART_BORDER'
    
    # Add panel features for edge processing
    edge_cuts = [
        # Bottom edge notches for ventilation
        [(600, 50), (620, 50), (620, 70), (600, 70), (600, 50)],
        [(700, 50), (720, 50), (720, 70), (700, 70), (700, 50)],
        [(800, 50), (820, 50), (820, 70), (800, 70), (800, 50)],
        
        # Top edge cable management
        [(650, 950), (750, 950), (750, 930), (650, 930), (650, 950)]
    ]
    
    for points in edge_cuts:
        cut = msp.add_lwpolyline(points)
        cut.dxf.layer = '_ABF_CUTTING_LINES'
    
    # 1. Corner mounting holes (D10)
    corner_holes = [
        (600, 100),   # Top left
        (800, 100),   # Top right
        (600, 700),   # Bottom left
        (800, 700),   # Bottom right
    ]
    for pos in corner_holes:
        hole = msp.add_circle(pos, radius=5)
        hole.dxf.layer = 'ABF_D10'
    
    # 2. Shelf support holes (D5) - Two vertical rows
    shelf_holes_left = [(600, 200 + i*100) for i in range(5)]
    shelf_holes_right = [(800, 200 + i*100) for i in range(5)]
    for pos in shelf_holes_left + shelf_holes_right:
        hole = msp.add_circle(pos, radius=2.5)
        hole.dxf.layer = 'ABF_D5'
    
    # 3. Hinge mounting pattern (D8) - Three sets
    hinge_positions = [(700, 150), (700, 400), (700, 650)]
    for center_x, center_y in hinge_positions:
        # Create hinge hole pattern (2x2 grid)
        for dx, dy in [(-15,-15), (15,-15), (-15,15), (15,15)]:
            hole = msp.add_circle((center_x + dx, center_y + dy), radius=4)
            hole.dxf.layer = 'ABF_D8'
    
    # 4. Cable management holes with different sizes
    cable_holes = [
        # Large cable holes (D30)
        (700, 150, 15, 'ABF_D30'),
        (700, 850, 15, 'ABF_D30'),
        # Medium cable holes (D20)
        (700, 300, 10, 'ABF_D20'),
        (700, 700, 10, 'ABF_D20'),
        # Small cable holes (D10)
        (700, 450, 5, 'ABF_D10'),
        (700, 550, 5, 'ABF_D10')
    ]
    for x, y, radius, layer in cable_holes:
        hole = msp.add_circle((x, y), radius=radius)
        hole.dxf.layer = layer
    
    # 5. Ventilation hole patterns
    # Diamond pattern
    vent_center_x, vent_center_y = 700, 500
    for i in range(-2, 3):
        for j in range(-2, 3):
            if abs(i) + abs(j) <= 3:  # Diamond shape
                x = vent_center_x + i*30
                y = vent_center_y + j*30
                hole = msp.add_circle((x, y), radius=3)
                hole.dxf.layer = 'ABF_D6'
    
    # 6. Hardware mounting patterns
    # Circular pattern for special mount (D8)
    center_x, center_y = 650, 600
    radius = 30
    for angle in range(0, 360, 45):  # 8 holes in circle
        import math
        x = center_x + radius * math.cos(math.radians(angle))
        y = center_y + radius * math.sin(math.radians(angle))
        hole = msp.add_circle((x, y), radius=4)
        hole.dxf.layer = 'ABF_D8'
    
    # 7. Complex cutting patterns
    # T-shaped slot
    t_slot = msp.add_lwpolyline([
        (750, 200), (800, 200),      # Horizontal top
        (800, 200), (800, 250),      # Right vertical
        (800, 250), (780, 250),      # Bottom right
        (780, 250), (780, 220),      # Small vertical
        (780, 220), (770, 220),      # Bottom middle
        (770, 220), (770, 250),      # Small vertical
        (770, 250), (750, 250),      # Bottom left
        (750, 250), (750, 200)       # Left vertical
    ])
    t_slot.dxf.layer = '_ABF_CUTTING_LINES'
    
    # Cable management groove
    groove = msp.add_lwpolyline([
        (800, 350), (770, 350),      # Top horizontal
        (770, 350), (760, 360),      # Top diagonal
        (760, 360), (760, 390),      # Vertical
        (760, 390), (770, 400),      # Bottom diagonal
        (770, 400), (800, 400)       # Bottom horizontal
    ])
    groove.dxf.layer = '_ABF_CUTTING_LINES'
    
    # After mirroring, the program should create:
    # 1. Left sheet border as mirror of right sheet border
    # 2. Cutting lines in left side as mirror of part border
    # 3. Mirror all holes to the left side
    
    return doc

if __name__ == '__main__':
    import sys
    sys.stderr.write("Script started\n")
    sys.stderr.flush()
    try:
        import sys
        sys.stdout.write("Starting test DXF creation...\n")
        sys.stdout.flush()
        
        doc = create_test_dxf()
        sys.stdout.write("Drawing created in memory\n")
        sys.stdout.flush()
        
        # Validate the drawing before saving
        validate_drawing(doc)
        sys.stdout.write("Initial validation passed\n")
        sys.stdout.flush()
        
        output_path = os.path.join(os.path.dirname(__file__), 'test.dxf')
        doc.saveas(output_path)
        sys.stdout.write(f"Successfully saved DXF file to: {output_path}\n")
        sys.stdout.flush()
        
        # Extra validation - try to read the file back
        doc2 = ezdxf.readfile(output_path)
        validate_drawing(doc2)
        sys.stdout.write("Final validation successful - file contains all required entities\n")
        sys.stdout.flush()
        
    except Exception as e:
        import traceback
        sys.stderr.write(f"Error creating test DXF:\n{str(e)}\n")
        sys.stderr.write(traceback.format_exc())
        sys.stderr.flush()
        sys.exit(1)
