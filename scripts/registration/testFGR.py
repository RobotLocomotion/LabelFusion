from director import objectmodel as om
from director import ioUtils
from director import visualization as vis
from director import transformUtils
from director import filterUtils
from director import segmentation
from director import applogic
from director.debugVis import DebugData
from director import viewbehaviors
from director import vtkAll as vtk
from director import vtkNumpy as vnp
from director import segmentation
from director.shallowCopy import shallowCopy

import os
import numpy as np
import subprocess

import PythonQt
from PythonQt import QtGui, QtCore



def computePointFeatureHistograms(polyData, searchRadius=0.10):
    f = vtk.vtkPCLFPFHEstimation()
    f.SetInput(polyData)
    f.SetSearchRadius(searchRadius)
    f.Update()
    return shallowCopy(f.GetOutput())


def removeFile(filename):
    if os.path.isfile(filename):
        os.remove(filename)


def renameFeaturesFile(newName):
    assert os.path.isfile('features.bin')
    os.rename('features.bin', newName)


def loadTransformFromFile(filename):
    lines = open(filename).readlines()
    data = np.array([[float(x) for x in line.split()] for line in lines[1:]])
    return transformUtils.getTransformFromNumpy(data)


def showTransformedData(name):
    obj = om.findObjectByName(name)
    t = loadTransformFromFile('output.txt')
    pd = filterUtils.transformPolyData(obj.polyData, t)
    vis.showPolyData(pd, name + ' transformed')


def testAlign(modelName, sceneName):

    removeFile('model_features.bin')
    removeFile('scene_features.bin')
    removeFile('features.bin')

    for objType, objName in [('model', modelName), ('scene', sceneName)]:
        print 'process', objName
        pd = om.findObjectByName(objName).polyData
        pd = segmentation.applyVoxelGrid(pd, leafSize=0.005)
        print 'compute normals...'
        pd = segmentation.normalEstimation(pd, searchRadius=0.05, useVoxelGrid=False, voxelGridLeafSize=0.01)

        print 'compute features...'
        computePointFeatureHistograms(pd, searchRadius=0.10)
        renameFeaturesFile(objType + '_features.bin')

    print 'run registration...'
    subprocess.check_call(['bash', 'runFGR.sh'])

    showTransformedData(sceneName)

    print 'done.'





segmentation.SegmentationContext.initWithUser(0.0, vtk.vtkTransform(), viewAxis=2)





robotMesh = ioUtils.readPolyData('robot-mesh.vtp')

t = transformUtils.frameFromPositionAndRPY([0.0, 0.0, 2.0], [90,0,0])
robotMesh = filterUtils.transformPolyData(robotMesh, t)

robotMesh.GetPointData().SetNormals(None)
obj = vis.showPolyData(robotMesh, 'robot mesh', visible=False)

subd = vtk.vtkLoopSubdivisionFilter()
subd.SetInput(robotMesh)
subd.SetNumberOfSubdivisions(3)
subd.Update()
subdividedMesh = subd.GetOutput()

modelPoints = segmentation.applyVoxelGrid(subdividedMesh, leafSize=0.005)
vis.showPolyData(modelPoints, 'model points')
print 'model pts:', modelPoints.GetNumberOfPoints()


pointCloud = ioUtils.readPolyData('pointcloud.vtp')
obj = vis.showPolyData(pointCloud, 'pointcloud original')

'''
t = transformUtils.frameFromPositionAndRPY([0.2, 0.3, 0.4], [10,14,15])
pointCloud = filterUtils.transformPolyData(pointCloud, t)

scenePoints = segmentation.applyVoxelGrid(pointCloud, leafSize=0.005)
vis.showPolyData(scenePoints, 'scene points')
print 'scene pts:', scenePoints.GetNumberOfPoints()
'''

testAlign('model points', 'pointcloud original')



'''


pd = modelPoints


print 'compute normals...'
pd = segmentation.normalEstimation(pd, searchRadius=0.05, useVoxelGrid=False, voxelGridLeafSize=0.01)


computePointFeatureHistograms(pd)

glyphs = segmentation.applyArrowGlyphs(pd, computeNormals=False)
vis.showPolyData(glyphs, 'glyphs', visible=False)

'''



