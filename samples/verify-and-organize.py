#!/usr/bin/env python3
"""
Verify all BSPL protocols and create symbolic links in by-property directory
based on their verification results.
"""

import os
import subprocess
import json
from pathlib import Path
import glob

def verify_protocol(bspl_file):
    """Run bspl verify all on a protocol and return the results."""
    try:
        result = subprocess.run(
            ['bspl', 'verify', 'all', bspl_file],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"Error verifying {bspl_file}: {result.stderr}")
            return None
            
        # Parse the output to extract safety and liveness results
        output_lines = result.stdout.strip().split('\n')
        
        safety_result = None
        liveness_result = None
        
        for line in output_lines:
            if line.strip().startswith('{') and "'safe':" in line:
                safety_result = eval(line.strip())
            elif line.strip().startswith('{') and "'live':" in line:
                liveness_result = eval(line.strip())
        
        return {
            'file': bspl_file,
            'safe': safety_result.get('safe', False) if safety_result else False,
            'live': liveness_result.get('live', False) if liveness_result else False,
            'safety_paths': safety_result.get('paths', 0) if safety_result else 0,
            'liveness_paths': liveness_result.get('paths', 0) if liveness_result else 0
        }
        
    except Exception as e:
        print(f"Exception verifying {bspl_file}: {e}")
        return None

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
    print(f"  Linked: {link_name} -> {rel_path}")

def main():
    # Change to samples directory
    samples_dir = Path(__file__).parent
    os.chdir(samples_dir)
    
    # Find all .bspl files (excluding by-property directory)
    bspl_files = []
    for pattern in ['**/*.bspl']:
        for file in glob.glob(pattern, recursive=True):
            if 'by-property' not in file and file.endswith('.bspl'):
                bspl_files.append(file)
    
    print(f"Found {len(bspl_files)} BSPL files to verify\n")
    
    # Verify each protocol
    results = []
    for bspl_file in sorted(bspl_files):
        print(f"Verifying {bspl_file}...")
        result = verify_protocol(bspl_file)
        if result:
            results.append(result)
            print(f"  Safe: {result['safe']}, Live: {result['live']}")
    
    print(f"\nSuccessfully verified {len(results)} protocols")
    
    # Create symbolic links based on results
    print("\nCreating symbolic links...")
    
    safe_count = 0
    unsafe_count = 0
    live_count = 0
    nonlive_count = 0
    
    for result in results:
        file_path = result['file']
        file_name = Path(file_path).name
        
        # Link to safe or unsafe
        if result['safe']:
            create_symlink(f"../{file_path}", "by-property/safe", file_name)
            safe_count += 1
        else:
            create_symlink(f"../{file_path}", "by-property/unsafe", file_name)
            unsafe_count += 1
        
        # Link to live or nonlive
        if result['live']:
            create_symlink(f"../{file_path}", "by-property/live", file_name)
            live_count += 1
        else:
            create_symlink(f"../{file_path}", "by-property/nonlive", file_name)
            nonlive_count += 1
    
    # Print summary
    print("\n=== Summary ===")
    print(f"Total protocols verified: {len(results)}")
    print(f"Safe protocols: {safe_count}")
    print(f"Unsafe protocols: {unsafe_count}")
    print(f"Live protocols: {live_count}")
    print(f"Nonlive protocols: {nonlive_count}")
    
    # Save detailed results
    results_file = "by-property/verification-results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {results_file}")

if __name__ == "__main__":
    main()