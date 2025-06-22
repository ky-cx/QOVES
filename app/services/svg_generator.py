import base64
from typing import Dict, List
from xml.etree.ElementTree import Element, SubElement, tostring
import numpy as np

class SVGGenerator:
    def __init__(self):
        # Define a color palette for different facial regions
        self.colors = {
            "1": "#FF6B6B",  # A reddish color
            "2": "#4ECDC4",  # A teal color
            "3": "#45B7D1",  # A blue color
            "4": "#96CEB4",  # A soft green
            "5": "#FECA57",  # A yellow/gold color
            "6": "#FFA07A",  # Light Salmon for other regions
        }
    
    def generate_svg(
        self, 
        image_shape: tuple,
        mask_contours: Dict[str, List[List[Dict[str, float]]]]
    ) -> str:
        """
        Generate an SVG string with contour overlays and encode it as base64.
        """
        height, width = image_shape[:2]
        
        # Create the root <svg> element
        svg = Element('svg')
        svg.set('width', str(width))
        svg.set('height', str(height))
        svg.set('xmlns', 'http://www.w3.org/2000/svg')
        svg.set('viewBox', f'0 0 {width} {height}')
        
        # Add each region's contours as a styled path
        for region_id, contour_list in mask_contours.items():
            # Get a color for the region, with a default for unlisted regions
            color = self.colors.get(region_id, "#CCCCCC") # Default to gray
            
            for contour in contour_list:
                if len(contour) < 3:
                    continue  # A path needs at least 3 points to be a shape
                
                # Create the <path> element
                path = SubElement(svg, 'path')
                
                # Build the path data string ("d" attribute)
                path_data = f"M {contour[0]['x']},{contour[0]['y']}"
                for point in contour[1:]:
                    path_data += f" L {point['x']},{point['y']}"
                path_data += " Z"  # Close the path
                
                # Set SVG attributes for styling as per requirements
                path.set('d', path_data)
                path.set('fill', 'none') # Transparent fill 
                path.set('stroke', color)
                path.set('stroke-width', '2')
                path.set('stroke-dasharray', '5,5') # Dashed outline 
                path.set('opacity', '0.9')
        
        # Convert the XML tree to a string and then encode it as base64
        svg_string = tostring(svg, encoding='unicode')
        svg_base64 = base64.b64encode(svg_string.encode('utf-8')).decode('utf-8')
        
        return svg_base64