#!/usr/bin/env python3
"""
CSV Natural Join Script
This script performs a natural join of two CSV files based on the ID column.
The output is a new CSV file containing the joined data.

Usage:
    python csv_join.py -f1 <file1.csv> -f2 <file2.csv> -o <output.csv> -m <max_points> [--anonymize]
"""
import traceback
import pandas as pd
import sys
import os
import argparse


def natural_join(file1, file2, output_file, max_points, anonymize=False):
    """
    Perform a natural join on two CSV files based on the 'ID' column.

    Args:
        file1 (str): Path to the first CSV file
        file2 (str): Path to the second CSV file
        output_file (str): Path to save the joined CSV file
        max_points (int): The maximum number of points to consider
        anonymize (bool): Whether to remove student name columns
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

        # Rename 'Student ID' to 'ID' if it exists in either dataframe
        if 'Student ID' in df1.columns and 'ID' not in df1.columns:
            df1.rename(columns={'Student ID': 'ID'}, inplace=True)
        if 'Student ID' in df2.columns and 'ID' not in df2.columns:
            df2.rename(columns={'Student ID': 'ID'}, inplace=True)

    except Exception as e:
        raise Exception(f"Error reading CSV files: {e}")

    # Check if 'ID' column exists in both DataFrames
    if 'ID' not in df1.columns:
        raise ValueError(f"'ID' column not found in {file1}")
    if 'ID' not in df2.columns:
        raise ValueError(f"'ID' column not found in {file2}")

    # Perform natural join (merge in pandas) on the ID column
    joined_df = pd.merge(df1, df2, on='ID', how='inner')

    # Rename columns
    if "Total Points" in joined_df.columns:
        joined_df.rename(columns={"Total Points": "Total Points Test"}, inplace=True)
    if "Total Score (%)" in joined_df.columns:
        joined_df.rename(columns={"Total Score (%)": "Total Score Test(%)"}, inplace=True)

    # Apply transformations after merging
    joined_df = joined_df[joined_df["Total Points Test"] != "NO KEY FOUND"]
    joined_df["Total Points Test"] = pd.to_numeric(joined_df["Total Points Test"], errors='coerce')

    # Calculate total points
    test_total_points = joined_df["Total Points Test"]
    open_ended_total_points = joined_df[[x for x, t in zip(joined_df.columns, joined_df.dtypes)
                                         if x.startswith("OEQ") and pd.api.types.is_numeric_dtype(t)]].sum(axis=1)
    total_points = test_total_points + open_ended_total_points

    # Insert calculated columns
    joined_df.insert(3, 'Overall Points', total_points)
    joined_df.insert(3, 'Overall Grade (%)', 100 * total_points / max_points)

    # Ensure ID and test form are the first two columns
    cols = joined_df.columns.tolist()
    cols_to_move = ['ID']
    if 'test form' in cols:  # Check if 'test form' exists
        cols_to_move.append('test form')

    # Remove columns to move from the list
    for col in cols_to_move:
        if col in cols:
            cols.remove(col)

    # Add them at the beginning
    joined_df = joined_df[cols_to_move + cols]

    # Find the index of the first Q1 question column
    q1_columns = [col for col in joined_df.columns if col.startswith('Q1')]
    if q1_columns:
        first_q1_column = q1_columns[0]
        first_q1_index = joined_df.columns.get_loc(first_q1_column)

        # Get columns before the first Q1 column (including it)
        keep_columns = list(joined_df.columns[:first_q1_index + 1])

        # Add all numeric columns that appear after the first Q1
        for col in joined_df.columns[first_q1_index + 1:]:
            if pd.api.types.is_numeric_dtype(joined_df[col].dtype):
                keep_columns.append(col)

        # Keep only the selected columns
        joined_df = joined_df[keep_columns]

    # Anonymize data if requested
    if anonymize:
        name_columns = ['Last Name', 'First Name', 'Middle Name', 'Family Name']
        for col in name_columns:
            if col in joined_df.columns:
                joined_df.drop(col, axis=1, inplace=True)

    # Save the joined DataFrame to a CSV file
    joined_df.to_csv(output_file, index=False)

    # Calculate and display statistics
    total_students = len(joined_df)
    passing_students = len(joined_df[joined_df['Overall Grade (%)'] > 50])
    passing_percentage = (passing_students / total_students * 100) if total_students > 0 else 0
    avg_grade = joined_df['Overall Grade (%)'].mean()
    avg_passing_grade = joined_df[joined_df['Overall Grade (%)'] > 50][
        'Overall Grade (%)'].mean() if passing_students > 0 else 0
    max_grade = joined_df['Overall Grade (%)'].max()
    min_grade = joined_df['Overall Grade (%)'].min()

    print(f"\nStatistics:")
    print(f"Total students: {total_students}")
    print(f"Passing students (>50%): {passing_students} ({passing_percentage:.2f}%)")
    print(f"Average grade: {avg_grade:.2f}%")
    print(f"Average grade of passing students: {avg_passing_grade:.2f}%")
    print(f"Maximum grade: {max_grade:.2f}%")
    print(f"Minimum grade: {min_grade:.2f}%")

    print(f"\nJoin completed successfully. Output saved to {output_file}")
    print(f"Joined {len(joined_df)} rows")

    return joined_df


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Perform a natural join of two CSV files based on the ID column.'
    )

    # Add arguments
    parser.add_argument('-f1', '--file1', required=True, help='Path to the first CSV file')
    parser.add_argument('-f2', '--file2', required=True, help='Path to the second CSV file')
    parser.add_argument('-o', '--output', required=True, help='Path to save the joined CSV file')
    parser.add_argument('-m', '--max-points', type=int, required=True, help='Maximum number of points to consider')
    parser.add_argument('--anonymize', action='store_true',
                        help='Remove student name columns (Last Name, First Name, Middle Name, Family Name)')

    # Parse arguments
    args = parser.parse_args()

    try:
        natural_join(args.file1, args.file2, args.output, args.max_points, args.anonymize)
        print(f"Joined to {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()