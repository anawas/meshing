"""
Verify that H values are uniform within each glyph (sphere).
"""

import pyvista as pv
import numpy as np
from scipy.spatial import cKDTree

def verify_uniform_values():
    print("="*60)
    print("Verifying Uniform H Values Per Glyph")
    print("="*60)

    decimated = pv.read("sat_glyphs_decimated.vtp")

    print(f"\nDecimated mesh:")
    print(f"  Points: {decimated.n_points:,}")
    print(f"  Cells: {decimated.n_cells:,}")

    # Get typical sphere radius
    typical_radius = np.median(decimated.point_data['GlyphScale'])
    print(f"  Typical sphere radius: {typical_radius:.2f}")

    # Check H values
    h_values = decimated.point_data['H']
    print(f"\nH data:")
    print(f"  Min: {h_values.min():.3f}")
    print(f"  Max: {h_values.max():.3f}")
    print(f"  Unique values: {len(np.unique(h_values))}")

    # Sample a few random points and check if nearby points have the same H value
    print(f"\n Checking uniformity within spheres...")
    tree = cKDTree(decimated.points)

    num_samples = 10
    all_uniform = True

    for i in np.random.choice(decimated.n_points, min(num_samples, decimated.n_points), replace=False):
        # Find nearby points within sphere
        nearby = tree.query_ball_point(decimated.points[i], r=typical_radius * 1.5)

        if len(nearby) > 1:
            h_cluster = h_values[nearby]
            h_std = h_cluster.std()

            if h_std < 0.01:  # Nearly uniform
                print(f"  [OK] Point {i}: cluster size={len(nearby)}, H std={h_std:.6f}")
            else:
                print(f"  [WARN] Point {i}: cluster size={len(nearby)}, H std={h_std:.6f} (not uniform)")
                all_uniform = False

    print("\n" + "="*60)
    if all_uniform:
        print("[SUCCESS] H values are uniform within each glyph!")
        print("Each sphere will display as a single solid color.")
    else:
        print("[WARNING] Some variation detected within glyphs")
    print("="*60)

if __name__ == "__main__":
    verify_uniform_values()
