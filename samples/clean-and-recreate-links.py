#!/usr/bin/env python3
"""
Clean up and recreate all symlinks properly
"""

import os
import json
from pathlib import Path
import shutil

def clean_directory(dir_path):
    """Remove all symlinks in a directory"""
    dir_path = Path(dir_path)
    if dir_path.exists():
        for item in dir_path.iterdir():
            if item.is_symlink():
                item.unlink()
        print(f"Cleaned {dir_path}")

def create_symlink(source, category, filename):
    """Create a proper symlink"""
    # Handle name conflicts by including directory in filename
    if '/' in source:
        parts = source.split('/')
        if len(parts) > 1:
            # Create unique name: dir-filename.bspl
            unique_filename = f"{parts[0]}-{filename}"
        else:
            unique_filename = filename
    else:
        unique_filename = filename
        
    link_path = Path(f"by-property/{category}") / unique_filename
    
    # Calculate correct relative path (only need ../../)
    rel_path = f"../../{source}"
    
    # Remove existing link if it exists
    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    
    link_path.symlink_to(rel_path)

def main():
    os.chdir(Path(__file__).parent)
    
    # Clean all directories
    for category in ['safe', 'unsafe', 'live', 'nonlive', 'invalid']:
        clean_directory(f'by-property/{category}')
    
    # Load verification results
    with open('by-property/verification-results.json', 'r') as f:
        results = json.load(f)
    
    # Track what we've processed
    processed = set()
    
    # Process successful verifications
    for result in results.get('successful', []):
        file_path = result['file']
        filename = Path(file_path).name
        processed.add(file_path)
        
        # Safety category
        if result.get('safe', False):
            create_symlink(file_path, 'safe', filename)
        else:
            create_symlink(file_path, 'unsafe', filename)
            
        # Liveness category  
        if result.get('live', False):
            create_symlink(file_path, 'live', filename)
        else:
            create_symlink(file_path, 'nonlive', filename)
    
    # Process errors (invalid)
    for result in results.get('errors', []):
        file_path = result['file']
        filename = Path(file_path).name
        
        # Don't add to invalid if already processed as successful
        if file_path not in processed:
            create_symlink(file_path, 'invalid', filename)
    
    # Also check the manually verified ones
    manual_verified = [
        ("trade-finance/purchase-unsafe.bspl", False, True),
        ("trade-finance/ebusiness-unsafe.bspl", False, True),
        ("trade-finance/purchase-nonlive.bspl", True, False),
        ("tests/sale-unsafe.bspl", False, True),
        ("tests/private-unsafe.bspl", False, True),
        ("tests/composition-unsafe.bspl", False, True),
        ("tests/dependent-nonlive.bspl", True, True),
        ("tests/indirect-nonlive.bspl", True, False),
        ("tests/identical-names-nonlive.bspl", True, False),
    ]
    
    for file_path, is_safe, is_live in manual_verified:
        if Path(file_path).exists() and file_path not in processed:
            filename = Path(file_path).name
            processed.add(file_path)
            
            if is_safe:
                create_symlink(file_path, 'safe', filename)
            else:
                create_symlink(file_path, 'unsafe', filename)
                
            if is_live:
                create_symlink(file_path, 'live', filename)
            else:
                create_symlink(file_path, 'nonlive', filename)
    
    # Print summary
    print("\nRecreated symlinks:")
    for category in ['safe', 'unsafe', 'live', 'nonlive', 'invalid']:
        count = len(list(Path(f'by-property/{category}').glob('*.bspl')))
        print(f"  {category}: {count}")
    
    # Test a symlink
    test_link = Path('by-property/safe/basic.bspl')
    if test_link.exists():
        print(f"\nTest symlink: {test_link} -> {test_link.readlink()}")
        print(f"Resolves to: {test_link.resolve()}")
        print(f"Target exists: {test_link.resolve().exists()}")

if __name__ == "__main__":
    main()