#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify that stroke count data has been loaded correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from database_manager import get_db_manager

def main():
    # Initialize database manager (this will trigger table initialization)
    db_manager = get_db_manager()
    
    # Get stroke count for a few test characters
    test_chars = ['一', '二', '三', '甲', '子', '龙', '鳖']  # including some rare ones
    print("Testing stroke count for sample characters:")
    for char in test_chars:
        strokes = db_manager.get_stroke_count(char)
        print(f"  {char}: {strokes}")
    
    # Get total count
    # We need to query directly
    import sqlite3
    conn = sqlite3.connect(r'D:\PythonProject\KP-AI-FENGSHUI\data\fengshui.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stroke_count")
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"\nTotal rows in stroke_count table: {count}")
    
    # Expected count from our JSON
    expected = 102998
    if count == expected:
        print(f"✓ Count matches expected {expected}")
        return 0
    else:
        print(f"✗ Count mismatch: expected {expected}, got {count}")
        return 1

if __name__ == '__main__':
    sys.exit(main())