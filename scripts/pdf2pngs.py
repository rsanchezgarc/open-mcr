#!/usr/bin/env python3
"""
PDF to PNG Converter

A command-line tool that extracts each page from a PDF file and saves it as a PNG image.
"""

import argparse
import os
from pathlib import Path
from pdf2image import convert_from_path


def convert_pdf_to_png(pdf_path, output_dir, dpi=300, prefix=None):
    """
    Convert a PDF file to individual PNG images (one per page).
    
    Args:
        pdf_path (str): Path to the PDF file.
        output_dir (str): Directory where PNG images will be saved.
        dpi (int): Resolution of the output images in DPI.
        prefix (str, optional): Prefix for the output filenames.
    
    Returns:
        list: Paths of created PNG files.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Get filename without extension to use as prefix if none provided
    if prefix is None:
        prefix = Path(pdf_path).stem
    
    # Convert PDF to images
    pages = convert_from_path(pdf_path, dpi=dpi)
    
    # Save each page as PNG
    output_files = []
    for i, page in enumerate(pages):
        output_file = os.path.join(output_dir, f"{prefix}_page_{i+1:03d}.png")
        page.save(output_file, "PNG")
        output_files.append(output_file)
        print(f"Saved: {output_file}")
    
    return output_files


def main():
    parser = argparse.ArgumentParser(description="Convert PDF files to PNG images (one per page)")
    parser.add_argument("pdf_path", help="Path to the PDF file to convert")
    parser.add_argument("-o", "--output-dir", default="output", help="Directory to save the PNG files (default: 'output')")
    parser.add_argument("-d", "--dpi", type=int, default=300, help="Resolution of output images in DPI (default: 300)")
    parser.add_argument("-p", "--prefix", help="Prefix for output filenames (default: PDF filename)")
    
    args = parser.parse_args()
    
    try:
        output_files = convert_pdf_to_png(
            args.pdf_path,
            args.output_dir,
            args.dpi,
            args.prefix
        )
        print(f"\nConversion complete! Converted {len(output_files)} pages to PNG.")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
