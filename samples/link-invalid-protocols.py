#!/usr/bin/env python3
"""
Find all protocols that failed verification and link them to the invalid category
"""

import json
import os
from pathlib import Path

def create_symlink(source, link_dir, link_name):
    """Create a symbolic link, handling existing links."""
    link_path = Path(link_dir) / link_name
    
    # Calculate relative path from link location to source
    source_path = Path(source).absolute()
    link_dir_path = Path(link_dir).absolute()
    
    # Get relative path
    try:
        rel_path = os.path.relpath(source_path, link_dir_path)
    except ValueError:
        # If on different drives on Windows, use absolute path
        rel_path = str(source_path)
    
    # Remove existing link if it exists
    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    
    # Create new link
    link_path.symlink_to(rel_path)
    print(f"  Linked: {link_name}")

def main():
    os.chdir(Path(__file__).parent)
    
    # Load the verification results
    with open('by-property/verification-results.json', 'r') as f:
        results = json.load(f)
    
    print("Linking invalid protocols...\n")
    
    # Process all errors
    invalid_count = 0
    for error_result in results.get('errors', []):
        file_path = error_result['file']
        error_msg = error_result['error']
        
        # Check if file exists
        if Path(file_path).exists():
            file_name = Path(file_path).name
            print(f"{file_path}:")
            print(f"  Error: {error_msg}")
            
            # Create symlink in invalid directory
            create_symlink(f"../{file_path}", "by-property/invalid", file_name)
            invalid_count += 1
            print()
    
    # Also check for any .bspl files that aren't in any category
    print("\nChecking for uncategorized protocols...\n")
    
    # Get all .bspl files
    import glob
    all_bspl = set()
    for pattern in ['**/*.bspl']:
        for file in glob.glob(pattern, recursive=True):
            if 'by-property' not in file:
                all_bspl.add(file)
    
    # Get all categorized files
    categorized = set()
    for category in ['safe', 'unsafe', 'live', 'nonlive']:
        cat_dir = Path(f'by-property/{category}')
        if cat_dir.exists():
            for link in cat_dir.iterdir():
                if link.is_symlink():
                    # Get the original filename
                    target = link.resolve()
                    # Find relative path from samples directory
                    try:
                        rel_from_samples = target.relative_to(Path.cwd())
                        categorized.add(str(rel_from_samples))
                    except:
                        pass
    
    # Find uncategorized files
    uncategorized = all_bspl - categorized
    
    # These should be the invalid ones
    for file_path in sorted(uncategorized):
        if Path(file_path).exists():
            file_name = Path(file_path).name
            
            # Skip if already in invalid
            if (Path('by-property/invalid') / file_name).exists():
                continue
                
            print(f"{file_path}: Uncategorized (likely invalid)")
            create_symlink(f"../{file_path}", "by-property/invalid", file_name)
            invalid_count += 1
            print()
    
    print(f"\nTotal invalid protocols linked: {invalid_count}")
    
    # Show all category counts
    print("\nUpdated category counts:")
    for category in ['safe', 'unsafe', 'live', 'nonlive', 'invalid']:
        cat_path = Path(f"by-property/{category}")
        if cat_path.exists():
            count = len(list(cat_path.glob("*.bspl")))
            print(f"  {category}: {count} protocols")

if __name__ == "__main__":
    main()