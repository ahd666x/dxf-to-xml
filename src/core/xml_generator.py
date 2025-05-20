"""XML generation functions for DXF to XML conversion."""
import xml.etree.ElementTree as ET
import xml.dom.minidom

def create_panel_xml_structure(panel_id, panel_name, length, width, thickness):
    """Creates the basic XML structure for a panel including Outline and empty Machines tag."""
    root = ET.Element("Root", Cad="BuiltInCad", version="2.0")
    project = ET.SubElement(root, "Project")
    panels_element = ET.SubElement(project, "Panels")
    panel_element = ET.SubElement(panels_element, "Panel",
                                IsProduce="true",
                                ID=panel_id,
                                Name=panel_name,
                                Length=f"{length:.0f}",
                                Width=f"{width:.0f}",
                                Thickness=f"{thickness:.0f}",
                                MachiningPoint="1")

    # Panel Outline
    outline = ET.SubElement(panel_element, "Outline")
    outline_points = [(length, width), (0, width), (0, 0), (length, 0), (length, width)]
    for x, y in outline_points:
        ET.SubElement(outline, "Point", X=f"{x:.0f}", Y=f"{y:.0f}")

    # Machines tag
    ET.SubElement(panel_element, "Machines")

    # EdgeGroup
    edge_group = ET.SubElement(panel_element, "EdgeGroup", X1="0", Y1="0")
    ET.SubElement(edge_group, "Edge", Face="2", Thickness="0", Pre_Milling="0", 
                 X="0", Y="0", CentralAngle="0")
    ET.SubElement(edge_group, "Edge", Face="1", Thickness="0", Pre_Milling="0", 
                 X=f"{length:.0f}", Y="0", CentralAngle="0")
    ET.SubElement(edge_group, "Edge", Face="4", Thickness="0", Pre_Milling="0", 
                 X=f"{length:.0f}", Y=f"{width:.0f}", CentralAngle="0")
    ET.SubElement(edge_group, "Edge", Face="3", Thickness="0", Pre_Milling="0", 
                 X="0", Y=f"{width:.0f}", CentralAngle="0")

    return root, panel_element

def save_xml_file(root, output_file):
    """Saves XML structure to file with pretty printing."""
    xml_string = ET.tostring(root, encoding='utf-8').decode('utf-8')
    dom = xml.dom.minidom.parseString(xml_string)
    pretty_xml_string = dom.toprettyxml(indent="  ", encoding='utf-8')
    
    with open(output_file, "wb") as f:
        f.write(pretty_xml_string)
