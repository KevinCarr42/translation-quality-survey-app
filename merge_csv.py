#!/usr/bin/env python3
"""
Script to merge two CSV files containing translation comparisons.
Each CSV has multiple rows per source text (one per translator).
This script combines them into one row per source text with separate columns for each translator.
"""

import csv
import sys
from collections import defaultdict, OrderedDict


def merge_csv_files(file1_path, file2_path, output_path):
    """
    Merge two CSV files containing translation data.
    
    Args:
        file1_path: Path to first CSV file (test_data)
        file2_path: Path to second CSV file (eval_data)
        output_path: Path for output merged CSV file
    """
    
    def process_csv_file(file_path, corpus_type):
        """Process a single CSV file and group by source text."""
        grouped_data = OrderedDict()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            current_source = None
            current_group = {}
            
            for row in reader:
                source = row['source']
                
                # If we hit a new source, save the previous group
                if current_source is not None and source != current_source:
                    if current_group:
                        current_group['corpus_type'] = corpus_type
                        grouped_data[current_source] = current_group
                    current_group = {}
                
                # Initialize group for new source
                if source != current_source:
                    current_source = source
                    current_group = {
                        'source': source,
                        'translation_bureau': row['target'],
                        'source_lang': row['source_lang'],
                        'other_lang': row['other_lang']
                    }
                
                # Add translator data
                translator_name = row['translator_name']
                current_group[translator_name] = row['translated_text']
            
            # Don't forget the last group
            if current_group:
                current_group['corpus_type'] = corpus_type
                grouped_data[current_source] = current_group
        
        return grouped_data
    
    # Process both files
    print(f"Processing {file1_path}...")
    test_data = process_csv_file(file1_path, 'test_data')
    
    print(f"Processing {file2_path}...")
    eval_data = process_csv_file(file2_path, 'eval_data')
    
    # Combine all data
    all_data = []
    all_data.extend(test_data.values())
    all_data.extend(eval_data.values())
    
    # Get all unique translator names to create consistent column headers
    all_translators = set()
    for data in all_data:
        for key in data.keys():
            if key not in ['source', 'translation_bureau', 'source_lang', 'other_lang', 'corpus_type']:
                all_translators.add(key)
    
    translator_columns = sorted(list(all_translators))
    
    # Define column order
    columns = ['source', 'source_lang', 'translation_bureau'] + translator_columns + ['corpus_type']
    
    # Write merged CSV
    print(f"Writing merged data to {output_path}...")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        
        for data in all_data:
            # Ensure all columns exist in the row
            row = {}
            for col in columns:
                row[col] = data.get(col, '')
            writer.writerow(row)
    
    print(f"Merge complete! Output contains {len(all_data)} rows.")
    print(f"Test data rows: {len(test_data)}")
    print(f"Eval data rows: {len(eval_data)}")
    print(f"Translator columns: {translator_columns}")


if __name__ == "__main__":
    # File paths
    file1 = "translation_comparison_20250819-0834.csv"  # test_data
    file2 = "translation_comparison_20250819-0923.csv"  # eval_data
    output = "merged_translation_data.csv"
    
    try:
        merge_csv_files(file1, file2, output)
    except FileNotFoundError as e:
        print(f"Error: Could not find file - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
