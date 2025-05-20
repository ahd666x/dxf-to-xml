import pytest
import ezdxf
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.panel_mirroring import (
    find_right_sheet_border,
    get_entities_within_border,
    mirror_entities,
    add_entities_to_doc
)

def create_test_drawing():
    """Create a test drawing with sheet borders, panels, and holes."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create sheet borders
    left_sheet = msp.add_lwpolyline([(0, 0), (400, 0), (400, 600), (0, 600), (0, 0)])
    left_sheet.dxf.layer = '_ABF_SHEET_BORDER'
    
    right_sheet = msp.add_lwpolyline([(500, 0), (900, 0), (900, 600), (500, 600), (500, 0)])
    right_sheet.dxf.layer = '_ABF_SHEET_BORDER'
    
    # Create a panel border in right sheet
    panel = msp.add_lwpolyline([(600, 200), (800, 200), (800, 400), (600, 400), (600, 200)])
    panel.dxf.layer = '_ABF_PART_BORDER'
    
    # Add some holes in the panel
    hole1 = msp.add_circle((650, 250), radius=5)
    hole1.dxf.layer = 'ABF_D10'
    
    hole2 = msp.add_circle((750, 350), radius=5)
    hole2.dxf.layer = 'ABF_D10'
    
    return doc

def test_find_right_sheet_border():
    doc = create_test_drawing()
    right_border = find_right_sheet_border(doc, '_ABF_SHEET_BORDER')
    points = list(right_border.get_points())
    max_x = max(p[0] for p in points)
    assert max_x == 900, "Right sheet border should be at x=900"

def test_get_entities_within_border():
    doc = create_test_drawing()
    right_border = find_right_sheet_border(doc, '_ABF_SHEET_BORDER')
    entities = get_entities_within_border(doc, right_border)
    assert len(entities) == 3, "Should find 3 entities (1 panel border + 2 holes)"
    
    entity_types = set(e.dxftype() for e in entities)
    assert 'LWPOLYLINE' in entity_types, "Should find panel border"
    assert 'CIRCLE' in entity_types, "Should find holes"

def test_mirror_entities():
    doc = create_test_drawing()
    right_border = find_right_sheet_border(doc, '_ABF_SHEET_BORDER')
    entities = get_entities_within_border(doc, right_border)
    
    points = list(right_border.get_points())
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    axis_x = (min_x + max_x) / 2
    
    mirrored = mirror_entities([right_border] + entities, (min_x, max_x), axis_x)
    assert len(mirrored) == 4, "Should mirror 4 entities (border + panel + 2 holes)"
    
    # Check if holes are mirrored correctly
    hole_layers = [e.dxf.layer for e in mirrored if e.dxftype() == 'CIRCLE']
    assert all(layer == 'ABF_D10' for layer in hole_layers), "Mirrored holes should keep their layer"

def test_add_entities_to_doc():
    doc = create_test_drawing()
    initial_count = len(list(doc.modelspace()))
    
    right_border = find_right_sheet_border(doc, '_ABF_SHEET_BORDER')
    entities = get_entities_within_border(doc, right_border)
    
    points = list(right_border.get_points())
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    axis_x = (min_x + max_x) / 2
    
    mirrored = mirror_entities([right_border] + entities, (min_x, max_x), axis_x)
    add_entities_to_doc(doc, mirrored)
    
    final_count = len(list(doc.modelspace()))
    assert final_count == initial_count + len(mirrored), "Should add all mirrored entities"

if __name__ == '__main__':
    pytest.main(['-v', __file__])
