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

    def spawnTableFrame(self):
        pointOnTable = self.measurementPanel.pickPoints[0]
        pointAboveTable = self.measurementPanel.pickPoints[1]
        scenePolyData = self.openniDepthPointCloud.polyData
        d = GRUtils.segmentTable(scenePolyData=scenePolyData, searchRadius=0.3, visualize=False, thickness=0.01, pointOnTable=pointOnTable, pointAboveTable=pointAboveTable)


        origin = d['pointOnTable']
        normal = d['normal']
        frame = transformUtils.getTransformFromOriginAndNormal(origin, normal)
        self.tableFrame = vis.showFrame(frame, 'table frame', parent=self.visFolder, scale=0.1)


    def testCameraFrustrum(self):
        frame = om.findObjectByName('camera frame')
        self.cameraFrustumVisualizer = CameraFrustumVisualizer(self.imageManager,
                                                               self.cameraName,
                                                               frame)

class CameraFrustumVisualizer(object):

    def __init__(self, imageManager, cameraName, frame,
                 visFolder=None, name=None):
        self.cameraName = cameraName
        self.imageManager = imageManager
        self.rayLength = 2.0
        self.frame = frame

        if visFolder is None:
            self.visFolder = om.getOrCreateContainer('camera frustrum')

        if name is None:
            self.name = self.frame.getProperty('Name') + ' camera frustrum'

        self.frame.connectFrameModified(self.update)
        self.update(self.frame)

    def getCameraFrustumRays(self, cameraToLocal):
        '''
        Returns (cameraPositions, rays)
        cameraPosition is in world frame.
        rays are four unit length vectors in world frame that point in the
        direction of the camera frustum edges
        '''

        cameraPos = np.array(cameraToLocal.GetPosition())

        camRays = []
        rays = np.array(self.imageManager.queue.getCameraFrustumBounds(self.cameraName))
        for i in xrange(4):
            ray = np.array(cameraToLocal.TransformVector(rays[i*3:i*3+3]))
            ray /= np.linalg.norm(ray)
            camRays.append(ray)

        return cameraPos, camRays

    def getCameraFrustumGeometry(self, rayLength, cameraToLocal):

        camPos, rays = self.getCameraFrustumRays(cameraToLocal)

        rays = [rayLength*r for r in rays]

        d = DebugData()
        d.addLine(camPos, camPos+rays[0])
        d.addLine(camPos, camPos+rays[1])
        d.addLine(camPos, camPos+rays[2])
        d.addLine(camPos, camPos+rays[3])
        d.addLine(camPos+rays[0], camPos+rays[1])
        d.addLine(camPos+rays[1], camPos+rays[2])
        d.addLine(camPos+rays[2], camPos+rays[3])
        d.addLine(camPos+rays[3], camPos+rays[0])
        return d.getPolyData()

    def update(self, frame):
        obj = om.findObjectByName(self.name, parent=self.visFolder)
        frameToLocal = self.frame.transform

        if obj and not obj.getProperty('Visible'):
            return

        cameraFrustrumGeometry = self.getCameraFrustumGeometry(self.rayLength, frameToLocal)
        vis.updatePolyData(cameraFrustrumGeometry, self.name, parent=self.visFolder, visible=False)
