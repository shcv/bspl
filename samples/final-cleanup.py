#!/usr/bin/env python3
"""
Final cleanup - remove protocols from invalid if they were successfully verified manually
"""

from pathlib import Path

# These were manually verified and should NOT be in invalid
manually_verified = [
    "trade-finance-purchase-unsafe.bspl",
    "trade-finance-ebusiness-unsafe.bspl", 
    "trade-finance-purchase-nonlive.bspl",
    "tests-sale-unsafe.bspl",
    "tests-private-unsafe.bspl",
    "tests-composition-unsafe.bspl",
    "tests-dependent-nonlive.bspl",
    "tests-indirect-nonlive.bspl",
    "tests-identical-names-nonlive.bspl"
]

invalid_dir = Path("by-property/invalid")

removed = 0
for filename in manually_verified:
    link_path = invalid_dir / filename
    if link_path.exists():
        link_path.unlink()
        print(f"Removed {filename} from invalid")
        removed += 1

print(f"\nRemoved {removed} incorrectly categorized files from invalid/")

# Show updated counts
for category in ['safe', 'unsafe', 'live', 'nonlive', 'invalid']:
    count = len(list(Path(f'by-property/{category}').glob('*.bspl')))
    print(f"{category}: {count}")