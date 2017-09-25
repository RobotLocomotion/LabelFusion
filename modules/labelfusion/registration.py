# system imports
import os
import subprocess
import numpy as np
import time
import yaml

# director imports
from director import transformUtils
from director import filterUtils
from director import ioUtils
from director import objectmodel as om
from director import segmentation
from director import visualization as vis
from director import vtkNumpy as vnp
from director import vtkAll as vtk
from director.debugVis import DebugData
from director.shallowCopy import shallowCopy
from director.fieldcontainer import FieldContainer

# labelfusion imports
from . import utils
from .objectalignmenttool import ObjectAlignmentTool


class GlobalRegistration(object):

    def __init__(self, view, cameraView, measurementPanel, affordanceManager,
                 logFolder=None,
                 firstFrameToWorldTransform=None):
        self.view = view
        self.cameraView = cameraView
        self.objectData = utils.loadObjectData()
        self.objectToWorldTransform = dict()
        self.measurementPanel = measurementPanel
        self.affordanceManager = affordanceManager
        self.logFolder = logFolder
        assert firstFrameToWorldTransform is not None
        self.firstFrameToWorldTransform = firstFrameToWorldTransform

        self.initializeFields()


    def initializeFields(self):
        self.visFolder = om.getOrCreateContainer('global registration')


        if self.logFolder is None:
            self.logFolder = "logs/scratch"

        self.pathDict = utils.getFilenames(self.logFolder)
        self.objectAlignmentResults = dict() # stores results of object alignment tool
        self.objectAlignmentTool = None

        # load the above table poly data if it exists
        self.aboveTablePolyData = None
        if os.path.isfile(self.pathDict['aboveTablePointcloud']):
            print "loading above table pointcloud"
            polyData = ioUtils.readPolyData(self.pathDict['aboveTablePointcloud'])
            self.aboveTablePolyData = filterUtils.transformPolyData(polyData, self.firstFrameToWorldTransform)
            vis.updatePolyData(self.aboveTablePolyData, 'above table pointcloud', parent=self.visFolder, colorByName='RGB')

        self.storedObjects = dict()
        self.loadStoredObjects()


    def loadStoredObjects(self):
        if not os.path.isfile(self.pathDict['registrationResult']):
            return

        stream = file(self.pathDict['registrationResult'])
        registrationResult = yaml.load(stream)

        for objName, data in registrationResult.iteritems():
            objectMeshFilename = data['filename']  # should be relative to getLabelFusionDataDir()
            if len(objectMeshFilename) == 0:
                objectMeshFilename = utils.getObjectMeshFilename(self.objectData, objName)
            else:
                objectMeshFilename = os.path.join(utils.getLabelFusionDataDir(), objectMeshFilename)

            objectToFirstFrame = transformUtils.transformFromPose(data['pose'][0], data['pose'][1])
            objectToWorld = transformUtils.concatenateTransforms([objectToFirstFrame, self.firstFrameToWorldTransform])

            polyData = ioUtils.readPolyData(objectMeshFilename)
            polyDataWorld = filterUtils.transformPolyData(polyData, objectToWorld)


            d = dict()
            d['transform'] = objectToWorld
            d['polyData'] = polyDataWorld
            self.storedObjects[objName] = d



    def fitObjectToPointcloud(self, objectName, pointCloud=None, downsampleObject=True,
                              objectPolyData=None, filename=None, visualize=True,
                              algorithm="GoICP"):

        if objectPolyData is None:
            if filename is None:
                filename = utils.getObjectMeshFilename(self.objectData, objectName)

            objectPolyData = ioUtils.readPolyData(filename)


        # downsample the object poly data
        objectPolyDataForAlgorithm = objectPolyData
        if downsampleObject:
            objectPolyDataForAlgorithm = segmentation.applyVoxelGrid(objectPolyData,
                                                         leafSize=0.002)

        if pointCloud is None:
            pointCloud = om.findObjectByName('reconstruction').polyData

        sceneToModelTransform = GlobalRegistration.runRegistration(algorithm, pointCloud, objectPolyDataForAlgorithm)
        objectToWorld = sceneToModelTransform.GetLinearInverse()
        self.objectToWorldTransform[objectName] = objectToWorld

        if visualize:
            alignedObj = vis.updatePolyData(objectPolyData, objectName + ' aligned')
            alignedObj.actor.SetUserTransform(objectToWorld)

        return objectToWorld


    def cropPointCloud(self, point=None, pointCloud=None, radius=0.3,
                       visualize=True):
        """
        Crop pointcloud using sphere around given point and radius
        :param point: defaults to point chosen using measurement panel
        :param pointCloud: defaults to 'reconstruction'
        :return: cropped point cloud, polyData
        """
        if point is None:
            if len(self.measurementPanel.pickPoints) == 0:
                print "you haven't selected any points using measurement panel"
                return

            point = self.measurementPanel.pickPoints[-1]

        if pointCloud is None:
            pointCloud = om.findObjectByName('reconstruction').polyData

        croppedPointCloud = segmentation.cropToSphere(pointCloud, point, radius=radius)
        if visualize:
            vis.updatePolyData(croppedPointCloud, 'cropped pointcloud')

        return croppedPointCloud

    def segmentTable(self, scenePolyData=None, searchRadius=0.3, visualize=True,
                     thickness=0.01, pointOnTable=None, pointAboveTable=None):
        """
        This requires two clicks using measurement panel. One on the table, one above the table on one of the objects. Call them point0, point1. Then we will attempt to fit a plane that passes through point0 with approximate normal point1 - point0
        :param scenePolyData:
        :param searchRadius:
        :return:
        """

        if scenePolyData is None:
            scenePolyData = om.findObjectByName('reconstruction').polyData


        if pointOnTable is None:
            assert (len(self.measurementPanel.pickPoints) >= 2)
            pointOnTable = self.measurementPanel.pickPoints[0]
            pointAboveTable = self.measurementPanel.pickPoints[1]


        expectedNormal= pointAboveTable - pointOnTable
        expectedNormal = expectedNormal/np.linalg.norm(expectedNormal)

        polyData, normal = segmentation.applyPlaneFit(scenePolyData, searchOrigin=pointOnTable, searchRadius=searchRadius, expectedNormal=expectedNormal)


        # get points above plane
        abovePolyData = filterUtils.thresholdPoints(polyData, 'dist_to_plane', [thickness / 2.0, np.inf])
        belowPolyData = filterUtils.thresholdPoints(polyData, 'dist_to_plane', [-np.inf, -thickness / 2.0])

        self.aboveTablePolyData = abovePolyData


        # some debugging visualization
        if visualize:
            vis.showPolyData(abovePolyData, 'above table segmentation', color=[0, 1, 0],
                             parent=self.visFolder)
            arrowLength = 0.3
            headRadius = 0.02
            d = DebugData()
            d.addArrow(pointOnTable, pointOnTable + arrowLength*expectedNormal,
                       headRadius=headRadius)
            vis.showPolyData(d.getPolyData(), 'expected normal', color=[1, 0, 0],
                             parent=self.visFolder)

            d = DebugData()
            d.addArrow(pointOnTable, pointOnTable + arrowLength * normal,
                       headRadius=headRadius)
            vis.showPolyData(d.getPolyData(), 'computed normal', color=[0, 1, 0],
                             parent=self.visFolder)


        returnData = dict()
        returnData['abovePolyData'] = abovePolyData
        returnData['polyData'] = polyData
        returnData['normal'] = normal
        returnData['pointOnTable'] = pointOnTable
        return returnData

    def saveAboveTablePolyData(self):
        aboveTablePolyDataRaw = filterUtils.transformPolyData(self.aboveTablePolyData, self.firstFrameToWorldTransform.GetLinearInverse())

        ioUtils.writePolyData(aboveTablePolyDataRaw, self.pathDict['aboveTablePointcloud'])

    def rotateReconstructionToStandardOrientation(self, pointCloud=None, savePoseToFile=True, filename=None):
        """
        Rotates the reconstruction to right side up and saves the transform to a file
        :param pointcloud:
        :return:
        """

        if pointCloud is None:
            pointCloud = om.findObjectByName('reconstruction').polyData

        returnData = self.segmentTable(scenePolyData=pointCloud, visualize=False)

        normal = returnData['normal']
        polyData = returnData['polyData']
        # get transform that rotates normal --> [0,0,1]
        origin = returnData['pointOnTable'] - 0.5 * normal
        pointCloudToWorldTransform = transformUtils.getTransformFromOriginAndNormal(origin, normal).GetLinearInverse()

        rotatedPolyData = filterUtils.transformPolyData(polyData, pointCloudToWorldTransform)

        parent = om.getOrCreateContainer('segmentation')
        vis.updatePolyData(rotatedPolyData, 'reconstruction', colorByName='RGB', parent=parent)

        if savePoseToFile:
            if filename is None:
                assert self.pathDict is not None
                filename = self.pathDict['transforms']

            (pos, quat) = transformUtils.poseFromTransform(pointCloudToWorldTransform)
            d = dict()
            d['firstFrameToWorld'] = [pos.tolist(), quat.tolist()]
            utils.saveDictToYaml(d, filename)

        return pointCloudToWorldTransform

    def rotateAndSegmentPointCloud(self):
        print "rotating and pointcloud"
        firstFrameToWorld = self.rotateReconstructionToStandardOrientation()
        self.firstFrameToWorldTransform = firstFrameToWorld

        pointOnTable = np.array(firstFrameToWorld.TransformPoint(self.measurementPanel.pickPoints[0]))
        pointAboveTable = np.array(firstFrameToWorld.TransformPoint(self.measurementPanel.pickPoints[1]))

        print "segmenting table"
        d = self.segmentTable(pointOnTable=pointOnTable, pointAboveTable=pointAboveTable,
                          visualize=False)

        vis.updatePolyData(d['abovePolyData'], 'above table segmentation', colorByName='RGB', parent=self.visFolder)


        print "saving segmentation"
        self.saveAboveTablePolyData()
        self.initializeFields()


    def launchObjectAlignment(self, objectName, useAboveTablePointcloud=True):
        """
        Launches the object alignment tool.
        :param objectName:
        :param useAboveTablePointcloud:
        :return:
        """

        if self.objectAlignmentTool is not None:
            self.objectAlignmentTool.picker.stop()
            self.objectAlignmentTool.scenePicker.stop()
            self.objectAlignmentTool.widget.close()


        pointCloud = self.aboveTablePolyData
        # pointCloud = om.findObjectByName('reconstruction').polyData
        objectPolyData = utils.getObjectPolyData(self.objectData, objectName)
        resultsDict = dict()
        self.objectAlignmentResults[objectName] = resultsDict
        parent = om.getOrCreateContainer('global registration')

        def onFinishAlignment():
            """
            this is a callback that objectAlignmentTool will call when it finishes
            :param d:
            :return:
            """
            resultsDict['modelToFirstFrameTransform'] = transformUtils.concatenateTransforms([resultsDict['modelToSceneTransform'], self.firstFrameToWorldTransform.GetLinearInverse()])


            modelToWorld = resultsDict['modelToSceneTransform']


            visObj = om.findObjectByName(objectName)
            om.removeFromObjectModel(visObj)
            pose = transformUtils.poseFromTransform(modelToWorld)
            utils.loadObjectMesh(self.affordanceManager, objectName,
                                     visName=objectName, pose=pose)
            print "cropping and running ICP"
            self.ICPWithCropBasedOnModel(objectName=objectName)


        self.objectAlignmentTool = ObjectAlignmentTool(self.cameraView, modelPolyData=objectPolyData, pointCloud=pointCloud, resultsDict=resultsDict,
                                                  callback=onFinishAlignment)

    @staticmethod
    def cropPointCloudToModelBoundingBox(pointCloud, objectPointCloud,
                                         scaleFactor=1.5):
        print "cropping pointcloud to box"
        # f = segmentation.makePolyDataFields(objectPointCloud)
        f = GlobalRegistrationUtils.getOrientedBoundingBox(objectPointCloud)


        croppedPointCloud = segmentation.cropToBox(pointCloud, f.frame,
                                                   scaleFactor*np.array(f.dims))
        return croppedPointCloud




    @staticmethod
    def cropPointCloudToModel(pointCloud, objectPointCloud, distanceThreshold=0.02,
                              visualize=True, applyEuclideanClustering=True):
        """
        Crops pointCloud to just the points withing distanceThreshold of
        objectPointCloud

        :param pointCloud:
        :param objectPointCloud:
        :param distanceThreshold:
        :return: cropped pointcloud
        """
        registration = GlobalRegistrationUtils
        pointCloud = GlobalRegistration.cropPointCloudToModelBoundingBox(pointCloud, objectPointCloud, scaleFactor=1.5)
        arrayName = 'distance_to_mesh'
        print "computing point to point distance"
        dists = registration.computePointToPointDistance(pointCloud, objectPointCloud)
        vnp.addNumpyToVtk(pointCloud, dists, arrayName)
        polyData = filterUtils.thresholdPoints(pointCloud, arrayName, [0.0, distanceThreshold])

        # this stuff may be unecessary
        if applyEuclideanClustering:
            # polyData = segmentation.applyVoxelGrid(polyData, leafSize=0.01)
            polyData = segmentation.applyEuclideanClustering(polyData, clusterTolerance=0.04)
            polyData = segmentation.thresholdPoints(polyData, 'cluster_labels', [1, 1])

        if visualize:
            parent = om.getOrCreateContainer('global registration')
            vis.updatePolyData(polyData, 'cropped pointcloud', color=[0,1,0],
                               parent=parent)

        return polyData

    def cropPointCloudUsingAlignedObject(self, objectName='oil_bottle', pointCloud=None):
        """
        Crops the aboveTablePolyData within a radius of the fitted model
        :param objectName:
        :return:
        """

        if pointCloud is None:
            pointCloud = self.aboveTablePolyData

        assert pointCloud is not None

        alignedModel = None
        if objectName in self.objectAlignmentResults:
            alignedModel = self.objectAlignmentResults[objectName]['alignedModel']

        else:
            assert objectName in self.storedObjects
            alignedModel = self.storedObjects[objectName]['polyData']


        croppedPointCloud = GlobalRegistration.cropPointCloudToModel(pointCloud, alignedModel, visualize=True)

        return croppedPointCloud


    def saveRegistrationResults(self, filename=None):
        registrationResultDict = dict()
        if os.path.isfile(self.pathDict['registrationResult']):
            registrationResultDict = utils.getDictFromYamlFilename(self.pathDict['registrationResult'])

        affordanceFolder = om.getOrCreateContainer('affordances')
        affordanceList = affordanceFolder.children()

        for affordance in affordanceList:
            objectName = affordance.getProperty('Name')
            modelToWorld = affordance.getChildFrame().transform
            modelToFirstFrame = transformUtils.concatenateTransforms([modelToWorld, self.firstFrameToWorldTransform.GetLinearInverse()])
            pose = transformUtils.poseFromTransform(modelToFirstFrame)
            poseAsList = [pose[0].tolist(), pose[1].tolist()]
            d = dict()
            meshFilename = affordance.getProperty('Filename')
            relPathToDataDir = os.path.relpath(meshFilename, utils.getLabelFusionDataDir())

            d['filename'] = relPathToDataDir
            d['pose'] = poseAsList
            registrationResultDict[objectName] = d

        if filename is None:
            filename = self.pathDict['registrationResult']

        utils.saveDictToYaml(registrationResultDict, filename)

    def ICPWithCropBasedOnModel(self, objectName='oil_bottle', scenePointCloud=None):
        if scenePointCloud is None:
            scenePointCloud = self.aboveTablePolyData

        croppedPointcloud = self.cropPointCloudUsingAlignedObject(objectName, pointCloud=scenePointCloud)

        self.testICP(objectName, scenePointCloud=croppedPointcloud)

    def testICP(self, objectName, scenePointCloud=None, applyVoxelGrid=True):
        print "running ICP"
        visObj = om.findObjectByName(objectName)
        if scenePointCloud is None:
            scenePointCloud = om.findObjectByName('cropped pointcloud').polyData
        modelPointcloud = filterUtils.transformPolyData(visObj.polyData, visObj.actor.GetUserTransform())

        if applyVoxelGrid:
            modelPointcloud = segmentation.applyVoxelGrid(modelPointcloud, leafSize=0.0005)

        sceneToModelTransform = segmentation.applyICP(scenePointCloud, modelPointcloud)

        modelToSceneTransform = sceneToModelTransform.GetLinearInverse()
        concatenatedTransform = transformUtils.concatenateTransforms([visObj.actor.GetUserTransform(), modelToSceneTransform])
        visObj.getChildFrame().copyFrame(concatenatedTransform)

        print "ICP finished"

    def testPhoneFit(self, useStoredPointcloud=True, algorithm="GoICP"):
        croppedPointCloud = self.cropPointCloud(radius=0.08)

        if useStoredPointcloud:
            filename = os.path.join(utils.getLabelFusionDataDir(),
                                    'sandbox/phone_crop_no_table.vtp')
            croppedPointCloud = ioUtils.readPolyData(filename)

        return self.fitObjectToPointcloud('phone', pointCloud=croppedPointCloud, algorithm=algorithm)


    def test(self, algorithm="GoICP"):
        """
        Runs a defaul registration test with a kuka arm mesh
        :param algorithm:
        :return:
        """

        assert algorithm in ["GoICP", "Super4PCS"]

        baseName = os.path.join(utils.getLabelFusionDataDir(),
                                'registration-output/robot-scene')
        pointCloudFile = os.path.join(baseName, 'robot_mesh.vtp')
        robotMeshFile = os.path.join(baseName, 'robot_mesh.vtp')
        robotMeshPointcloudFile = os.path.join(baseName, 'robot_mesh_pointcloud.vtp')

        pointCloud = ioUtils.readPolyData(pointCloudFile)
        robotMesh = ioUtils.readPolyData(robotMeshFile)
        robotMeshPointcloud = ioUtils.readPolyData(robotMeshPointcloudFile)

        pointCloud = segmentation.applyVoxelGrid(pointCloud, leafSize=0.01)

        # rotate the scene 90 degrees
        sceneTransform = transformUtils.frameFromPositionAndRPY([0, 0, 0], [0, 0, 90])
        # sceneTransform = transformUtils.frameFromPositionAndRPY([-1, 0, 0], [0, 0, 0])
        pointCloud = filterUtils.transformPolyData(pointCloud, sceneTransform)

        print pointCloud.GetNumberOfPoints()
        print robotMeshPointcloud.GetNumberOfPoints()

        sceneName = 'scene pointcloud'
        modelName = 'model pointcloud'

        vis.showPolyData(robotMeshPointcloud, modelName)
        vis.showPolyData(pointCloud, sceneName)

        self.view.resetCamera()
        self.view.forceRender()

        sceneToModelTransform = GlobalRegistration.runRegistration(algorithm, pointCloud, robotMeshPointcloud)

        modelToSceneTransform = sceneToModelTransform.GetLinearInverse()
        GlobalRegistration.showAlignedPointcloud(robotMeshPointcloud, modelToSceneTransform, modelName + " aligned", color=[1, 0, 0])



    def testSuper4PCS(self):
        """
        Test the Super4PCS algorithm on some default data
        :return:
        """
        self.test(algorithm="Super4PCS")


    def testGoICP(self):
        """
        Test the Go-ICP algorithm on some default data
        :return:
        """
        self.test(algorithm="GoICP")

    @staticmethod
    def showAlignedPointcloud(polydata, transform, name, **kwargs):
        alignedPointcloud = filterUtils.transformPolyData(polydata, transform)
        vis.updatePolyData(alignedPointcloud, name, **kwargs)

    @staticmethod
    def runRegistration(algorithm, scenePointCloud, modelPointCloud,
                        visualize=True, **kwargs):
        assert algorithm in ["GoICP", "Super4PCS"]
        if (algorithm == "GoICP"):
            sceneToModelTransform = GoICP.run(scenePointCloud, modelPointCloud, **kwargs)
        elif algorithm == "Super4PCS":
            sceneToModelTransform = Super4PCS.run(scenePointCloud, modelPointCloud,
                                                  **kwargs)


        if visualize:
            alignedModelPointCloud = filterUtils.transformPolyData(modelPointCloud,
                                                                   sceneToModelTransform.GetLinearInverse())
            parent = om.getOrCreateContainer('registration')
            vis.updatePolyData(scenePointCloud, 'scene pointcloud', parent=parent)
            vis.updatePolyData(alignedModelPointCloud, 'aligned model pointcloud',
                               parent=parent, color=[1,0,0])

        return sceneToModelTransform




