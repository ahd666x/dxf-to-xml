#!/usr/bin/env python3
"""Main entry point for DXF to XML converter."""
import sys
import os
import importlib.util
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Dynamically import panel_mirroring
panel_mirroring_path = os.path.join(os.path.dirname(__file__), 'src', 'core', 'panel_mirroring.py')
spec = importlib.util.spec_from_file_location("panel_mirroring", panel_mirroring_path)
panel_mirroring = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel_mirroring)
find_right_sheet_border = panel_mirroring.find_right_sheet_border
get_entities_within_border = panel_mirroring.get_entities_within_border
mirror_entities = panel_mirroring.mirror_entities
add_entities_to_doc = panel_mirroring.add_entities_to_doc

from src.utils.config import DXF_LAYER_CONFIG
from src.ui.terminal import TerminalUI
from src.core.converter import dxf_to_custom_xml
import ezdxf
import tempfile
import shutil

def main():
    """Main entry point."""
    config = DXF_LAYER_CONFIG
    ui = TerminalUI(config)
    selected_file = ui.run()
    
    if selected_file:
        print("\nProcessing...")
        temp_dir = None
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp(prefix='dxf_processing_')
            
            # --- MIRRORING LOGIC ---
            doc = ezdxf.readfile(selected_file)
            sheet_border_layer = config['sheet_border']
            right_border = find_right_sheet_border(doc, sheet_border_layer)
            entities_in_right = get_entities_within_border(doc, right_border)
            
            # Get bounding box and axis for mirroring
            points = list(right_border.get_points())
            min_x = min(p[0] for p in points)
            max_x = max(p[0] for p in points)
            axis_x = (min_x + max_x) / 2
            mirrored_entities = mirror_entities([right_border] + entities_in_right, (min_x, max_x), axis_x)
            add_entities_to_doc(doc, mirrored_entities)
            
            # Save to a temp file in our temp directory
            temp_dxf_path = os.path.join(temp_dir, 'mirrored.dxf')
            doc.saveas(temp_dxf_path)
            
            # Process the mirrored DXF
            panel_thickness_value = 16.0
            dxf_to_custom_xml(temp_dxf_path, config, panel_thickness=panel_thickness_value)
            
        except Exception as e:
            print(f"\nError during processing: {str(e)}")
        finally:
            # Clean up all temporary files
            if temp_dir and os.path.exists(temp_dir):
                for root, dirs, files in os.walk(temp_dir, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(temp_dir)
            
        input("\nPress Enter to exit...")

if __name__ == '__main__':
    main()