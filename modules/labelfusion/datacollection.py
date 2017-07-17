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
from director import robotstate
from director.ikplanner import ConstraintSet
from director.timercallback import TimerCallback
from director.ikparameters import IkParameters


from . import utils
from .cameraposes import CameraPoses
from .registration import GlobalRegistrationUtils
from .camerafrustumvisualizer import CameraFrustumVisualizer


class DataCollectionHelper(object):

    def __init__(self, robotSystem, openniDepthPointCloud):
        self.robotSystem = robotSystem
        self.openniDepthPointCloud = openniDepthPointCloud

        self.loadData()

    def loadData(self):
        logFolder = 'logs_test/moving-camera'
        self.pathDict = utils.getFilenames(logFolder)
        if self.pathDict is None:
            return

        self.cameraposes = CameraPoses(self.pathDict['cameraposes'])


        # load the elastic fusion reconstruction if we already know where to
        # put it
        self.savedTransformFilename = os.path.join(utils.getLabelFusionBaseDir(), 'sandbox', 'reconstruction_robot_frame.yaml')
        if os.path.exists(self.savedTransformFilename):
            firstFrameToWorld = utils.getFirstFrameToWorldTransform(self.savedTransformFilename)
            utils.loadElasticFusionReconstruction(self.pathDict['reconstruction'],
                                                      transform=firstFrameToWorld)


    def loadReconstructedPointCloud(self):
        utime = self.openniDepthPointCloud.lastUtime
        cameraToFirstFrame = self.cameraposes.getCameraPoseAtUTime(utime)
        cameraToWorld = om.findObjectByName('camera frame').transform
        firstFrameToCamera = cameraToFirstFrame.GetLinearInverse()
        firstFrameToWorld = transformUtils.concatenateTransforms([firstFrameToCamera, cameraToWorld])

        self.firstFrameToWorld = firstFrameToWorld
        utils.loadElasticFusionReconstruction(self.pathDict['reconstruction'],
                                                  transform=firstFrameToWorld)

    def saveTransform(self):
        (pos, quat) = transformUtils.poseFromTransform(self.firstFrameToWorld)
        d = dict()
        d['firstFrameToWorld'] = [pos.tolist(), quat.tolist()]
        utils.saveDictToYaml(d, self.savedTransformFilename)


