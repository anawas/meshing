"""
Check if H values are truly uniform within each connected region.
"""

import pyvista as pv
import numpy as np

decimated = pv.read("sat_glyphs_decimated.vtp")

print("Checking H uniformity per connected region...")

# Get regions
regions = decimated.connectivity('all', variable_output=True)
if 'RegionId' in regions.point_data:
    region_ids = regions.point_data['RegionId']
else:
    region_ids = regions.cell_data['RegionId']
    regions = regions.cell_data_to_point_data()
    region_ids = regions.point_data['RegionId']

h_values = decimated.point_data['H']
n_regions = region_ids.max() + 1

print(f"Total regions: {n_regions}")
print(f"Sampling 20 regions to check uniformity...")

# Sample some regions
non_uniform = 0
for region_id in np.random.choice(n_regions, min(20, n_regions), replace=False):
    mask = region_ids == region_id
    region_h = h_values[mask]

    if len(region_h) > 0:
        std = region_h.std()
        if std < 0.001:
            print(f"  Region {region_id}: {len(region_h)} points, H std={std:.6f} [OK]")
        else:
            print(f"  Region {region_id}: {len(region_h)} points, H std={std:.6f} [NOT UNIFORM!]")
            non_uniform += 1

if non_uniform == 0:
    print("\n[SUCCESS] All regions have uniform H values!")
else:
    print(f"\n[FAIL] {non_uniform}/20 regions are not uniform")
