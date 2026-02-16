"""
Script to reduce polygon count in sat_glyphs.vtp by decimating the mesh.

This simplifies the existing geometry rather than regenerating glyphs.
"""

import pyvista as pv
import numpy as np
from scipy.spatial import cKDTree

def reduce_polygons_decimate(input_file, output_file, target_reduction=0.9):
    """
    Reduce polygon count using mesh decimation.

    Parameters:
    -----------
    input_file : str
        Path to input .vtp file
    output_file : str
        Path to output .vtp file
    target_reduction : float
        Fraction of polygons to remove (0.0 = no reduction, 0.9 = remove 90%)
    """

    print(f"Reading {input_file}...")
    mesh = pv.read(input_file)

    print(f"\nOriginal mesh:")
    print(f"  - Points: {mesh.n_points:,}")
    print(f"  - Cells: {mesh.n_cells:,}")

    # List all data arrays
    print(f"  - Point data arrays: {list(mesh.point_data.keys())}")
    print(f"  - Cell data arrays: {list(mesh.cell_data.keys())}")
    print(f"  - Field data arrays: {list(mesh.field_data.keys())}")

    # Copy field data before decimation
    field_data = {}
    for name in mesh.field_data.keys():
        field_data[name] = mesh.field_data[name]

    print(f"\nDecimating mesh (target reduction: {target_reduction*100:.0f}%)...")
    # Decimate with vtkOriginalPointIds to track which original points are kept
    decimated = mesh.decimate(target_reduction, volume_preservation=True)

    print(f"\nDecimated mesh:")
    print(f"  - Points: {decimated.n_points:,}")
    print(f"  - Cells: {decimated.n_cells:,}")
    print(f"  - Actual reduction: {100 * (1 - decimated.n_cells / mesh.n_cells):.1f}%")
    print(f"  - Point data arrays: {list(decimated.point_data.keys())}")
    print(f"  - Cell data arrays: {list(decimated.cell_data.keys())}")

    # Restore field data
    for name, data in field_data.items():
        decimated.field_data[name] = data

    # Restore point data with uniform values per glyph
    print(f"\nAssigning uniform values per glyph...")

    # First, interpolate data from original to decimated mesh
    print("  - Interpolating data from original mesh...")
    sampled = decimated.sample(mesh, tolerance=1e-6)

    # Identify connected regions in the decimated mesh (fast since it's small)
    print("  - Identifying glyphs in decimated mesh...")
    regions_dec = decimated.connectivity('all', variable_output=True)
    if 'RegionId' in regions_dec.point_data:
        region_ids = regions_dec.point_data['RegionId']
    else:
        region_ids = regions_dec.cell_data['RegionId']
        regions_dec = regions_dec.cell_data_to_point_data()
        region_ids = regions_dec.point_data['RegionId']

    n_regions = region_ids.max() + 1
    print(f"    Found {n_regions} glyphs")

    # For each data array, assign uniform mean values per region
    for name in mesh.point_data.keys():
        if name not in ['vtkOriginalPointIds', 'vtkOriginalCellIds'] and name in sampled.point_data:
            print(f"  - Processing {name}...")

            # Copy interpolated values
            decimated.point_data[name] = sampled.point_data[name].copy()

            # Calculate mean for each region and assign uniformly
            for region_id in range(n_regions):
                region_mask = (region_ids == region_id)
                if region_mask.sum() > 0:
                    region_values = decimated.point_data[name][region_mask]
                    if region_values.ndim == 1:
                        mean_value = region_values.mean()
                    else:
                        mean_value = region_values.mean(axis=0)

                    decimated.point_data[name][region_mask] = mean_value

            print(f"    Assigned uniform values for {name} across {n_regions} glyphs")

    # Save the result
    print(f"\nSaving to {output_file}...")
    decimated.save(output_file)
    print("Done!")

    return decimated