class DataCollection(object):

    def __init__(self, robotSystem, openniDepthPointCloud, measurementPanel,
                 imageManager):
        self.robotSystem = robotSystem
        self.openniDepthPointCloud = openniDepthPointCloud
        self.measurementPanel = measurementPanel
        self.imageManager = imageManager
        self.visFolder = om.getOrCreateContainer('data collection')
        self.cameraName = 'OPENNI_FRAME_LEFT'
        self.savedTransformFilename = os.path.join(utils.getLabelFusionBaseDir(), 'sandbox',
                                                   'reconstruction_robot_frame.yaml')
        self.frustumVis = dict()
        self.loadSavedData()
        self.setupDevTools()

    def loadSavedData(self):
        if not os.path.exists(self.savedTransformFilename):
            return

        d = utils.getDictFromYamlFilename(self.savedTransformFilename)
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
        d = GlobalRegistrationUtils.segmentTable(scenePolyData=scenePolyData, searchRadius=0.3, visualize=False, thickness=0.01, pointOnTable=pointOnTable, pointAboveTable=pointAboveTable)


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
        self.frustumVis['camera'] = self.cameraFrustumVisualizer


    def makeTargetCameraTransform(self, rotateX=-40, rotateY=0, translateZ=-0.8, visualize=True):
        t = transformUtils.copyFrame(self.tableFrame.transform)
        t.PreMultiply()
        t.RotateX(rotateX)
        t.RotateY(rotateY)
        t.Translate((0,0,translateZ))


        if visualize:
            name = 'target camera frame'
            if om.findObjectByName(name) is None:
                frame = vis.updateFrame(t, name, scale=0.15)
                cameraFrustum = CameraFrustumVisualizer(self.imageManager, self.cameraName, frame, verbose=False, visFolder=frame)
                self.frustumVis['target camera'] = cameraFrustum
            else:
                frame = vis.updateFrame(t, name, scale=0.15)


            self.targetCameraFrame = frame

        return t

    def makeTargetCameraFrames(self, filename=None):
        self.targetFrames = []

        if filename is None:
            filename = 'data_collection.yaml'

        fullFilename = os.path.join(utils.getLabelFusionBaseDir(), 'config', filename)
        frameData = utils.getDictFromYamlFilename(fullFilename)['frames']
        graspToHandLinkFrame = utils.getCameraToKukaEndEffectorFrame()

        # d = dict()
        # d['rotateX'] = -40
        # d['rotateY'] = 30
        # d['translateZ'] = -0.8
        # d['numFrames'] = 4
        # frameData.append(d)

        rotationDirection = 1
        for data in frameData:
            rotateX = data['rotateX']
            translateZ = data['translateZ']
            numFrames = data['numFrames']

            rotateY = data['rotateY']
            rotateYGrid = np.linspace(rotateY['min'], rotateY['max'], numFrames)

            for idx in xrange(0,numFrames):
                rotateY = rotateYGrid[idx]*rotationDirection
                transform = self.makeTargetCameraTransform(rotateX=rotateX,
                                                   rotateY=rotateY,
                                                   translateZ=translateZ,
                                                   visualize=False)


                # check if feasible to reach that frame
                ikData = self.runIK(transform, makePlan=False,
                                    graspToHandLinkFrame=graspToHandLinkFrame)

                # if infeasible increase tolerance to 5 degs
                if ikData['info'] != 1:
                    ikData = self.runIK(transform, makePlan=False,
                                        graspToHandLinkFrame=graspToHandLinkFrame,
                                        angleToleranceInDegrees=5.0)

                if ikData['info'] == 1:
                    frameName = 'target frame ' + str(len(self.targetFrames))
                    frame = self.showTargetFrame(transform, frameName)
                    self.targetFrames.append(frame)
                else:
                    print "\n\n----------"
                    print "infeasible frame"
                    print "rotateX = ", rotateX
                    print "rotateY = ", rotateY
                    print "translateZ = ", translateZ
                    print "-----------\n\n"


            # alternate the rotation direction each time
            rotationDirection = -rotationDirection



    def showTargetFrame(self, transform, frameName):
        visFolder = om.getOrCreateContainer('target camera frames')
        frame = vis.updateFrame(transform, frameName,
                                parent='target camera frames',
                                scale=0.15)
        cameraFrustum = CameraFrustumVisualizer(self.imageManager,
                                                self.cameraName, frame,
                                                verbose=False,
                                                visFolder=frame)

        return frame


    def saveTableFrame(self):
        # d = utils.getDictFromYamlFilename(self.savedTransformFilename)
        d = dict()
        (pos, quat) = transformUtils.poseFromTransform(self.tableFrame.transform)
        d['table frame'] = [pos.tolist(), quat.tolist()]
        utils.saveDictToYaml(d, self.savedTransformFilename)


    def setupDevTools(self):
        teleopCameraFrame = om.findObjectByName('camera frame teleop')
        teleopCameraFrameFrustumVis = CameraFrustumVisualizer(self.imageManager,
                                                              self.cameraName,
                                                              teleopCameraFrame,
                                                              verbose=False)

        self.frustumVis['teleop'] = teleopCameraFrameFrustumVis

        self.testCameraFrustrum()
        # self.makeTargetCameraFrames()
    def runIK(self, targetFrame, startPose=None, graspToHandLinkFrame=None,
              makePlan=True, positionTolerance=0.0, angleToleranceInDegrees=5.0,
              maxDegreesPerSecond=60):
        """
        Sets the cameraFrame to the targetFrame using IK
        :param targetFrame:
        :return:
        """

        if startPose is None:
            startPose = self.getPlanningStartPose()

        ikPlanner = self.robotSystem.ikPlanner
        startPoseName = 'reach_start'
        endPoseName = 'reach_end'
        ikPlanner.addPose(startPose, startPoseName)
        side = ikPlanner.reachingSide

        constraints = []
        constraints.append(KukaPlanningUtils.createLockedBasePostureConstraint(ikPlanner, startPoseName))

        positionConstraint, orientationConstraint = ikPlanner.createPositionOrientationGraspConstraints(side, targetFrame,
                                                                                                   graspToHandLinkFrame,
                                                                                                   positionTolerance=positionTolerance,
                                                                                                   angleToleranceInDegrees=angleToleranceInDegrees)
        positionConstraint.tspan = [1.0, 1.0]
        orientationConstraint.tspan = [1.0, 1.0]

        constraints.append(positionConstraint)
        constraints.append(orientationConstraint)

        constraintSet = ConstraintSet(ikPlanner, constraints, 'reach_end',
                                      startPoseName)
        constraintSet.ikParameters = IkParameters(maxDegreesPerSecond=maxDegreesPerSecond)



        endPose, info = constraintSet.runIk()
        returnData = dict()
        returnData['info'] = info
        returnData['endPose'] = endPose

        if makePlan:
            plan = constraintSet.planEndPoseGoal()
            returnData['plan'] = plan

        return returnData

    def getPlanningStartPose(self):
        return self.robotSystem.robotStateJointController.q


    def testRunIK(self):
        targetFrame = self.targetCameraFrame.transform
        graspToHandLinkFrame = utils.getCameraToKukaEndEffectorFrame()
        return self.runIK(targetFrame, graspToHandLinkFrame=graspToHandLinkFrame)

    def reachToTargetFrame(self, frameNum):
        targetFrame = self.targetFrames[frameNum].transform
        graspToHandLinkFrame = utils.getCameraToKukaEndEffectorFrame()
        return self.runIK(targetFrame, graspToHandLinkFrame=graspToHandLinkFrame)

    def spawnTargetFrame(self):
        debugFolder = om.getOrCreateContainer('debug')
        om.removeFromObjectModel('target frame')

        handLink = str(self.robotSystem.ikPlanner.getHandLink())
        handFrame = transformUtils.copyFrame(self.robotSystem.robotStateModel.getLinkFrame(handLink))

        handFrame.PreMultiply()
        handFrame.Translate(0.02, 0, 0)

        self.targetFrame = vis.updateFrame(handFrame, 'target frame', parent=debugFolder, scale=0.15)
        return self.targetFrame

    def makePlanRunner(self):
        return DataCollectionPlanRunner(self, self.robotSystem, self.targetFrames)



