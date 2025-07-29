#!/usr/bin/env python3
"""
Verify all BSPL protocols in parallel and create symbolic links in by-property directory
based on their verification results.
"""

import os
import subprocess
import json
from pathlib import Path
import glob
from concurrent.futures import ProcessPoolExecutor, as_completed
import sys
import ast

def verify_protocol(bspl_file):
    """Run bspl verify all on a protocol and return the results."""
    try:
        result = subprocess.run(
            ['bspl', 'verify', 'all', bspl_file],
            capture_output=True,
            text=True,
            check=False,
            timeout=30  # 30 second timeout per file
        )
        
        if result.returncode != 0:
            return {
                'file': bspl_file,
                'error': f"Return code {result.returncode}: {result.stderr}",
                'safe': False,
                'live': False
            }
            
        # Parse the output to extract safety and liveness results
        output = result.stdout.strip()
        
        safety_result = None
        liveness_result = None
        
        # The output contains multiple JSON objects, one per line
        # We need to parse each one separately
        
        for line in output.split('\n'):
            line = line.strip()
            if not line or not line.startswith('{'):
                continue
            
            try:
                # Try to parse as a dictionary
                result_dict = ast.literal_eval(line)
                
                # Check if it's a safety result
                if 'safe' in result_dict:
                    safety_result = result_dict
                # Check if it's a liveness result
                elif 'live' in result_dict:
                    liveness_result = result_dict
            except (ValueError, SyntaxError):
                # If parsing fails, try to extract the type from the line
                if "'safe':" in line or '"safe":' in line:
                    # Try to fix common JSON issues
                    try:
                        # Replace single quotes with double quotes for valid JSON
                        json_line = line.replace("'", '"')
                        safety_result = json.loads(json_line)
                    except:
                        pass
                elif "'live':" in line or '"live":' in line:
                    try:
                        json_line = line.replace("'", '"')
                        liveness_result = json.loads(json_line)
                    except:
                        pass
        
        return {
            'file': bspl_file,
            'safe': safety_result.get('safe', False) if safety_result else False,
            'live': liveness_result.get('live', False) if liveness_result else False,
            'safety_paths': safety_result.get('paths', 0) if safety_result else 0,
            'liveness_paths': liveness_result.get('paths', 0) if liveness_result else 0
        }
        
    except subprocess.TimeoutExpired:
        return {
            'file': bspl_file,
            'error': 'Timeout',
            'safe': False,
            'live': False
        }
    except Exception as e:
        return {
            'file': bspl_file,
            'error': str(e),
            'safe': False,
            'live': False
        }

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

def main():
    # Change to samples directory
    samples_dir = Path(__file__).parent
    os.chdir(samples_dir)
    
    # Create by-property directories if they don't exist
    for dir_name in ['by-property/safe', 'by-property/unsafe', 'by-property/live', 
                     'by-property/nonlive', 'by-property/invalid']:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
    
    # Find all .bspl files (excluding by-property directory)
    bspl_files = []
    for pattern in ['**/*.bspl']:
        for file in glob.glob(pattern, recursive=True):
            if 'by-property' not in file and file.endswith('.bspl'):
                bspl_files.append(file)
    
    print(f"Found {len(bspl_files)} BSPL files to verify\n")
    
    # Verify protocols in parallel
    results = []
    errors = []
    
    max_workers = min(8, os.cpu_count() or 4)  # Limit parallel processes
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all verification tasks
        future_to_file = {executor.submit(verify_protocol, f): f for f in sorted(bspl_files)}
        
        # Process results as they complete
        for future in as_completed(future_to_file):
            bspl_file = future_to_file[future]
            try:
                result = future.result()
                if 'error' in result:
                    errors.append(result)
                    print(f"✗ {bspl_file}: {result['error']}")
                else:
                    results.append(result)
                    status = []
                    if result['safe']:
                        status.append('safe')
                    else:
                        status.append('unsafe')
                    if result['live']:
                        status.append('live')
                    else:
                        status.append('nonlive')
                    print(f"✓ {bspl_file}: {', '.join(status)}")
            except Exception as e:
                print(f"✗ {bspl_file}: Exception: {e}")
                errors.append({'file': bspl_file, 'error': str(e)})
    
    print(f"\nSuccessfully verified {len(results)} protocols")
    if errors:
        print(f"Failed to verify {len(errors)} protocols")
    
    # Create symbolic links based on results
    print("\nCreating symbolic links...")
    
    safe_count = 0
    unsafe_count = 0
    live_count = 0
    nonlive_count = 0
    invalid_count = 0
    
    for result in results:
        file_path = result['file']
        file_name = Path(file_path).name
        
        # Check for duplicate names and add directory prefix if needed
        if Path(f"by-property/safe/{file_name}").exists() or \
           Path(f"by-property/unsafe/{file_name}").exists() or \
           Path(f"by-property/live/{file_name}").exists() or \
           Path(f"by-property/nonlive/{file_name}").exists() or \
           Path(f"by-property/invalid/{file_name}").exists():
            # Add directory prefix to avoid conflicts
            dir_name = Path(file_path).parent.name
            file_name = f"{dir_name}-{file_name}"
        
        # Link to safe or unsafe
        if result['safe']:
            create_symlink(file_path, "by-property/safe", file_name)
            safe_count += 1
        else:
            create_symlink(file_path, "by-property/unsafe", file_name)
            unsafe_count += 1
        
        # Link to live or nonlive
        if result['live']:
            create_symlink(file_path, "by-property/live", file_name)
            live_count += 1
        else:
            create_symlink(file_path, "by-property/nonlive", file_name)
            nonlive_count += 1
    
    # Handle errors - create links in invalid directory
    for error in errors:
        file_path = error['file']
        file_name = Path(file_path).name
        
        # Check for duplicate names
        if Path(f"by-property/invalid/{file_name}").exists():
            dir_name = Path(file_path).parent.name
            file_name = f"{dir_name}-{file_name}"
        
        create_symlink(file_path, "by-property/invalid", file_name)
        invalid_count += 1
    
    # Print summary
    print("\n=== Summary ===")
    print(f"Total protocols processed: {len(bspl_files)}")
    print(f"Successfully verified: {len(results)}")
    print(f"Failed verification: {len(errors)}")
    print(f"\nSafe protocols: {safe_count}")
    print(f"Unsafe protocols: {unsafe_count}")
    print(f"Live protocols: {live_count}")
    print(f"Nonlive protocols: {nonlive_count}")
    print(f"Invalid protocols: {invalid_count}")
    
    # Save detailed results
    all_results = {
        'successful': results,
        'errors': errors,
        'summary': {
            'total': len(bspl_files),
            'verified': len(results),
            'failed': len(errors),
            'safe': safe_count,
            'unsafe': unsafe_count,
            'live': live_count,
            'nonlive': nonlive_count,
            'invalid': invalid_count
        }
    }
    
    results_file = "by-property/verification-results.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nDetailed results saved to: {results_file}")

if __name__ == "__main__":
    main()