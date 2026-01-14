import numpy as np
import pyvista as pv
from pyvista import PolyData

data: PolyData = pv.examples.download_armadillo()

data.save("mesh.vtp", binary=True)
"""
vtk_plotter = pv.Plotter(off_screen=True)
vtk_plotter.add_mesh(data)
out = vtk_plotter.export_vtksz("szene.vtksz")
print("Export: ", out)
"""