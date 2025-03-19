#!/usr/bin/env python3
"""
CSV Natural Join Script

This script performs a natural join of two CSV files based on the ID column.
The output is a new CSV file containing the joined data.

Usage:
    python csv_join.py <file1.csv> <file2.csv> <output.csv>
"""

import pandas as pd
import sys
import os

def natural_join(file1, file2, output_file):
    """
    Perform a natural join on two CSV files based on the 'ID' column.
    
    Args:
        file1 (str): Path to the first CSV file
        file2 (str): Path to the second CSV file
        output_file (str): Path to save the joined CSV file
    """
    # Check if files exist
    if not os.path.exists(file1):
        raise FileNotFoundError(f"File not found: {file1}")
    if not os.path.exists(file2):
        raise FileNotFoundError(f"File not found: {file2}")
    
    # Read CSV files into pandas DataFrames
    try:
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
    except Exception as e:
        raise Exception(f"Error reading CSV files: {e}")
    
    # Check if 'ID' column exists in both DataFrames
    if 'ID' not in df1.columns:
        raise ValueError(f"'ID' column not found in {file1}")
    if 'ID' not in df2.columns:
        raise ValueError(f"'ID' column not found in {file2}")
    
    # Perform natural join (merge in pandas) on the ID column
    joined_df = pd.merge(df1, df2, on='ID', how='inner')
    
    # Save the joined DataFrame to a CSV file
    joined_df.to_csv(output_file, index=False)
    
    print(f"Join completed successfully. Output saved to {output_file}")
    print(f"Joined {len(joined_df)} rows")
    
    return joined_df

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) != 4:
        print("Usage: python csv_join.py <file1.csv> <file2.csv> <output.csv>")
        sys.exit(1)
    
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    output_file = sys.argv[3]
    
    try:
        natural_join(file1, file2, output_file)
        print(f"Joined to {output_file}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