class GlobalRegistrationUtils(object):
    """
    A collection of useful utilities for global registration
    """

    @staticmethod
    def removeOriginPoints(polyData):
        """
        openni2-lcm driver publishes 0.0 depth for points with invalid range
        :param polyData:
        :return:
        """
        points = vnp.getNumpyFromVtk(polyData, 'Points')
        labels = np.array(np.sum(points, axis=1) == 0.0, dtype=int)
        vnp.addNumpyToVtk(polyData, labels, 'is_origin_point')
        return filterUtils.thresholdPoints(polyData, 'is_origin_point', [0.0, 0.0])

    @staticmethod
    def rescalePolyData(polyDataList):
        pointList = [vnp.getNumpyFromVtk(polyData, 'Points') for polyData in polyDataList]
        # scaleFactor = np.max([np.max(np.abs(points)) for points in pointList])
        scaleFactor = np.max([np.max(np.linalg.norm(points, axis=1)) for points in pointList])

        for points in pointList:
            points /= np.max(scaleFactor)

        return scaleFactor

    @staticmethod
    def shiftPointsToOrigin(polyData, copy=True, shuffle=True):
        points = None
        if copy:
            points = vnp.getNumpyFromVtk(polyData, 'Points').copy()
        else:
            points = vnp.getNumpyFromVtk(polyData, 'Points')

        if shuffle:
            np.random.shuffle(points)

        points -= np.average(points, axis=0)
        return vnp.numpyToPolyData(points, createVertexCells=True)

    @staticmethod
    def writePointsFile(polyData, filename):
        points = vnp.getNumpyFromVtk(polyData, 'Points')
        f = open(filename, 'w')
        f.write('%d\n' % len(points))
        for p in points:
            f.write('%f %f %f\n' % (p[0], p[1], p[2]))
        # np.savetxt(f, points)
        f.close()

    @staticmethod
    def getSandboxDir():
        return os.path.join(utils.getLabelFusionBaseDir(), 'sandbox')

    @staticmethod
    def removeFile(filename):
        if os.path.isfile(filename):
            os.remove(filename)

    @staticmethod
    def getSandboxRelativePath(filename):
        baseName = GlobalRegistrationUtils.getSandboxDir()
        return os.path.join(baseName, filename)

    @staticmethod
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

    @staticmethod
    def computePointToPointDistance(pointsPolyData, searchPolyData):

        cl = vtk.vtkPointLocator()
        cl.SetDataSet(searchPolyData)
        cl.BuildLocator()

        points = vnp.getNumpyFromVtk(pointsPolyData, 'Points')
        searchPoints = vnp.getNumpyFromVtk(searchPolyData, 'Points')
        closestPoints = np.zeros((len(points), 3))

        for i in xrange(len(points)):
            ptId = cl.FindClosestPoint(points[i])
            closestPoints[i] = searchPoints[ptId]

        return np.linalg.norm(closestPoints - points, axis=1)

    @staticmethod
    def getOrientedBoundingBox(pd):
        mesh = pd
        origin, edges, wireframe = segmentation.getOrientedBoundingBox(mesh)

        edgeLengths = np.array([np.linalg.norm(edge) for edge in edges])
        axes = [edge / np.linalg.norm(edge) for edge in edges]

        # find axis nearest to the +/- up vector
        upVector = [0, 0, 1]
        dotProducts = [np.abs(np.dot(axe, upVector)) for axe in axes]
        zAxisIndex = np.argmax(dotProducts)

        # re-index axes and edge lengths so that the found axis is the z axis
        axesInds = [(zAxisIndex + 1) % 3, (zAxisIndex + 2) % 3, zAxisIndex]
        axes = [axes[i] for i in axesInds]
        edgeLengths = [edgeLengths[i] for i in axesInds]

        # flip if necessary so that z axis points toward up
        if np.dot(axes[2], upVector) < 0:
            axes[1] = -axes[1]
            axes[2] = -axes[2]

        boxCenter = segmentation.computeCentroid(wireframe)

        t = transformUtils.getTransformFromAxes(axes[0], axes[1], axes[2])
        t.PostMultiply()
        t.Translate(boxCenter)

        pd = filterUtils.transformPolyData(pd, t.GetLinearInverse())
        wireframe = filterUtils.transformPolyData(wireframe, t.GetLinearInverse())

        return FieldContainer(points=pd, box=wireframe, frame=t, dims=edgeLengths, axes=axes)

    @staticmethod
    def segmentTable(scenePolyData=None, searchRadius=0.3, visualize=True,
                     thickness=0.01, pointOnTable=None, pointAboveTable=None,
                     computeAboveTablePolyData=False):
        """
        This requires two clicks using measurement panel. One on the table, one above the table on one of the objects. Call them point0, point1. Then we will attempt to fit a plane that passes through point0 with approximate normal point1 - point0
        :param scenePolyData:
        :param searchRadius:
        :return:
        """

        if scenePolyData is None:
            scenePolyData = om.findObjectByName('reconstruction').polyData


        assert scenePolyData is not None
        assert pointOnTable is not None
        assert pointAboveTable is not None


        expectedNormal= pointAboveTable - pointOnTable
        expectedNormal = expectedNormal/np.linalg.norm(expectedNormal)

        polyData, normal = segmentation.applyPlaneFit(scenePolyData, searchOrigin=pointOnTable, searchRadius=searchRadius, expectedNormal=expectedNormal)


        # get points above plane
        abovePolyData = None
        belowPolyData = None
        if computeAboveTablePolyData:
            abovePolyData = filterUtils.thresholdPoints(polyData, 'dist_to_plane', [thickness / 2.0, np.inf])
            belowPolyData = filterUtils.thresholdPoints(polyData, 'dist_to_plane', [-np.inf, -thickness / 2.0])


        # some debugging visualization
        if visualize:
            visFolder = om.getOrCreateContainer('debug')

            if abovePolyData is not None:
                vis.showPolyData(abovePolyData, 'above table segmentation', color=[0, 1, 0],
                             parent=visFolder)
            arrowLength = 0.3
            headRadius = 0.02
            d = DebugData()
            visFolder = om.getOrCreateContainer('debug')
            d.addArrow(pointOnTable, pointOnTable + arrowLength*expectedNormal,
                       headRadius=headRadius)
            vis.showPolyData(d.getPolyData(), 'expected normal', color=[1, 0, 0],
                             parent=visFolder)

            d = DebugData()
            d.addArrow(pointOnTable, pointOnTable + arrowLength * normal,
                       headRadius=headRadius)
            vis.showPolyData(d.getPolyData(), 'computed normal', color=[0, 1, 0],
                             parent=visFolder)


        returnData = dict()
        returnData['abovePolyData'] = abovePolyData
        returnData['polyData'] = polyData
        returnData['normal'] = normal
        returnData['pointOnTable'] = pointOnTable
        return returnData



