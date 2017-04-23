import os
import numpy as np
from director import visualization as vis
from director import objectmodel as om
from director import transformUtils
from director import ioUtils
from director import filterUtils


def initRobotKinematicsCameraFrame():
    endEffectorToWorld = robotSystem.robotStateModel.getLinkFrame('iiwa_link_ee')
    frameObj = vis.updateFrame(endEffectorToWorld, 'iiwa_link_ee', parent='debug', scale=0.15, visible=False)
    cameraToEE = transformUtils.frameFromPositionAndRPY([0.1,0,0.0], [-90,-22.5,-90])
    cameraToWorld = transformUtils.concatenateTransforms([cameraToEE, endEffectorToWorld])
    obj = vis.updateFrame(cameraToWorld, 'camera frame', parent=frameObj, scale=0.15)
    frameObj.getFrameSync().addFrame(obj, ignoreIncoming=True)

    def onCameraFrameModified(f):
        setCameraToWorld(f.transform)

    obj.connectFrameModified(onCameraFrameModified)


def updateCameraPoseFromRobotKinematics(model):
    endEffectorToWorld = model.getLinkFrame('iiwa_link_ee')
    vis.updateFrame(endEffectorToWorld, 'iiwa_link_ee', parent='debug', scale=0.15, visible=False)


def getDefaultCameraToWorld():
    return transformUtils.frameFromPositionAndRPY([0,0,0], [-90,0,-90])


def printObjectPose(name):
    obj = om.findObjectByName(name)
    assert obj
    pos, quat = transformUtils.poseFromTransform(obj.getChildFrame().transform)
    print (pos.tolist(), quat.tolist())


def loadAffordanceModel(affordanceManager, name, filename, pose):
    return affordanceManager.newAffordanceFromDescription(
        dict(classname='MeshAffordanceItem', Name=name,
             pose=pose, Filename=filename))


def loadObjectMeshes(affordanceManager):

    objData = getResultsConfig()['object-registration']
    dataDir = getCorlDataDir()

    for obj in objData:
        loadAffordanceModel(
            affordanceManager,
            name=obj['name'],
            filename=os.path.join(dataDir, obj['filename']),
            pose=obj['pose'])


def getCorlBaseDir():
    return os.path.join(os.environ['SPARTAN_SOURCE_DIR'], 'src/CorlDev')


def getCorlRelativePath(path):
    return os.path.join(getCorlBaseDir(), path)


def getCorlDataDir():
    return getCorlRelativePath('data')


def evalFileAsString(filename):
    context = dict()
    return eval(open(filename, 'r').read(), context)


def getResultsConfig():
    filename = getCorlRelativePath('config/registration_result.py')
    return evalFileAsString(filename)


def loadElasticFustionReconstruction():
    filename = os.path.join(getCorlDataDir(), getResultsConfig()['reconstruction'])
    polyData = ioUtils.readPolyData(filename)
    polyData = filterUtils.transformPolyData(polyData, getDefaultCameraToWorld())
    obj = vis.showPolyData(polyData, 'reconstruction', colorByName='RGB')
    return obj


def initCameraUpdateCallback(obj, publishCameraPoseFunction):

    filename = os.path.join(getCorlDataDir(), getResultsConfig()['camera-poses'])
    data = np.loadtxt(filename)
    poseTimes = np.array(data[:,0]*1e6, dtype=int)
    poses = np.array(data[:,1:])

    def getCameraPoseAtTime(t):
        ind = poseTimes.searchsorted(t)
        if ind == len(poseTimes):
            ind = len(poseTimes)-1
        pose = poses[ind]
        pos = pose[:3]
        quat = pose[6], pose[3], pose[4], pose[5] # quat data from file is ordered as x, y, z, w
        return transformUtils.transformFromPose(pos, quat)

    def myUpdate():
        lastUtime = obj.lastUtime
        obj.update()
        if obj.lastUtime == lastUtime:
            return


        cameraToCameraStart = getCameraPoseAtTime(obj.lastUtime)
        t = transformUtils.concatenateTransforms([cameraToCameraStart, getDefaultCameraToWorld()])

        vis.updateFrame(t, 'camera pose')

        useAffordanceProjection = True

        if useAffordanceProjection:
            publishCameraPoseFunction(t)
        else:
            obj.actor.SetUserTransform(t)

    obj.timer.callback = myUpdate
