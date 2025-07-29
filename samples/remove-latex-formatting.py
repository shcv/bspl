#!/usr/bin/env python3
"""
Remove LaTeX formatting from BSPL files
"""

import re
from pathlib import Path
import os

def remove_latex_from_file(filepath):
    """Remove LaTeX formatting from a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Common LaTeX patterns to remove
        replacements = [
            (r'\$\\msf\{roles\}\$', 'roles'),
            (r'\$\\msf\{parameters\}\$', 'parameters'),
            (r'\$\\msf\{private\}\$', 'private'),
            (r'\$\\mapsto\$', '→'),
            (r'\$\\msf\{([^}]+)\}\$', r'\1'),  # Generic \msf{...}
            (r'\$([^$]+)\$', r'\1'),  # Any remaining $...$
            (r'\\msf\{([^}]+)\}', r'\1'),  # \msf{...} without $
            (r'\\mapsto', '→'),  # \mapsto without $
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Check if we made any changes
        if content != original_content:
            # Write back the cleaned content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    # Change to samples directory
    samples_dir = Path(__file__).parent
    os.chdir(samples_dir)
    
    # Find all .bspl files
    bspl_files = list(Path('.').glob('**/*.bspl'))
    
    print(f"Checking {len(bspl_files)} BSPL files for LaTeX formatting...\n")
    
    modified_count = 0
    modified_files = []
    
    for filepath in sorted(bspl_files):
        # Skip by-property directory (contains only symlinks)
        if 'by-property' in str(filepath):
            continue
            
        # Check and clean the file
        if remove_latex_from_file(filepath):
            modified_count += 1
            modified_files.append(str(filepath))
            print(f"✓ Cleaned: {filepath}")
    
    print(f"\n=== Summary ===")
    print(f"Total files checked: {len([f for f in bspl_files if 'by-property' not in str(f)])}")
    print(f"Files modified: {modified_count}")
    
    if modified_files:
        print("\nModified files:")
        for f in modified_files:
            print(f"  - {f}")

if __name__ == "__main__":
    main()