class Super4PCS(object):
    """
    A wrapper to the Super PCS 4 algorithm
    """

    @staticmethod
    def run(scenePointCloud, modelPointCloud, overlap=0.9, distance=0.02, timeout=1000, numSamples=200):
        """

        :param scenePointCloud:
        :param modelPointCloud:
        :return: transform from scenePointCloud --> modelPointCloud. It is a vtkTransform
        """
        baseName = GlobalRegistrationUtils.getSandboxDir()
        modelFile = os.path.join(baseName, 'model_data_for_pcs4.ply')
        sceneFile = os.path.join(baseName, 'scene_data_for_pcs4.ply')

        ioUtils.writePolyData(modelPointCloud, modelFile)
        ioUtils.writePolyData(scenePointCloud, sceneFile)

        super4PCSBaseDir = utils.getSuper4PCSBaseDir()
        registrationBin = os.path.join(super4PCSBaseDir, 'build/Super4PCS')
        outputFile = os.path.join(utils.getLabelFusionBaseDir(),
                                  'sandbox/pcs4_mat_output.txt')

        print "number of scene points = ", scenePointCloud.GetNumberOfPoints()
        print "number of model points = ", modelPointCloud.GetNumberOfPoints()

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

        startTime = time.time()
        subprocess.check_call(registrationArgs)
        elapsedTime = time.time() - startTime
        print "SuperPCS4 took " + str(elapsedTime) + " seconds"

        print 'done.'
        transform = Super4PCS.getTransformFromFile(outputFile)
        return transform

    @staticmethod
    def getTransformFromFile(outputFile):
        assert os.path.isfile(outputFile)
        data = open(outputFile).readlines()
        T = np.array([np.fromstring(l, sep=' ') for l in data[2:6]])
        transform = transformUtils.getTransformFromNumpy(T)
        return transform



