#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix indentation in database_manager.py after editing stroke_count line.
"""

import sys

def main():
    file_path = r'D:\PythonProject\KP-AI-FENGSHUI\core\database_manager.py'
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the line numbers for the if block
    # We know the line "        if not json_loaded:" is at index?
    # Let's search for it.
    target_line = "        if not json_loaded:"
    start_idx = None
    for i, line in enumerate(lines):
        if line.rstrip('\n') == target_line:
            start_idx = i
            break
    
    if start_idx is None:
        print("Could not find target line")
        return 1
    
    # The if block should start at start_idx+1 and continue until the line before the next method or class?
    # Actually, the if block ends before the line that is at same indentation as the if (i.e., 8 spaces) and not empty?
    # We'll instead indent all lines from start_idx+1 until we encounter a line that has exactly 8 spaces and is not empty? 
    # Simpler: we know the built-in data block starts with a comment "# 常用字笔画数据..." and ends before the line "        for char, strokes in stroke_data:"
    # But we can just indent lines from start_idx+1 to the line before the line that starts with "        for char, strokes in stroke_data:" (which is at indent 8).
    
    # Let's find the line that starts with "        for char, strokes in stroke_data:"
    for_marker = "        for char, strokes in stroke_data:"
    end_idx = None
    for i in range(start_idx+1, len(lines)):
        if lines[i].rstrip('\n') == for_marker:
            end_idx = i
            break
    
    if end_idx is None:
        print("Could not find end marker")
        return 1
    
    # Indent lines from start_idx+1 to end_idx-1 by adding 4 spaces
    for i in range(start_idx+1, end_idx):
        if lines[i].strip() == '':  # empty line, keep empty but add spaces? We'll just add 4 spaces to preserve emptiness.
            lines[i] = '    ' + lines[i]
        else:
            lines[i] = '    ' + lines[i]
    
    # Also, we need to ensure the line after the if (the empty line) is properly indented.
    # Already handled.
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Indentation fixed.")
    return 0

if __name__ == '__main__':
    sys.exit(main())