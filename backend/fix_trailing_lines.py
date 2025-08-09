#!/usr/bin/env python3
"""
Script to remove trailing blank lines from Python files.
"""

import os

files_to_fix = [
    "app/auth/dependencies.py",
    "app/database/init_db.py", 
    "app/database/seed.py",
    "app/routers/auth.py",
    "app/routers/notes.py",
    "app/schemas/schemas.py",
    "main.py"
]

def remove_trailing_blank_lines(filename):
    """Remove trailing blank lines from a file."""
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        # Remove trailing blank lines
        while lines and lines[-1].strip() == '':
            lines.pop()
        
        # Ensure file ends with exactly one newline
        if lines and not lines[-1].endswith('\n'):
            lines[-1] += '\n'
        
        with open(filename, 'w') as f:
            f.writelines(lines)
        
        print(f"Fixed trailing blank lines in {filename}")
        return True
    except Exception as e:
        print(f"Error fixing {filename}: {e}")
        return False

def main():
    """Main function to fix all files."""
    print("Fixing trailing blank lines in Python files...")
    
    success_count = 0
    for filename in files_to_fix:
        if os.path.exists(filename):
            if remove_trailing_blank_lines(filename):
                success_count += 1
        else:
            print(f"File not found: {filename}")
    
    print(f"Successfully fixed {success_count}/{len(files_to_fix)} files")

if __name__ == "__main__":
    main()
