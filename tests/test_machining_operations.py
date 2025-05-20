"""Test suite for machining operations."""
import unittest
import xml.etree.ElementTree as ET
from src.core.machining_operations import (
    _extract_depth_from_layer,
    _validate_depth,
    _calculate_groove_width
)

class TestMachiningOperations(unittest.TestCase):
    def setUp(self):
        self.test_config = {
            'validation': {
                'min_depth': 1,
                'max_depth': 16
            }
        }

    def test_extract_depth_from_layer(self):
        """Test depth extraction from layer names."""
        test_cases = [
            ('ABF_D10', 'ABF_D{depth}', 10),
            ('ABF_GROOVE8', 'ABF_GROOVE{depth}', 8),
            ('ABF_D16', 'ABF_D{depth}', 16),
            ('INVALID_LAYER', 'ABF_D{depth}', None),
            ('ABF_D', 'ABF_D{depth}', None),
            ('ABF_DABC', 'ABF_D{depth}', None),
        ]
        
        for layer_name, pattern, expected in test_cases:
            with self.subTest(layer_name=layer_name):
                result = _extract_depth_from_layer(layer_name, pattern)
                self.assertEqual(result, expected)

    def test_validate_depth(self):
        """Test depth validation against config limits."""
        test_cases = [
            (1, True),   # Min depth
            (16, True),  # Max depth
            (8, True),   # Middle value
            (0, False),  # Below min
            (17, False), # Above max
        ]
        
        for depth, expected in test_cases:
            with self.subTest(depth=depth):
                result = _validate_depth(depth, self.test_config)
                self.assertEqual(result, expected)

    def test_calculate_groove_width(self):
        """Test groove width calculation from vertices."""
        test_cases = [
            # Rectangle 10x20
            ([(0,0), (10,0), (10,20), (0,20)], 10),
            # Rectangle 20x10
            ([(0,0), (20,0), (20,10), (0,10)], 10),
            # Square 10x10
            ([(0,0), (10,0), (10,10), (0,10)], 10),
            # Invalid vertices
            ([(0,0), (10,0)], None),  # Too few vertices
            ([], None),                # Empty list
        ]
        
        for vertices, expected in test_cases:
            with self.subTest(vertices=vertices):
                result = _calculate_groove_width(vertices)
                self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