class GoICP(object):
    """
    A wrapper to the Go-ICP algorithm.
    """
    @staticmethod
    def run(scenePointCloudOriginal, modelPointCloudOriginal, numDownsampledPoints=1000):

        # make deep copies of pointclouds so we don't touch original data
        scenePointCloud = vtk.vtkPolyData()
        scenePointCloud.DeepCopy(scenePointCloudOriginal)
        modelPointCloud = vtk.vtkPolyData()
        modelPointCloud.DeepCopy(modelPointCloudOriginal)


        # transform the data a bit
        registration = GlobalRegistrationUtils
        # use this if your point cloud contains invalid points with 0.0 range
        scenePointCloud = registration.removeOriginPoints(scenePointCloud)
        scenePointCloud = registration.shiftPointsToOrigin(scenePointCloud)
        modelPointCloud = registration.shiftPointsToOrigin(modelPointCloud)
        scaleFactor = registration.rescalePolyData([scenePointCloud, modelPointCloud])

        numDownsampledPoints = min(numDownsampledPoints, scenePointCloud.GetNumberOfPoints)

        print "scaleFactor = ", scaleFactor
        print "number of scene points = ", scenePointCloud.GetNumberOfPoints()
        print "downsampled number of scene points = ", numDownsampledPoints
        print "number of model points = ", modelPointCloud.GetNumberOfPoints()

        # files where temporary output will be stored
        baseName = registration.getSandboxDir()
        modelPointCloudFile = os.path.join(baseName, 'model_data.txt')
        scenePointCloudFile = os.path.join(baseName, 'scene_data.txt')
        outputFile = os.path.join(baseName, 'goicp_output.txt')


        # write the polyData to a file so that
        registration.writePointsFile(modelPointCloud, modelPointCloudFile)
        registration.writePointsFile(scenePointCloud, scenePointCloudFile)

        goICPBaseDir = utils.getGoICPBaseDir()
        # goICPConfigFile = os.path.join(goICPBaseDir, 'demo/config.txt')
        goICPConfigFile = os.path.join(utils.getLabelFusionBaseDir(),
                                       'config/go_icp_config.txt')
        goICPBin = os.path.join(goICPBaseDir, 'build/GoICP')


        goICPArgs = [
            goICPBin,
            modelPointCloudFile,
            scenePointCloudFile,
            str(numDownsampledPoints),
            goICPConfigFile,
            outputFile]

        goICPArgs = ' '.join(goICPArgs).split()

        if os.path.isfile(outputFile):
            print 'removing', outputFile
            os.remove(outputFile)

        print 'calling goicp...'
        print
        print ' '.join(goICPArgs)

        startTime = time.time()
        subprocess.check_call(goICPArgs)
        elapsedTime = time.time() - startTime
        print "GoICP took " + str(elapsedTime) + " seconds"
        data = open(outputFile).readlines()
        print data

        T = np.eye(4)
        T[:3, :3] = np.array([np.fromstring(l, sep=' ') for l in [data[1], data[2], data[3]]])
        T[:3, 3] = [float(x) for x in [data[4], data[5], data[6]]]

        print T

        sceneToModelTransform = transformUtils.getTransformFromNumpy(T)


        if True:
            parent = om.getOrCreateContainer('Go-ICP')
            transformedPointCloud = filterUtils.transformPolyData(scenePointCloud, transformUtils.getTransformFromNumpy(T))

            vis.showPolyData(modelPointCloud, 'model pointcloud ', color=[0,1,0],
                             parent=parent)
            vis.showPolyData(transformedPointCloud, 'aligned model pointcloud', color=[1,0,0], parent=parent)
            vis.showPolyData(scenePointCloud, 'scene pointcloud goicp', color=[0,1,1],
                             parent=parent)

        return sceneToModelTransform