class DataCollectionPlanRunner(object):
    def __init__(self, dataCollection, robotSystem, targetFrames, configFilename=None):
        self.robotSystem = robotSystem
        self.dataCollection = dataCollection
        self.timer = TimerCallback(targetFps=5)
        self.timer.callback = self.callback
        self.targetFrames = targetFrames
        self.counter = 0
        self.configFilename = configFilename
        self.initialized = False
        self.loadConfig(self.configFilename)

    def loadConfig(self, configFilename):
        if configFilename is None:
            configFilename = 'data_collection.yaml'

        fullFilename = os.path.join(utils.getLabelFusionBaseDir(), 'config', configFilename)
        self.config = utils.getDictFromYamlFilename(fullFilename)

    def start(self):
        print "starting data collection plan runner"
        self.timer.start()
        os.system("cd /home/robot-lab/newdata && sleep 4 && auto_start_data_collect &")

    def stop(self):
        print "stopping data collection plan runner"
        self.timer.stop()

    def callback(self):

        if self.initialized:
            utime = self.getUtime()
            if utime < self.planData['endUTime']:
                return

        self.initialized = True

        if self.counter >= len(self.targetFrames):
            print "finished reaching all target frames"
            self.stop()
            return

        planData = self.makeNextPlan()
        if planData['info'] == 1:
            self.commitNextPlan()
        else:
            self.stop()
            raise ValueError(' plan info was not 1, stopping execution')





    def makeNextPlan(self):
        targetFrame = self.targetFrames[self.counter].transform
        graspToHandLinkFrame = utils.getCameraToKukaEndEffectorFrame()
        maxDegreesPerSecond = self.config['planning']['maxDegreesPerSecond']
        self.planData =  self.dataCollection.runIK(targetFrame, graspToHandLinkFrame=graspToHandLinkFrame, maxDegreesPerSecond=maxDegreesPerSecond)
        return self.planData

    def getUtime(self):
        return self.robotSystem.robotStateJointController.lastRobotStateMessage.utime

    def commitNextPlan(self):
        print "committed a new plan"
        self.robotSystem.manipPlanner.commitManipPlan(self.planData['plan'])
        planDuration = self.planData['plan'].plan[-1].utime
        self.planData['endUTime'] = self.getUtime() + 1.1*planDuration
        self.counter += 1


class KukaPlanningUtils(object):

    @staticmethod
    def createLockedBasePostureConstraint(ikPlanner, startPoseName):
        return ikPlanner.createPostureConstraint(startPoseName, robotstate.matchJoints('base_'))

