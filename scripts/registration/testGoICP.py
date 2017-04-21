from director.shallowCopy import shallowCopy
from director import segmentation

import os
import subprocess


def applySubdivision(polyData, subdivisions=3):
    f = vtk.vtkLoopSubdivisionFilter()
    f.SetInput(polyData)
    f.SetNumberOfSubdivisions(subdivisions)
    f.Update()
    return shallowCopy(f.GetOutput())


def applyQuadricClustering(polyData, spacing=0.01):
    f = vtk.vtkQuadricClustering()
    f.AutoAdjustNumberOfDivisionsOn()
    f.SetDivisionOrigin(0,0,0)
    f.SetDivisionSpacing(spacing, spacing, spacing)
    f.SetInput(polyData)
    f.Update()
    return shallowCopy(f.GetOutput())



def shuffleAndShiftPoints(polyData, scaleFactor=1.0, keepFirst=1000):
    '''Shuffles the points into a random order, subtracts the mean and normalizes.
    Returns a new polyData object'''
    points = vnp.getNumpyFromVtk(polyData, 'Points').copy()
    np.random.shuffle(points)
    #points = points[:keepFirst]
    points -= np.average(points, axis=0)
    return vnp.numpyToPolyData(points, createVertexCells=True)


def rescalePolyData(polyDataList):
    pointList = [vnp.getNumpyFromVtk(polyData, 'Points') for polyData in polyDataList]
    #scaleFactor = np.max([np.max(np.abs(points)) for points in pointList])
    scaleFactor = np.max([np.max(np.linalg.norm(points, axis=1)) for points in pointList])

    for points in pointList:
        points /= np.max(scaleFactor)


def writePointsFile(polyData, filename):
    points = vnp.getNumpyFromVtk(polyData, 'Points')
    f = open(filename, 'w')
    f.write('%d\n' % len(points))
    for p in points:
        f.write('%f %f %f\n' % (p[0], p[1], p[2]))
    #np.savetxt(f, points)
    f.close()


def convertMeshToPointcloud(polyData):
    polyData = applySubdivision(polyData)
    polyData = vnp.numpyToPolyData(vnp.getNumpyFromVtk(polyData, 'Points'), createVertexCells=True)
    polyData = applyQuadricClustering(polyData)
    return polyData


def removeOutliers(polyData, **kwargs):
    polyData = segmentation.labelOutliers(polyData, **kwargs)
    return filterUtils.thresholdPoints(polyData, 'is_outlier', [0.0, 0.0])


def removeOriginPoints(polyData):
    points = vnp.getNumpyFromVtk(polyData, 'Points')
    labels = np.array(np.sum(points, axis=1) == 0.0, dtype=int)
    vnp.addNumpyToVtk(polyData, labels, 'is_origin_point')
    return filterUtils.thresholdPoints(polyData, 'is_origin_point', [0.0, 0.0])


pointCloud = ioUtils.readPolyData('data/unaligned_full_pointcloud.vtp')
robotMesh = ioUtils.readPolyData('data/robot_mesh.vtp')
robotMeshPointcloud = ioUtils.readPolyData('data/robot_mesh_pointcloud.vtp')


pointCloud = removeOriginPoints(pointCloud)


robotMeshPointcloud = shuffleAndShiftPoints(robotMeshPointcloud)
pointCloud = shuffleAndShiftPoints(pointCloud)

rescalePolyData([pointCloud, robotMeshPointcloud])

print pointCloud.GetNumberOfPoints()
print robotMeshPointcloud.GetNumberOfPoints()

vis.showPolyData(robotMeshPointcloud, 'model pointcloud')
vis.showPolyData(pointCloud, 'scene pointcloud')

d = DebugData()
d.addSphere((0,0,0), radius=1)
vis.showPolyData(d.getPolyData(), 'unit sphere', alpha=0.1)

view.resetCamera()
view.forceRender()


scenePointCloud = pointCloud
modelPointCloud = robotMeshPointcloud

scenePointCloud, modelPointCloud = modelPointCloud, scenePointCloud

writePointsFile(modelPointCloud, 'model_data.txt')
writePointsFile(scenePointCloud, 'scene_data.txt')

goIcpBin = '/home/pat/source/goicp/GoICP_V1.3/demo/GoICP'
outputFile = 'goicp_output.txt'
goIcpArgs = [
    goIcpBin,
#    '/home/pat/source/goicp/GoICP_V1.3/demo/model_bunny.txt',
#    '/home/pat/source/goicp/GoICP_V1.3/demo/data_bunny.txt',

    'model_data.txt',
    'scene_data.txt',
    '1000',
    '/home/pat/source/goicp/GoICP_V1.3/demo/config.txt',
    outputFile]

if os.path.isfile(outputFile):
    print 'removing', outputFile
    os.remove(outputFile)


print 'calling goicp...'
print
print ' '.join(goIcpArgs)


subprocess.check_call(goIcpArgs)

print 'done.'

assert os.path.isfile(outputFile)

data = open(outputFile).readlines()
print data

T = np.eye(4)
T[:3,:3] = np.array([np.fromstring(l, sep=' ') for l in [data[1], data[2], data[3]]])
T[:3, 3] = [float(x) for x in [data[4], data[5], data[6]]]

print T


transformedPointCloud = filterUtils.transformPolyData(scenePointCloud, transformUtils.getTransformFromNumpy(T))

vis.showPolyData(transformedPointCloud, 'transformed pointcloud')


