import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
import os
import re
from typing import Dict, List, Tuple, Optional


class SVGFormPrefiller:
    """
    Class to prefill student information on Open-MCR forms using SVG format.
    """

    def __init__(self, svg_template_path: str):
        """
        Initialize with path to the blank SVG form template.

        Args:
            svg_template_path: Path to the blank form SVG
        """
        # Load the SVG template
        self.tree = ET.parse(svg_template_path)
        self.root = self.tree.getroot()

        # Define SVG namespace to use with find operations
        self.ns = {"svg": "http://www.w3.org/2000/svg"}

        # Define field information (from the grid_info.py file)
        self.fields = {
            'LAST_NAME': {'horizontal_start': 1, 'vertical_start': 3, 'num_fields': 12, 'type': 'LETTER'},
            'FIRST_NAME': {'horizontal_start': 14, 'vertical_start': 3, 'num_fields': 6, 'type': 'LETTER'},
            'MIDDLE_NAME': {'horizontal_start': 21, 'vertical_start': 3, 'num_fields': 2, 'type': 'LETTER'},
            'STUDENT_ID': {'horizontal_start': 25, 'vertical_start': 3, 'num_fields': 10, 'type': 'NUMBER'},
            'COURSE_ID': {'horizontal_start': 25, 'vertical_start': 16, 'num_fields': 10, 'type': 'NUMBER'},
            'TEST_FORM_CODE': {'horizontal_start': 27, 'vertical_start': 28, 'field_length': 6, 'type': 'LETTER'}
        }

        # Letter and number mappings
        self.letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.numbers = "0123456789"

        # Map field names to SVG element IDs (may need to be adjusted based on SVG structure)
        self.field_id_prefixes = {
            'LAST_NAME': 'last-name-',
            'FIRST_NAME': 'first-name-',
            'MIDDLE_NAME': 'middle-name-',
            'STUDENT_ID': 'student-id-',
            'COURSE_ID': 'course-id-',
            'TEST_FORM_CODE': 'test-form-code-'
        }

    def get_bubble_id(self, field: str, position: int, value: str) -> str:
        """
        Generate the ID for a specific bubble in the SVG.

        Args:
            field: Field name (LAST_NAME, FIRST_NAME, etc.)
            position: Position within the field (0 for first character, etc.)
            value: The letter or number value

        Returns:
            ID string for the bubble in the SVG
        """
        prefix = self.field_id_prefixes.get(field, field.lower().replace('_', '-') + '-')

        if self.fields[field]['type'] == 'LETTER':
            value_index = self.letters.index(value.upper())
        else:  # NUMBER
            value_index = int(value)

        # Format depends on your SVG's ID structure - adapt as needed
        # This is a common format: field-position-value (e.g., last-name-0-a for first position, letter A)
        return f"{prefix}{position}-{value_index}"

    def find_bubble_by_coordinates(self, field: str, position: int, value: str) -> Optional[ET.Element]:
        """
        Find a bubble element based on its coordinates in the grid.
        This is an alternative approach if IDs aren't available in the SVG.

        Args:
            field: Field name (LAST_NAME, FIRST_NAME, etc.)
            position: Position within the field (0 for first character, etc.)
            value: The letter or number value

        Returns:
            The SVG circle element, or None if not found
        """
        field_info = self.fields[field]

        # Calculate grid coordinates
        h_start = field_info['horizontal_start']
        v_start = field_info['vertical_start']

        h_pos = h_start + position

        if field_info['type'] == 'LETTER':
            v_pos = v_start + self.letters.index(value.upper())
        else:  # NUMBER
            v_pos = v_start + int(value)

        # Find the circle at these coordinates
        # Note: This requires analyzing the SVG structure to understand how to match positions
        # This is a placeholder implementation and will need to be adapted to your SVG
        for circle in self.root.findall(".//svg:circle", self.ns):
            # Extract x, y from transform or cx, cy attributes
            # This is highly dependent on your SVG structure
            cx = float(circle.get('cx', '0'))
            cy = float(circle.get('cy', '0'))

            # Check if this circle is at the right position
            # You'll need to determine the actual grid-to-SVG coordinate mapping
            # This is just a placeholder calculation
            grid_x = cx / 20  # Assuming 20px per grid unit
            grid_y = cy / 20  # Assuming 20px per grid unit

            if abs(grid_x - h_pos) < 0.5 and abs(grid_y - v_pos) < 0.5:
                return circle

        return None

    def fill_bubble(self, bubble_id: str) -> bool:
        """
        Fill in a bubble in the SVG by its ID.

        Args:
            bubble_id: ID of the bubble element in the SVG

        Returns:
            True if successful, False if element not found
        """
        # Try to find by ID first
        bubble = self.root.find(f".//svg:circle[@id='{bubble_id}']", self.ns)

        # If not found by ID, try other approaches like searching by class or position
        if bubble is None:
            # Look for elements that might contain the ID in class or other attributes
            for elem in self.root.findall(".//svg:circle", self.ns):
                if bubble_id in elem.get('class', '') or bubble_id in elem.get('data-id', ''):
                    bubble = elem
                    break

        if bubble is None:
            print(f"Warning: Could not find bubble with ID {bubble_id}")
            return False

        # Fill the bubble (modify fill attribute)
        bubble.set('fill', 'black')
        bubble.set('fill-opacity', '1')

        return True

    def fill_letter(self, field: str, position: int, letter: str) -> bool:
        """
        Fill in a letter bubble on the form.

        Args:
            field: Field name (LAST_NAME, FIRST_NAME, etc.)
            position: Position within the field (0 for first character, etc.)
            letter: The letter to fill in

        Returns:
            True if successful, False otherwise
        """
        letter = letter.upper()
        if letter not in self.letters:
            return False  # Skip if invalid letter

        # Try to find by ID
        bubble_id = self.get_bubble_id(field, position, letter)
        if self.fill_bubble(bubble_id):
            return True

        # Fallback to finding by coordinates
        bubble = self.find_bubble_by_coordinates(field, position, letter)
        if bubble is not None:
            bubble.set('fill', 'black')
            bubble.set('fill-opacity', '1')
            return True

        return False

    def fill_number(self, field: str, position: int, number: str) -> bool:
        """
        Fill in a number bubble on the form.

        Args:
            field: Field name (STUDENT_ID, COURSE_ID, etc.)
            position: Position within the field (0 for first digit, etc.)
            number: The digit to fill in

        Returns:
            True if successful, False otherwise
        """
        if number not in self.numbers:
            return False  # Skip if invalid number

        # Try to find by ID
        bubble_id = self.get_bubble_id(field, position, number)
        if self.fill_bubble(bubble_id):
            return True

        # Fallback to finding by coordinates
        bubble = self.find_bubble_by_coordinates(field, position, number)
        if bubble is not None:
            bubble.set('fill', 'black')
            bubble.set('fill-opacity', '1')
            return True

        return False

    def fill_student_info(self,
                          last_name: str = "",
                          first_name: str = "",
                          middle_name: str = "",
                          student_id: str = "",
                          course_id: str = "",
                          test_form_code: str = "") -> ET.ElementTree:
        """
        Fill in all student information on a copy of the form.

        Args:
            last_name: Student's last name
            first_name: Student's first name
            middle_name: Student's middle name
            student_id: Student ID number
            course_id: Course ID number
            test_form_code: Test form code

        Returns:
            Modified ElementTree with filled form
        """
        # Make a deep copy of the root element
        form_copy = ET.parse(ET.tostring(self.root))
        self.root = form_copy.getroot()

        # Add visible text labels (if your SVG has text elements for displaying the values)
        self.add_text_labels(last_name, first_name, middle_name, student_id, course_id, test_form_code)

        # Fill in last name
        last_name = last_name.upper()[:min(len(last_name), self.fields['LAST_NAME']['num_fields'])]
        for i, letter in enumerate(last_name):
            self.fill_letter('LAST_NAME', i, letter)

        # Fill in first name
        first_name = first_name.upper()[:min(len(first_name), self.fields['FIRST_NAME']['num_fields'])]
        for i, letter in enumerate(first_name):
            self.fill_letter('FIRST_NAME', i, letter)

        # Fill in middle name
        middle_name = middle_name.upper()[:min(len(middle_name), self.fields['MIDDLE_NAME']['num_fields'])]
        for i, letter in enumerate(middle_name):
            self.fill_letter('MIDDLE_NAME', i, letter)

        # Fill in student ID
        student_id = student_id[:min(len(student_id), self.fields['STUDENT_ID']['num_fields'])]
        for i, digit in enumerate(student_id):
            self.fill_number('STUDENT_ID', i, digit)

        # Fill in course ID
        course_id = course_id[:min(len(course_id), self.fields['COURSE_ID']['num_fields'])]
        for i, digit in enumerate(course_id):
            self.fill_number('COURSE_ID', i, digit)

        # Fill in test form code
        test_form_code = test_form_code.upper()[
                         :min(len(test_form_code), self.fields['TEST_FORM_CODE']['field_length'])]
        for i, letter in enumerate(test_form_code):
            self.fill_letter('TEST_FORM_CODE', i, letter)

        return form_copy

    def add_text_labels(self, last_name, first_name, middle_name, student_id, course_id, test_form_code):
        """
        Add visible text labels to the form for easier identification.
        Only relevant if your SVG has text elements for displaying the values.

        Args:
            last_name, first_name, etc.: Student information to display
        """
        # Map of field names to SVG text element IDs
        text_element_ids = {
            'LAST_NAME': 'text-last-name',
            'FIRST_NAME': 'text-first-name',
            'MIDDLE_NAME': 'text-middle-name',
            'STUDENT_ID': 'text-student-id',
            'COURSE_ID': 'text-course-id',
            'TEST_FORM_CODE': 'text-test-form-code'
        }

        # Map of student data to fields
        field_values = {
            'LAST_NAME': last_name,
            'FIRST_NAME': first_name,
            'MIDDLE_NAME': middle_name,
            'STUDENT_ID': student_id,
            'COURSE_ID': course_id,
            'TEST_FORM_CODE': test_form_code
        }

        # Update text elements if they exist
        for field, value in field_values.items():
            if not value:
                continue

            text_id = text_element_ids.get(field)
            if text_id:
                text_elem = self.root.find(f".//svg:text[@id='{text_id}']", self.ns)
                if text_elem is not None:
                    # Clear existing text content
                    for child in text_elem:
                        text_elem.remove(child)

                    # Add new text content
                    text_elem.text = value

    def save_svg(self, output_path: str):
        """
        Save the modified SVG to a file.

        Args:
            output_path: Path to save the SVG file
        """
        self.tree.write(output_path, encoding='utf-8', xml_declaration=True)

    def process_student_list(self, students_csv: str, output_dir: str, include_ids_in_filename: bool = True):
        """
        Process a CSV file of students and generate filled forms for each.

        Args:
            students_csv: Path to a CSV file with student information
            output_dir: Directory to save filled forms
            include_ids_in_filename: Whether to include student IDs in filenames
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Read student data
        students = pd.read_csv(students_csv)

        for i, student in students.iterrows():
            # Extract student info (handling potential missing columns)
            last_name = student.get('last_name', '')
            first_name = student.get('first_name', '')
            middle_name = student.get('middle_name', '')
            student_id = str(student.get('student_id', ''))
            course_id = str(student.get('course_id', ''))
            test_form_code = student.get('test_form_code', '')

            # Fill form
            filled_form = self.fill_student_info(
                last_name, first_name, middle_name,
                student_id, course_id, test_form_code
            )

            # Generate output filename
            if include_ids_in_filename and student_id:
                output_filename = f"{last_name}_{first_name}_{student_id}.svg"
            else:
                output_filename = f"{last_name}_{first_name}.svg"

            output_path = os.path.join(output_dir, output_filename)

            # Save filled form
            self.save_svg(output_path)
            print(f"Created form for {first_name} {last_name} ({i + 1}/{len(students)})")

    def convert_all_to_pdf(self, svg_dir: str, output_dir: str = None):
        """
        Convert all SVGs in a directory to PDFs.
        Requires cairosvg to be installed (pip install cairosvg).

        Args:
            svg_dir: Directory containing SVG files
            output_dir: Directory to save PDFs (defaults to svg_dir if None)
        """
        try:
            import cairosvg
        except ImportError:
            print("cairosvg is not installed. Please install it with: pip install cairosvg")
            return

        if output_dir is None:
            output_dir = svg_dir
        else:
            os.makedirs(output_dir, exist_ok=True)

        svg_files = list(Path(svg_dir).glob("*.svg"))
        for i, svg_file in enumerate(svg_files):
            pdf_path = os.path.join(output_dir, f"{svg_file.stem}.pdf")
            cairosvg.svg2pdf(url=str(svg_file), write_to=pdf_path)
            print(f"Converted {svg_file.name} to PDF ({i + 1}/{len(svg_files)})")


# Example usage
if __name__ == "__main__":
    # Create a form prefiller
    print(os.getcwd())
    prefiller = SVGFormPrefiller("../src/assets/multiple_choice_sheet_75q.svg")

    # Example for a single student
    filled_form = prefiller.fill_student_info(
        last_name="SMITH",
        first_name="JOHN",
        middle_name="A",
        student_id="1234567890",
        course_id="0987654321",
        test_form_code="ABC123"
    )
    prefiller.save_svg("filled_form_example.svg")

    # Process a whole class
    prefiller.process_student_list("students.csv", "filled_forms")

    # Optionally convert all SVGs to PDFs for printing
    prefiller.convert_all_to_pdf("filled_forms")