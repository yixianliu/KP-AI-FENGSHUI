#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update stroke count data from Unihan_IRGSources.txt to JSON file for MeiHua stroke divination.
"""

import json
import os

def parse_unihan_strokes(unihan_file_path):
    """Parse Unihan_IRGSources.txt for kTotalStrokes entries.
    
    Returns:
        list of dicts: [{'char': character, 'strokes': int}, ...]
    """
    stroke_data = []
    with open(unihan_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) < 3:
                continue
            code_point_str, prop, value = parts[0], parts[1], parts[2]
            if prop == 'kTotalStrokes':
                # Convert code point like U+3400 to integer
                try:
                    code_point = int(code_point_str[2:], 16)
                    char = chr(code_point)
                    strokes = int(value)
                    stroke_data.append({'char': char, 'strokes': strokes})
                except (ValueError, OverflowError) as e:
                    # Skip invalid entries
                    pass
    return stroke_data

def main():
    # Paths
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    unihan_file = os.path.join(temp_dir, 'Unihan_IRGSources.txt')
    output_json = os.path.join(os.path.dirname(__file__), 'data', 'unihan_stroke_counts.json')
    
    if not os.path.exists(unihan_file):
        print(f"Error: Unihan file not found at {unihan_file}")
        print("Please download Unihan.zip from https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip")
        print("and extract Unihan_IRGSources.txt to the temp directory.")
        return 1
    
    print("Parsing Unihan_IRGSources.txt for kTotalStrokes...")
    stroke_data = parse_unihan_strokes(unihan_file)
    print(f"Found {len(stroke_data)} characters with stroke count data.")
    
    # Build JSON structure
    result = {
        "description": "Expanded stroke count data for MeiHua stroke divination from Unihan database",
        "version": "1.0",
        "characters": stroke_data
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    
    # Write JSON file
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully wrote stroke count data to {output_json}")
    
    # Also update the EXPECTED_SEED_CHECKSUMS in database_manager.py? We'll do that separately.
    return 0

if __name__ == '__main__':
    exit(main())