def reduce_polygons_extract_and_reglyph(input_file, output_file, phi_resolution=8, theta_resolution=8):
    """
    Extract glyph centers and regenerate with lower resolution spheres.

    This works by analyzing the existing geometry to find sphere centers,
    then creating new low-res spheres at those locations.
    """

    print(f"Reading {input_file}...")
    mesh = pv.read(input_file)

    print(f"\nOriginal mesh:")
    print(f"  - Points: {mesh.n_points:,}")
    print(f"  - Cells: {mesh.n_cells:,}")
    print(f"  - Point data arrays: {list(mesh.point_data.keys())}")
    print(f"  - Cell data arrays: {list(mesh.cell_data.keys())}")
    print(f"  - Field data arrays: {list(mesh.field_data.keys())}")

    # Try to identify if this is glyphs by analyzing the structure
    # If it's individual disconnected spheres, we can extract their centers

    # Get connected regions
    regions = mesh.connectivity('all', variable_output=True)
    n_regions = regions.n_arrays

    print(f"  - Found {n_regions} connected regions")

    if n_regions < 100:
        print("\nNOTE: Method 2 requires disconnected glyphs (100+ regions).")
        print(f"      Only {n_regions} regions found - glyphs are likely connected.")
        print("      This is normal. Use the decimated file from Method 1 instead.")
        return None

    # Extract center of each region
    print("\nExtracting glyph centers...")
    centers = []
    scales = []

    # Dictionary to store point data arrays for each glyph
    glyph_data = {}
    for name in regions.point_data.keys():
        if name != 'RegionId':
            glyph_data[name] = []

    # Get the region IDs
    if 'RegionId' in regions.point_data:
        region_ids = regions.point_data['RegionId']
    else:
        region_ids = regions.cell_data['RegionId']
        # Convert cell data to point data
        regions = regions.cell_data_to_point_data()
        region_ids = regions.point_data['RegionId']

    for region_id in range(n_regions):
        # Extract this region
        region_mask = region_ids == region_id
        region_points = regions.points[region_mask]
        if len(region_points) > 0:
            # Center is the centroid
            center = region_points.mean(axis=0)
            centers.append(center)

            # Scale is approximate sphere radius
            distances = np.linalg.norm(region_points - center, axis=1)
            scale = distances.max()
            scales.append(scale)

            # Extract point data for this region (use mean value)
            for name in glyph_data.keys():
                region_values = regions.point_data[name][region_mask]
                # Use mean for numeric data
                if region_values.ndim == 1:
                    glyph_data[name].append(region_values.mean())
                else:
                    glyph_data[name].append(region_values.mean(axis=0))

    print(f"  - Extracted {len(centers)} glyph centers")

    # Create point cloud
    point_cloud = pv.PolyData(np.array(centers))
    point_cloud.point_data['GlyphScale'] = np.array(scales)

    # Add extracted point data to the point cloud
    for name, values in glyph_data.items():
        point_cloud.point_data[name] = np.array(values)
        print(f"  - Preserved data array: {name}")

    # Copy field data
    for name in mesh.field_data.keys():
        point_cloud.field_data[name] = mesh.field_data[name]

    # Create low-resolution sphere
    sphere = pv.Sphere(radius=1.0, phi_resolution=phi_resolution, theta_resolution=theta_resolution)

    print(f"\nCreating glyphs with phi={phi_resolution}, theta={theta_resolution}...")
    print(f"  Each sphere will have ~{sphere.n_cells} polygons")

    # Apply glyphs
    glyphs = point_cloud.glyph(geom=sphere, scale='GlyphScale', orient=False)

    # Restore field data
    for name in mesh.field_data.keys():
        glyphs.field_data[name] = mesh.field_data[name]

    print(f"\nNew mesh:")
    print(f"  - Points: {glyphs.n_points:,}")
    print(f"  - Cells: {glyphs.n_cells:,}")
    print(f"  - Reduction: {100 * (1 - glyphs.n_cells / mesh.n_cells):.1f}% fewer polygons")

    # Save
    print(f"\nSaving to {output_file}...")
    glyphs.save(output_file)
    print("Done!")

    return glyphs


if __name__ == "__main__":
    import sys

    # Method 1: Simple decimation (faster, preserves structure better)
    print("=" * 60)
    print("METHOD 1: MESH DECIMATION")
    print("=" * 60)
    reduce_polygons_decimate(
        input_file="sat_glyphs.vtp",
        output_file="sat_glyphs_decimated.vtp",
        target_reduction=0.9  # Remove 90% of polygons
    )

    print("\n\n")
    print("=" * 60)
    print("METHOD 2: EXTRACT CENTERS AND RE-GLYPH")
    print("=" * 60)

    # Method 2: Extract and re-glyph (more control over sphere resolution)
    try:
        reduce_polygons_extract_and_reglyph(
            input_file="sat_glyphs.vtp",
            output_file="sat_glyphs_reglyphed.vtp",
            phi_resolution=4,
            theta_resolution=4
        )
    except Exception as e:
        print(f"\nMethod 2 not applicable: {e}")
        print("Use the decimated file from Method 1 (sat_glyphs_decimated.vtp)")
