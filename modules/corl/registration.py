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

#corl imports
import utils as CorlUtils

class GlobalRegistration(object):

    def __init__(self, view, measurementPanel, logFolder=None):
        self.view = view
        self.objectToWorldTransform = dict()
        self.measurementPanel = measurementPanel
        self.logFolder = logFolder
        self.initializeFields()

    def initializeFields(self):
        self.aboveTablePolyData = None

        if self.logFolder is None:
            self.logFolder = "logs/scratch"

        self.pathDict = CorlUtils.getFilenames(self.logFolder)

    def fitObjectToPointcloud(self, objectName, pointCloud=None, downsampleObject=True,
                              objectPolyData=None, filename=None, visualize=True,
                              algorithm="GoICP"):

        if objectPolyData is None:
            if filename is None:
                filename = CorlUtils.getObjectMeshFilename(objectName)

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

    def segmentTable(self, scenePolyData=None, searchRadius=0.3, visualize=True):
        """
        This requires two clicks using measurement panel. One on the table, one above the table on one of the objects. Call them point0, point1. Then we will attempt to fit a plane that passes through point0 with approximate normal point1 - point0
        :param scenePolyData:
        :param searchRadius:
        :return:
        """

        if scenePolyData is None:
            scenePolyData = om.findObjectByName('reconstruction').polyData

        assert (len(self.measurementPanel.pickPoints) >= 2)
        pointOnTable = self.measurementPanel.pickPoints[0]
        pointAboveTable = self.measurementPanel.pickPoints[1]
        expectedNormal= pointAboveTable - pointOnTable
        expectedNormal = expectedNormal/np.linalg.norm(expectedNormal)

        polyData, normal = segmentation.applyPlaneFit(scenePolyData, searchOrigin=pointOnTable, searchRadius=searchRadius, expectedNormal=expectedNormal)


        # get points above plane
        thickness = 0.02
        abovePolyData = filterUtils.thresholdPoints(polyData, 'dist_to_plane', [thickness / 2.0, np.inf])
        belowPolyData = filterUtils.thresholdPoints(polyData, 'dist_to_plane', [-np.inf, -thickness / 2.0])

        self.aboveTablePolyData = abovePolyData

        if visualize:
            parent = om.getOrCreateContainer('global reconstruction')
            vis.showPolyData(abovePolyData, 'above table segmentation', color=[0, 1, 0],
                             parent=parent)

            arrowLength = 0.3
            headRadius = 0.02
            d = DebugData()
            d.addArrow(pointOnTable, pointOnTable + arrowLength*expectedNormal,
                       headRadius=headRadius)
            vis.showPolyData(d.getPolyData(), 'expected normal', color=[1, 0, 0],
                             parent=parent)

            d = DebugData()
            d.addArrow(pointOnTable, pointOnTable + arrowLength * normal,
                       headRadius=headRadius)
            vis.showPolyData(d.getPolyData(), 'computed normal', color=[0, 1, 0],
                             parent=parent)


        returnData = dict()
        returnData['polyData'] = polyData
        returnData['normal'] = normal
        returnData['pointOnTable'] = pointOnTable
        return returnData

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
        vis.updatePolyData(rotatedPolyData, 'reconstruction rotated', colorByName='RGB', parent=parent)

        if savePoseToFile:
            if filename is None:
                assert self.pathDict is not None
                filename = self.pathDict['transforms']

            pose = transformUtils.poseFromTransform(pointCloudToWorldTransform)
            d = dict()
            d['pointCloudToWorld'] = pose
            CorlUtils.saveDictToYaml(d, filename)

        return pointCloudToWorldTransform

    def testPhoneFit(self, useStoredPointcloud=True, algorithm="GoICP"):
        croppedPointCloud = self.cropPointCloud(radius=0.08)

        if useStoredPointcloud:
            filename = os.path.join(CorlUtils.getCorlDataDir(),
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

        baseName = os.path.join(CorlUtils.getCorlDataDir(),
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
        return os.path.join(CorlUtils.getCorlBaseDir(), 'sandbox')


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

        super4PCSBaseDir = CorlUtils.getSuper4PCSBaseDir()
        registrationBin = os.path.join(super4PCSBaseDir, 'build/Super4PCS')
        outputFile = os.path.join(CorlUtils.getCorlBaseDir(),
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
        GRUtils = GlobalRegistrationUtils
        # use this if your point cloud contains invalid points with 0.0 range
        scenePointCloud = GRUtils.removeOriginPoints(scenePointCloud)
        scenePointCloud = GRUtils.shiftPointsToOrigin(scenePointCloud)
        modelPointCloud = GRUtils.shiftPointsToOrigin(modelPointCloud)
        scaleFactor = GRUtils.rescalePolyData([scenePointCloud, modelPointCloud])

        numDownsampledPoints = min(numDownsampledPoints, scenePointCloud.GetNumberOfPoints)

        print "scaleFactor = ", scaleFactor
        print "number of scene points = ", scenePointCloud.GetNumberOfPoints()
        print "downsampled number of scene points = ", numDownsampledPoints
        print "number of model points = ", modelPointCloud.GetNumberOfPoints()

        # files where temporary output will be stored
        baseName = GRUtils.getSandboxDir()
        modelPointCloudFile = os.path.join(baseName, 'model_data.txt')
        scenePointCloudFile = os.path.join(baseName, 'scene_data.txt')
        outputFile = os.path.join(baseName, 'goicp_output.txt')


        # write the polyData to a file so that
        GRUtils.writePointsFile(modelPointCloud, modelPointCloudFile)
        GRUtils.writePointsFile(scenePointCloud, scenePointCloudFile)

        goICPBaseDir = CorlUtils.getGoICPBaseDir()
        # goICPConfigFile = os.path.join(goICPBaseDir, 'demo/config.txt')
        goICPConfigFile = os.path.join(CorlUtils.getCorlBaseDir(),
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



