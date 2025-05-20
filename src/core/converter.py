"""Main DXF to XML converter module."""
import os
import ezdxf
from ..utils.helpers import get_bbox_dimensions_sorted
from .xml_generator import create_panel_xml_structure, save_xml_file
from .panel_processor import process_machining_entities_for_panel
from .panel_finder import find_and_group_panels

def dxf_to_custom_xml(input_file, config, panel_thickness=16.0):
    """
    Main function to read DXF file, identify and process panels and their
    machining entities, and generate corresponding XML files.
    Uses layer names from config.
    """
    try:
        # Create output directory based on DXF filename
        dxf_base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_dir = os.path.join(os.path.dirname(input_file), dxf_base_name)
        os.makedirs(output_dir, exist_ok=True)
        print(f"DEBUG: مسیر خروجی '{output_dir}' ایجاد شد.")

        # Load the DXF document
        doc = ezdxf.readfile(input_file)
        print(f"DEBUG: فایل DXF '{input_file}' با موفقیت بارگذاری شد.")

        # Find and group physical panels
        grouped_panels = find_and_group_panels(doc, config)

        if not grouped_panels:
            print(f"❌ خطا: هیچ پنل فیزیکی برای پردازش یافت نشد.")
            return

        # Get the base name of the input DXF file without extension
        dxf_base_name = os.path.splitext(os.path.basename(input_file))[0]

        # Process each grouped physical panel
        for i, panel_group_info in enumerate(grouped_panels):
            _process_panel(i, panel_group_info, dxf_base_name, panel_thickness, doc, config)

    except FileNotFoundError:
        print(f"❌ خطا: فایل ورودی '{input_file}' یافت نشد.")
    except ezdxf.DXFStructureError:
        print(f"❌ خطا: فایل '{input_file}' یک فایل DXF معتبر نیست یا خراب است.")
    except Exception as e:
        print(f"❌ خطا در پردازش فایل DXF: {str(e)}")
        import traceback
        traceback.print_exc()

def _process_panel(index, panel_group_info, dxf_base_name, panel_thickness, doc, config):
    """Process a single panel group and generate its XML file."""
    primary_border_entity = panel_group_info['primary_border']
    panel_xml_width, panel_xml_length = get_bbox_dimensions_sorted(
        list(primary_border_entity.vertices())
    )
    length = panel_xml_length
    width = panel_xml_width

    print(f"\nDEBUG: --- شروع پردازش پنل فیزیکی شماره {index+1} (نوع: {panel_group_info['type']}) ---")
    print(f"DEBUG:   ابعاد پنل در XML (Length x Width): {length:.3f} x {width:.3f}")

    # Create output directory and filename
    output_dir = os.path.join(os.getcwd(), dxf_base_name)
    os.makedirs(output_dir, exist_ok=True)
    output_file_name_base = f"{dxf_base_name}.{length:.0f}x{width:.0f}.{index+1}"
    output_file = os.path.join(output_dir, f"{output_file_name_base}.xml")

    # Create XML structure
    root, panel_element = create_panel_xml_structure(
        output_file_name_base,
        output_file_name_base,
        length,
        width,
        panel_thickness
    )

    # Process machining entities
    process_machining_entities_for_panel(
        doc,
        panel_element,
        panel_group_info,
        length,
        width,
        panel_thickness,
        config
    )

    # Save XML file
    save_xml_file(root, output_file)

    print(f"✅ فایل '{output_file}' با موفقیت برای پنل فیزیکی شماره {index+1} (نوع: {panel_group_info['type']}) ایجاد شد.")
    print(f"DEBUG: --- پایان پردازش پنل فیزیکی شماره {index+1} ---")
