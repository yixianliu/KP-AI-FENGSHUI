#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compute checksum for stroke_count table data to update EXPECTED_SEED_CHECKSUMS.
"""

import json
import hashlib
import os
from collections import OrderedDict

def compute_checksum_from_json(json_file_path):
    """Compute row count and MD5 checksum for stroke_count data as would be stored in DB.
    
    The table schema: char TEXT PRIMARY KEY, strokes INTEGER NOT NULL, source TEXT DEFAULT 'kangxi'
    For data loaded from unihan JSON, source = 'unihan'.
    
    Returns:
        tuple: (row_count, md5_hex_16)
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Build list of rows as dicts, sorted by char for determinism
    rows = []
    for item in data['characters']:
        char = item['char']
        strokes = item['strokes']
        # Source is 'unihan' for all entries from this JSON
        rows.append({'char': char, 'strokes': strokes, 'source': 'unihan'})
    
    # Sort by char to ensure deterministic order
    rows.sort(key=lambda x: x['char'])
    
    row_count = len(rows)
    if row_count == 0:
        return (0, '0' * 16)
    
    # Serialize to deterministic JSON
    json_str = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    md5_full = hashlib.md5(json_str.encode('utf-8')).hexdigest()
    return (row_count, md5_full[:16])

def main():
    json_file = os.path.join(os.path.dirname(__file__), 'data', 'unihan_stroke_counts.json')
    if not os.path.exists(json_file):
        print(f"Error: JSON file not found at {json_file}")
        return 1
    
    row_count, md5 = compute_checksum_from_json(json_file)
    print(f"Stroke count checksum: rows={row_count}, md5={md5}")
    print(f"Update EXPECTED_SEED_CHECKSUMS['stroke_count'] = ({row_count}, '{md5}')")
    
    # Also show the full line for easy replacement
    print(f"    'stroke_count': ({row_count}, '{md5}'),")
    
    return 0

if __name__ == '__main__':
    import sys
    exit(main())