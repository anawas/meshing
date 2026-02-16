"""
Test script to verify H data is correctly preserved in the decimated file.
"""

import pyvista as pv
import numpy as np

def test_h_preservation():
    print("="*60)
    print("Testing H Data Preservation")
    print("="*60)

    # Load original and decimated meshes
    print("\nLoading files...")
    original = pv.read("sat_glyphs.vtp")
    decimated = pv.read("sat_glyphs_decimated.vtp")

    print(f"\nOriginal mesh:")
    print(f"  Points: {original.n_points:,}")
    print(f"  Cells: {original.n_cells:,}")
    print(f"  Point data: {list(original.point_data.keys())}")

    print(f"\nDecimated mesh:")
    print(f"  Points: {decimated.n_points:,}")
    print(f"  Cells: {decimated.n_cells:,}")
    print(f"  Point data: {list(decimated.point_data.keys())}")
    print(f"  Reduction: {100 * (1 - decimated.n_cells / original.n_cells):.1f}%")

    # Check if H exists in both
    print("\n" + "="*60)
    print("H Data Verification")
    print("="*60)

    if 'H' not in original.point_data:
        print("[ERROR] H not found in original mesh!")
        return False

    if 'H' not in decimated.point_data:
        print("[ERROR] H not found in decimated mesh!")
        return False

    print("[OK] H data found in both meshes")

    # Compare H statistics
    h_orig = original.point_data['H']
    h_dec = decimated.point_data['H']

    print(f"\nOriginal H data:")
    print(f"  Shape: {h_orig.shape}")
    print(f"  Min: {h_orig.min():.3f}")
    print(f"  Max: {h_orig.max():.3f}")
    print(f"  Mean: {h_orig.mean():.3f}")
    print(f"  Std: {h_orig.std():.3f}")

    print(f"\nDecimated H data:")
    print(f"  Shape: {h_dec.shape}")
    print(f"  Min: {h_dec.min():.3f}")
    print(f"  Max: {h_dec.max():.3f}")
    print(f"  Mean: {h_dec.mean():.3f}")
    print(f"  Std: {h_dec.std():.3f}")

    # Check if statistics are similar (allowing for interpolation differences)
    min_diff = abs(h_orig.min() - h_dec.min())
    max_diff = abs(h_orig.max() - h_dec.max())
    mean_diff = abs(h_orig.mean() - h_dec.mean())

    print(f"\nDifferences:")
    print(f"  Min diff: {min_diff:.3f}")
    print(f"  Max diff: {max_diff:.3f}")
    print(f"  Mean diff: {mean_diff:.3f}")

    # Check field data preservation
    print("\n" + "="*60)
    print("Field Data Verification")
    print("="*60)

    for name in original.field_data.keys():
        if name in decimated.field_data:
            print(f"[OK] {name}: preserved")
        else:
            print(f"[FAIL] {name}: missing")

    # Final assessment
    print("\n" + "="*60)
    print("RESULT")
    print("="*60)

    if 'H' in decimated.point_data and max_diff < 1.0:  # Allow small differences
        print("[OK] SUCCESS: H data correctly preserved in decimated file!")
        print(f"   - Reduction: {100 * (1 - decimated.n_cells / original.n_cells):.1f}%")
        print(f"   - File ready for use in webapp")
        return True
    else:
        print("[FAIL] FAILED: H data not properly preserved")
        return False

if __name__ == "__main__":
    success = test_h_preservation()
    exit(0 if success else 1)
