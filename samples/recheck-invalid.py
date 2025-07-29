#!/usr/bin/env python3
"""
Re-check all protocols currently in invalid/ to see if they actually verify
"""

import subprocess
from pathlib import Path
import os

def verify_protocol(bspl_file):
    """Run bspl verify all and parse results properly"""
    try:
        # First check syntax
        syntax_result = subprocess.run(
            ['bspl', 'check-syntax', bspl_file],
            capture_output=True,
            text=True,
            check=False
        )
        
        if syntax_result.returncode != 0:
            return {'file': bspl_file, 'error': 'Syntax check failed', 'details': syntax_result.stderr}
        
        # Check for actual syntax errors in output
        if "Syntax: correct" not in syntax_result.stdout:
            # Extract error message
            error_lines = [line for line in syntax_result.stdout.split('\n') if line.strip() and "Warning:" not in line and bspl_file not in line]
            error_msg = '\n'.join(error_lines)
            return {'file': bspl_file, 'error': 'Syntax error', 'details': error_msg}
        
        # Now run full verification
        result = subprocess.run(
            ['bspl', 'verify', 'all', bspl_file],
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )
        
        if result.returncode != 0:
            return {'file': bspl_file, 'error': 'Verification failed', 'details': result.stderr}
        
        # Parse output more carefully
        lines = result.stdout.strip().split('\n')
        safe = None
        live = None
        
        for line in lines:
            if "'safe': True" in line:
                safe = True
            elif "'safe': False" in line:
                safe = False
            if "'live': True" in line:
                live = True
            elif "'live': False" in line:
                live = False
        
        if safe is None or live is None:
            return {'file': bspl_file, 'error': 'Could not parse verification output', 'details': result.stdout}
        
        return {
            'file': bspl_file,
            'safe': safe,
            'live': live,
            'verified': True
        }
        
    except subprocess.TimeoutExpired:
        return {'file': bspl_file, 'error': 'Timeout'}
    except Exception as e:
        return {'file': bspl_file, 'error': str(e)}

def main():
    os.chdir(Path(__file__).parent)
    
    invalid_dir = Path('by-property/invalid')
    protocols = list(invalid_dir.glob('*.bspl'))
    
    print(f"Re-checking {len(protocols)} protocols currently marked as invalid...\n")
    
    actually_invalid = []
    should_be_valid = []
    
    for protocol in sorted(protocols):
        # Get the target of the symlink
        target = protocol.readlink()
        # Make it relative to current directory
        full_path = str(target).replace('../../', '')
        
        print(f"Checking {protocol.name}...")
        result = verify_protocol(full_path)
        
        if result.get('verified'):
            should_be_valid.append(result)
            print(f"  ✓ Actually valid! Safe: {result['safe']}, Live: {result['live']}")
        else:
            actually_invalid.append(result)
            print(f"  ✗ Invalid: {result.get('error', 'Unknown error')}")
            if result.get('details') and len(result['details']) < 100:
                print(f"    Details: {result['details']}")
    
    print(f"\n=== Summary ===")
    print(f"Actually invalid: {len(actually_invalid)}")
    print(f"Should be valid: {len(should_be_valid)}")
    
    if should_be_valid:
        print("\nProtocols that should be moved out of invalid:")
        for result in should_be_valid:
            filename = Path(result['file']).name
            prefix = result['file'].split('/')[0]
            link_name = f"{prefix}-{filename}"
            print(f"  {link_name}: Safe={result['safe']}, Live={result['live']}")
    
    if actually_invalid:
        print("\nProtocols that are truly invalid:")
        for result in actually_invalid[:5]:  # Show first 5
            print(f"  {result['file']}: {result['error']}")
        if len(actually_invalid) > 5:
            print(f"  ... and {len(actually_invalid) - 5} more")

if __name__ == "__main__":
    main()