class FastGlobalRegistration(object):

    @staticmethod
    def run(scenePointCloud, modelPointCloud):
        registration = GlobalRegistrationUtils
        registration.removeFile('model_features.bin')
        registration.removeFile('scene_features.bin')
        registration.removeFile('features.bin')

        FGR = FastGlobalRegistration
        FGR.computeFeatures(scenePointCloud, 'scene')
        FGR.computeFeatures(modelPointCloud, 'model')

        print 'run registration...'
        FGRBaseDir = utils.getGRBaseDir()
        FGRBin = os.path.join(FGRBaseDir, 'build/FastGlobalRegistration/FastGlobalRegistration')

        goICPArgs = [
            goICPBin,
            modelPointCloudFile,
            scenePointCloudFile,
            str(numDownsampledPoints),
            goICPConfigFile,
            outputFile]

        subprocess.check_call(['bash', 'runFGR.sh'])

        showTransformedData(sceneName)

        print 'done.'

    @staticmethod
    def computeFeatures(polyData, name):
        pd = segmentation.applyVoxelGrid(pd, leafSize=0.005)
        print 'compute normals...'
        pd = segmentation.normalEstimation(pd, searchRadius=0.05, useVoxelGrid=False, voxelGridLeafSize=0.01)

        print 'compute features...'
        FastGlobalRegistration.computePointFeatureHistograms(pd, searchRadius=0.10)
        newName = name + '_features.bin'
        FastGlobalRegistration.renameFeaturesFile(name)

    @staticmethod
    def computePointFeatureHistograms(polyData, searchRadius=0.10):
        f = vtk.vtkPCLFPFHEstimation()
        f.SetInput(polyData)
        f.SetSearchRadius(searchRadius)
        f.Update()
        return shallowCopy(f.GetOutput())

    @staticmethod
    def renameFeaturesFile(newName):
        assert os.path.isfile('features.bin')
        newName = GlobalRegistrationUtils.getSandboxRelativePath(newName)
        os.rename('features.bin', newName)
