import os
import numpy as np
import yaml
from director import visualization as vis
from director import objectmodel as om
from director import transformUtils
from director import ioUtils
from director import filterUtils
from director import vtkAll as vtk
from director.debugVis import DebugData
from director import segmentation
from director import lcmUtils
from director import lcmframe

from corl import utils as CorlUtils
from corl.cameraposes import CameraPoses
from corl.registration import GlobalRegistrationUtils as GRUtils
from corl.camerafrustumvisualizer import CameraFrustumVisualizer


class DataCollectionHelper(object):

    def __init__(self, robotSystem, openniDepthPointCloud):
        self.robotSystem = robotSystem
        self.openniDepthPointCloud = openniDepthPointCloud

        self.loadData()

    def loadData(self):
        logFolder = 'logs_test/moving-camera'
        self.pathDict = CorlUtils.getFilenames(logFolder)
        self.cameraPoses = CameraPoses(self.pathDict['cameraPoses'])


        # load the elastic fusion reconstruction if we already know where to
        # put it
        self.savedTransformFilename = os.path.join(CorlUtils.getCorlDataDir(), 'sandbox', 'reconstruction_robot_frame.yaml')
        if os.path.exists(self.savedTransformFilename):
            firstFrameToWorld = CorlUtils.getFirstFrameToWorldTransform(self.savedTransformFilename)
            CorlUtils.loadElasticFusionReconstruction(self.pathDict['reconstruction'],
                                                      transform=firstFrameToWorld)


    def loadReconstructedPointCloud(self):
        utime = self.openniDepthPointCloud.lastUtime
        cameraToFirstFrame = self.cameraPoses.getCameraPoseAtUTime(utime)
        cameraToWorld = om.findObjectByName('camera frame').transform
        firstFrameToCamera = cameraToFirstFrame.GetLinearInverse()
        firstFrameToWorld = transformUtils.concatenateTransforms([firstFrameToCamera, cameraToWorld])

        self.firstFrameToWorld = firstFrameToWorld
        CorlUtils.loadElasticFusionReconstruction(self.pathDict['reconstruction'],
                                                  transform=firstFrameToWorld)

    def saveTransform(self):
        (pos, quat) = transformUtils.poseFromTransform(self.firstFrameToWorld)
        d = dict()
        d['firstFrameToWorld'] = [pos.tolist(), quat.tolist()]
        CorlUtils.saveDictToYaml(d, self.savedTransformFilename)


class DataCollection(object):

    def __init__(self, robotSystem, openniDepthPointCloud, measurementPanel,
                 imageManager):
        self.robotSystem = robotSystem
        self.openniDepthPointCloud = openniDepthPointCloud
        self.measurementPanel = measurementPanel
        self.imageManager = imageManager
        self.visFolder = om.getOrCreateContainer('data collection')
        self.cameraName = 'OPENNI_FRAME_LEFT'
        self.savedTransformFilename = os.path.join(CorlUtils.getCorlDataDir(), 'sandbox',
                                                   'reconstruction_robot_frame.yaml')
        self.loadSavedData()

    def loadSavedData(self):
        d = CorlUtils.getDictFromYamlFilename(self.savedTransformFilename)
        if 'table frame' not in d:
            return
        (pos, quat) = d['table frame']
        t = transformUtils.transformFromPose(pos, quat)
        self.tableFrame = vis.updateFrame(t, 'table frame', scale=0.15)

    def spawnTableFrame(self):
        pointOnCloseTableEdge = self.measurementPanel.pickPoints[0]
        pointOnTable = self.measurementPanel.pickPoints[1]
        pointAboveTable = self.measurementPanel.pickPoints[2]
        scenePolyData = self.openniDepthPointCloud.polyData
        d = GRUtils.segmentTable(scenePolyData=scenePolyData, searchRadius=0.3, visualize=False, thickness=0.01, pointOnTable=pointOnTable, pointAboveTable=pointAboveTable)


        origin = d['pointOnTable']
        normal = d['normal']


        yaxis = -normal
        zaxis = pointOnTable - pointOnCloseTableEdge
        xaxis = np.cross(yaxis, zaxis)
        # frame = transformUtils.getTransformFromOriginAndNormal(origin, normal)
        frame = transformUtils.getTransformFromAxesAndOrigin(xaxis, yaxis, zaxis, origin)
        self.tableFrame = vis.updateFrame(frame, 'table frame', parent=self.visFolder, scale=0.15)


    def testCameraFrustrum(self):
        frame = om.findObjectByName('camera frame')
        self.cameraFrustumVisualizer = CameraFrustumVisualizer(self.imageManager,
                                                               self.cameraName,
                                                               frame)

    def makeTestFrame(self, rotateX=-40, rotateY=0, translateZ=-0.8):
        t = transformUtils.copyFrame(self.tableFrame.transform)
        t.PreMultiply()
        t.RotateX(rotateX)
        t.RotateY(rotateY)
        t.Translate((0,0,translateZ))

        name = 'frustum test'
        if om.findObjectByName(name) is None:
            frame = vis.updateFrame(t, 'test', scale=0.15)
            cameraFrustum = CameraFrustumVisualizer(self.imageManager, self.cameraName, frame)
            cameraFrustum.visObj.setProperty('Visible', True)
        else:
            frame = vis.updateFrame(t, 'test', scale=0.15)


    def saveTableFrame(self):
        d = CorlUtils.getDictFromYamlFilename(self.savedTransformFilename)
        (pos, quat) = transformUtils.poseFromTransform(self.tableFrame.transform)
        d['table frame'] = [pos.tolist(), quat.tolist()]
        CorlUtils.saveDictToYaml(d, self.savedTransformFilename)

