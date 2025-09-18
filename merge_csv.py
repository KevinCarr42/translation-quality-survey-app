#!/usr/bin/env python3
"""
Script to merge CSV files from a folder containing translation comparisons.
Each CSV has multiple rows per source text (one per translator).
This script combines them into one row per source text with separate columns for each translator.
"""

import csv
import sys
import os
import re
from collections import defaultdict, OrderedDict


def merge_csv_folder(folder_path, output_path):
    """
    Merge CSV files from a folder containing translation data.
    
    Args:
        folder_path: Path to folder containing CSV files
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
    
    # Find CSV files in folder matching the pattern
    csv_files = []
    pattern = re.compile(r'(.+?)_translation_comparison_(.+?)\.csv')
    
    for filename in os.listdir(folder_path):
        match = pattern.match(filename)
        if match:
            corpus_type = match.group(2)
            file_path = os.path.join(folder_path, filename)
            csv_files.append((file_path, corpus_type))
    
    if not csv_files:
        raise ValueError(f"No CSV files matching pattern found in {folder_path}")
    
    print(f"Found {len(csv_files)} CSV files:")
    for file_path, corpus_type in csv_files:
        print(f"  {os.path.basename(file_path)} -> corpus_type: {corpus_type}")
    
    # Process all files
    all_data = []
    for file_path, corpus_type in csv_files:
        print(f"Processing {os.path.basename(file_path)}...")
        file_data = process_csv_file(file_path, corpus_type)
        all_data.extend(file_data.values())
    
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
    corpus_counts = {}
    for data in all_data:
        corpus_type = data.get('corpus_type', 'unknown')
        corpus_counts[corpus_type] = corpus_counts.get(corpus_type, 0) + 1
    
    for corpus_type, count in corpus_counts.items():
        print(f"{corpus_type} rows: {count}")
    print(f"Translator columns: {translator_columns}")


if __name__ == "__main__":
    folder_path = "translation_results/"
    output = "dist/merged_translation_data.csv"
    
    try:
        merge_csv_folder(folder_path, output)
    except FileNotFoundError as e:
        print(f"Error: Could not find folder - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
