#!/usr/bin/env python3
"""
Fix protocol names with spaces and re-run verification
"""

import subprocess
import os
from pathlib import Path

# List of files that likely have protocol names with spaces
files_to_check = [
    "trade-finance/purchase-unsafe.bspl",
    "trade-finance/ebusiness-unsafe.bspl",
    "trade-finance/purchase-nonlive.bspl",
    "tests/sale-unsafe.bspl",
    "tests/private-unsafe.bspl",
    "tests/composition-unsafe.bspl",
    "tests/dependent-nonlive.bspl",
    "tests/indirect-nonlive.bspl",
    "tests/identical-names-nonlive.bspl"
]

def verify_single_file(filepath):
    """Verify a single file and return results"""
    print(f"\nVerifying {filepath}...")
    try:
        result = subprocess.run(
            ['bspl', 'verify', 'all', filepath],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            # Parse output
            lines = result.stdout.strip().split('\n')
            safe = False
            live = False
            
            for line in lines:
                if "'safe': False" in line:
                    safe = False
                elif "'safe': True" in line:
                    safe = True
                if "'live': False" in line:
                    live = False
                elif "'live': True" in line:
                    live = True
                    
            status = []
            status.append("safe" if safe else "unsafe")
            status.append("live" if live else "nonlive")
            
            print(f"  Result: {', '.join(status)}")
            
            # Create appropriate symlinks
            filename = Path(filepath).name
            
            if safe:
                link_path = Path("by-property/safe") / filename
            else:
                link_path = Path("by-property/unsafe") / filename
                
            if link_path.exists():
                link_path.unlink()
            rel_path = os.path.relpath(Path(filepath).absolute(), link_path.parent.absolute())
            link_path.symlink_to(rel_path)
            
            if live:
                link_path = Path("by-property/live") / filename
            else:
                link_path = Path("by-property/nonlive") / filename
                
            if link_path.exists():
                link_path.unlink()
            rel_path = os.path.relpath(Path(filepath).absolute(), link_path.parent.absolute())
            link_path.symlink_to(rel_path)
            
            return True
        else:
            print(f"  Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  Exception: {e}")
        return False

def main():
    os.chdir(Path(__file__).parent)
    
    print("Checking and verifying protocols with potential issues...")
    
    success_count = 0
    for filepath in files_to_check:
        if Path(filepath).exists():
            if verify_single_file(filepath):
                success_count += 1
        else:
            print(f"\nFile not found: {filepath}")
    
    print(f"\n\nSuccessfully verified and linked {success_count} protocols")
    
    # Show updated counts
    print("\nUpdated category counts:")
    for category in ['safe', 'unsafe', 'live', 'nonlive']:
        count = len(list(Path(f"by-property/{category}").glob("*.bspl")))
        print(f"  {category}: {count} protocols")

if __name__ == "__main__":
    main()