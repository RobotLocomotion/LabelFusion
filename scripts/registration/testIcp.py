from director import objectmodel as om
from director import ioUtils
from director import visualization as vis
from director import transformUtils
from director import segmentation
from director.debugVis import DebugData
from director import vtkAll as vtk
from director import vtkNumpy as vnp
import numpy as np





polyData = ioUtils.readPolyData('snapshot_2.vtp')

polyData = segmentation.cropToBounds(polyData, vtk.vtkTransform(), [[-10,10],[-10,10],[0.15,10]])

polyData = segmentation.applyVoxelGrid(polyData, leafSize=0.01)
polyData = segmentation.applyEuclideanClustering(polyData, clusterTolerance=0.04)
polyData = segmentation.thresholdPoints(polyData, 'cluster_labels', [1,1])

vis.showPolyData(polyData, 'snapshot_2', colorByName='rgb_colors', visible=True)



robotMesh = ioUtils.readPolyData('robot_mesh_2.vtp')
vis.showPolyData(robotMesh, 'robot_mesh_2', visible=True)


t = segmentation.applyICP(polyData, robotMesh)


print t.GetPosition()
print t.GetOrientation()

polyData = filterUtils.transformPolyData(polyData, t)
vis.showPolyData(polyData, 'transformed pointcloud', colorByName='rgb_colors', visible=False)
