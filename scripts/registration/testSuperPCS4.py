from director.shallowCopy import shallowCopy
from director import segmentation

import os
import subprocess


import os
import computeDistance


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



def readSuperPCS4TransformFile(outputFile):
    assert os.path.isfile(outputFile)
    data = open(outputFile).readlines()
    T = np.array([np.fromstring(l, sep=' ') for l in data[2:6]])
    return T


def showAlignedData(objName, outputFile):

    T = readSuperPCS4TransformFile(outputFile)
    polyData = om.findObjectByName(objName).polyData
    transformedPointCloud = filterUtils.transformPolyData(polyData, transformUtils.getTransformFromNumpy(T))
    vis.showPolyData(transformedPointCloud, objName + ' aligned')


def runSuperPCS4(modelName, sceneName):

    modelPointCloud = om.findObjectByName(modelName).polyData
    scenePointCloud = om.findObjectByName(sceneName).polyData

    modelFile = 'model_data_for_pcs4.ply'
    sceneFile = 'scene_data_for_pcs4.ply'

    ioUtils.writePolyData(modelPointCloud, modelFile)
    ioUtils.writePolyData(scenePointCloud, sceneFile)

    registrationBin = '/home/pat/source/Super4PCS/build/Super4PCS'
    outputFile = 'pcs4_mat_output.txt'
    overlap = 0.9
    distance = 0.02
    timeout = 1000
    numSamples = 200

    registrationArgs = [
        registrationBin,
        '-i',
        modelFile,
        sceneFile,
        '-o %f' % overlap,
        '-d %f' % distance,
        '-t %d' % timeout,
        '-n %d' % numSamples,
        '-r pcs4_transformed_output.ply',
        '-m %s' % outputFile]

    registrationArgs = ' '.join(registrationArgs).split()


    if os.path.isfile(outputFile):
        print 'removing', outputFile
        os.remove(outputFile)


    print 'calling super pcs4...'
    print
    print ' '.join(registrationArgs)


    subprocess.check_call(registrationArgs)

    print 'done.'

    showAlignedData(sceneName, outputFile)


def computeAlignmentScore(objA, objB, distanceThreshold=0.02):

    arrayName = 'distance_to_model'
    computeDistance.computeAndColorByDistance(objA, objB, colorByRange=[0.0, distanceThreshold], arrayName=arrayName)

    polyData = om.findObjectByName(objA).polyData
    polyData = filterUtils.thresholdPoints(polyData, arrayName, [0.0, distanceThreshold])
    lcpScore = float(polyData.GetNumberOfPoints())/om.findObjectByName(objA).polyData.GetNumberOfPoints()

    vis.showPolyData(polyData, '%s (dist threshold %.03f)' % (objA, distanceThreshold), colorByName=arrayName)
    print 'LCP percent (%s):' % objA, lcpScore


pointCloud = ioUtils.readPolyData('data/unaligned_full_pointcloud.vtp')
robotMesh = ioUtils.readPolyData('data/robot_mesh.vtp')
robotMeshPointcloud = ioUtils.readPolyData('data/robot_mesh_pointcloud.vtp')



# PCS4 algorithm performs very differently if you remove the origin point
#pointCloud = removeOriginPoints(pointCloud)


pointCloud = segmentation.applyVoxelGrid(pointCloud, leafSize=0.01)

#robotMeshPointcloud = shuffleAndShiftPoints(robotMeshPointcloud)
#pointCloud = shuffleAndShiftPoints(pointCloud)


print pointCloud.GetNumberOfPoints()
print robotMeshPointcloud.GetNumberOfPoints()

vis.showPolyData(robotMeshPointcloud, 'model pointcloud')
vis.showPolyData(pointCloud, 'scene pointcloud')


view.resetCamera()
view.forceRender()


sceneName = 'scene pointcloud'
modelName = 'model pointcloud'

runSuperPCS4(modelName, sceneName)

alignedSceneName = sceneName + ' aligned'
computeAlignmentScore(alignedSceneName, modelName)
computeAlignmentScore(modelName, alignedSceneName)

