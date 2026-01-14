import pyvista as pv
import numpy as np
import random

# Define a simple Gaussian surface
n = 20
x = np.linspace(-200, 200, num=n) + np.random.uniform(10, 50, size=n)
y = np.linspace(-200, 200, num=n) + np.random.uniform(10, 50, size=n)
xx, yy = np.meshgrid(x, y)
A, b = 100, 100
zz = np.random.uniform(1, 10, size=n*n)

# Get the points as a 2D NumPy array (N by 3)
points = np.c_[xx.reshape(-1), yy.reshape(-1), zz.reshape(-1)]

cloud = pv.PolyData(points)
cloud.plot(point_size=15)

surf = cloud.delaunay_2d()

# And plot it with edges shown
surf.plot(show_edges=True)