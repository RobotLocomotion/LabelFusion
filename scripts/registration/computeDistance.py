from director import objectmodel as om
from director import vtkAll as vtk
from director import vtkNumpy as vnp

import numpy as np

def computePointToSurfaceDistance(pointsPolyData, meshPolyData):

    cl = vtk.vtkCellLocator()
    cl.SetDataSet(meshPolyData)
    cl.BuildLocator()

    points = vnp.getNumpyFromVtk(pointsPolyData, 'Points')
    dists = np.zeros(len(points))


    closestPoint = np.zeros(3)
    closestPointDist = vtk.mutable(0.0)
    cellId = vtk.mutable(0)
    subId = vtk.mutable(0)

    for i in xrange(len(points)):
        cl.FindClosestPoint(points[i], closestPoint, cellId, subId, closestPointDist)
        dists[i] = closestPointDist

    return np.sqrt(dists)


def computePointToPointDistance(pointsPolyData, searchPolyData):

    cl = vtk.vtkPointLocator()
    cl.SetDataSet(searchPolyData)
    cl.BuildLocator()

    points = vnp.getNumpyFromVtk(pointsPolyData, 'Points')
    searchPoints = vnp.getNumpyFromVtk(searchPolyData, 'Points')
    closestPoints = np.zeros((len(points),3))

    for i in xrange(len(points)):
        ptId = cl.FindClosestPoint(points[i])
        closestPoints[i] = searchPoints[ptId]

    return np.linalg.norm(closestPoints - points, axis=1)


def computeAndColorByDistance(ptsName, meshName, colorByRange=[0.0, 0.05], arrayName='distance_to_mesh'):

    pointCloud = om.findObjectByName(ptsName)
    mesh = om.findObjectByName(meshName)

    isPointCloud = mesh._isPointCloud()

    assert pointCloud is not None
    assert mesh is not None

    dists = computePointToPointDistance(pointCloud.polyData, mesh.polyData)

    vnp.addNumpyToVtk(pointCloud.polyData, dists, arrayName)

    pointCloud._updateColorByProperty()
    pointCloud.setProperty('Color By', arrayName)
    pointCloud.colorBy(arrayName, colorByRange)

    return pointCloud
