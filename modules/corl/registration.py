# system imports
import os
import subprocess
import numpy as np

# director imports
from director import transformUtils
from director import filterUtils
from director import ioUtils
from director import objectmodel as om
from director import segmentation
from director import visualization as vis

#corl imports
import utils as CorlUtils

class GlobalRegistration(object):

    def __init__(self, view):
        self.view = view
        self.objectToWorldTransform = dict()

    def fitObjectToPointcloud(self, objectName, pointCloud=None,
                              objectPolyData=None, filename=None):

        if objectPolyData is None:
            if filename is None:
                filename = CorlUtils.getObjectMeshFilename(objectName)

            objectPolyData = ioUtils.readPolyData(filename)

        if pointCloud is None:
            pointCloud = om.findObjectByName('reconstruction').polyData

        sceneToModelTransform = SuperPCS4.run(pointCloud, objectPolyData)
        objectToWorld = sceneToModelTransform.GetLinearInverse()
        self.objectToWorldTransform[objectName] = objectToWorld
        return objectToWorld


    def testSuperPCS4(self):
        """
        Test the SuperPCS4 algorithm on some default data
        :return:
        """
        baseName = os.path.join(CorlUtils.getCorlDataDir(),
                                'registration-output/robot-scene')
        pointCloudFile = os.path.join(baseName, 'robot_mesh.vtp')
        robotMeshFile = os.path.join(baseName, 'robot_mesh.vtp')
        robotMeshPointcloudFile = os.path.join(baseName, 'robot_mesh_pointcloud.vtp')

        pointCloud = ioUtils.readPolyData(pointCloudFile)
        robotMesh = ioUtils.readPolyData(robotMeshFile)
        robotMeshPointcloud = ioUtils.readPolyData(robotMeshPointcloudFile)

        # PCS4 algorithm performs very differently if you remove the origin point
        # pointCloud = removeOriginPoints(pointCloud)


        pointCloud = segmentation.applyVoxelGrid(pointCloud, leafSize=0.01)

        sceneTransform = transformUtils.frameFromPositionAndRPY([0, 0, 0], [0, 0, 90])
        pointCloud = filterUtils.transformPolyData(pointCloud, sceneTransform)

        # robotMeshPointcloud = shuffleAndShiftPoints(robotMeshPointcloud)
        # pointCloud = shuffleAndShiftPoints(pointCloud)


        print pointCloud.GetNumberOfPoints()
        print robotMeshPointcloud.GetNumberOfPoints()

        sceneName = 'scene pointcloud'
        modelName = 'model pointcloud'

        vis.showPolyData(robotMeshPointcloud, modelName)
        vis.showPolyData(pointCloud, sceneName)

        self.view.resetCamera()
        self.view.forceRender()

        sceneToModelTransform = SuperPCS4.run(pointCloud, robotMeshPointcloud)
        GlobalRegistration.showAlignedPointcloud(pointCloud, sceneToModelTransform, sceneName + " aligned")

    @staticmethod
    def showAlignedPointcloud(polydata, transform, name):
        alignedPointcloud = filterUtils.transformPolyData(polydata, transform)
        vis.showPolyData(alignedPointcloud, name)


class SuperPCS4(object):

    @staticmethod
    def run(scenePointCloud, modelPointCloud):
        """

        :param scenePointCloud:
        :param modelPointCloud:
        :return: transform from scenePointCloud --> modelPointCloud. It is a vtkTransform
        """
        baseName = os.path.join(CorlUtils.getCorlBaseDir(),
                                'sandbox')
        modelFile = os.path.join(baseName, 'model_data_for_pcs4.ply')
        sceneFile = os.path.join(baseName, 'scene_data_for_pcs4.ply')

        ioUtils.writePolyData(modelPointCloud, modelFile)
        ioUtils.writePolyData(scenePointCloud, sceneFile)

        super4PCSBaseDir = CorlUtils.getSuper4PCSBaseDir()
        registrationBin = os.path.join(super4PCSBaseDir, 'build/Super4PCS')
        outputFile = os.path.join(CorlUtils.getCorlBaseDir(),
                                  'sandbox/pcs4_mat_output.txt')
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
        transform = SuperPCS4.getTransformFromFile(outputFile)
        return transform

    @staticmethod
    def getTransformFromFile(outputFile):
        assert os.path.isfile(outputFile)
        data = open(outputFile).readlines()
        T = np.array([np.fromstring(l, sep=' ') for l in data[2:6]])
        transform = transformUtils.getTransformFromNumpy(T)
        return transform

