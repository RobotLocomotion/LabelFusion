import os
import numpy as np
import yaml
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


def loadObjectMeshes(affordanceManager, filename):
    """
    Loads the object meshes from the registration_result.yaml file
    :param affordanceManager:
    :param filename: filename of registration_result.yaml, should be an absolute path
    :return: None
    """

    stream = file(filename)
    registrationResult = yaml.load(stream)

    for objName, data in registrationResult.iteritems():
        objectMeshFilename = data['filename'] # should be relative to getCorlDataDir()
        if len(objectMeshFilename) == 0:
            objectMeshFilename = getObjectMeshFilename(objName)
        else:
            objectMeshFilename = os.path.join(getCorlDataDir(), objectMeshFilename)

        loadAffordanceModel(
            affordanceManager,
            name=objName,
            filename=objectMeshFilename,
            pose=data['pose'])


def getCorlBaseDir():
    return os.path.join(os.environ['SPARTAN_SOURCE_DIR'], 'src/CorlDev')


def getCorlRelativePath(path):
    return os.path.join(getCorlBaseDir(), path)
    

def getCorlDataDir():
    return getCorlRelativePath('data')

def getObjectMeshFilename(objectName):
    """
    Returns the filename of mesh corresponding to this object.
    Filename is relative to getCorlDataDir()
    """
    objectMeshMapFilename = os.path.join(getCorlBaseDir(), 'config/object_mesh_map.yaml')

    stream = file(objectMeshMapFilename)
    objectMeshMap = yaml.load(stream)

    if objectName not in objectMeshMap:
        raise ValueError('there is no mesh for ' + objectName)

    return os.path.join(getCorlBaseDir(), objectMeshMap[objectName])


def convertImageIDToPaddedString(n, numCharacters=10):
    """
    Converts the integer n to a padded string with leading zeros
    """
    t = str(n)
    return t.rjust(numCharacters, '0')


def evalFileAsString(filename):
    context = dict()
    return eval(open(filename, 'r').read(), context)


def getResultsConfig():
    filename = getCorlRelativePath('config/registration_result.py')
    return evalFileAsString(filename)


def loadElasticFustionReconstruction(filename):
    """
    Loads reconstructed pointcloud into director view
    :param filename:
    :return:
    """
    polyData = ioUtils.readPolyData(filename)
    polyData = filterUtils.transformPolyData(polyData, getDefaultCameraToWorld())
    obj = vis.showPolyData(polyData, 'reconstruction', colorByName='RGB')
    return obj


def initCameraUpdateCallback(obj, publishCameraPoseFunction, filename):
    """

    :param obj:
    :param publishCameraPoseFunction:
    :param filename: Says where to find camera-poses from ElasticFusion
    :return:
    """

    
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

def getFilenames(logFolder):
    """
    Parse some standard filenames into a dict given the logFolder
    :param logFolder:
    :return:
    """
    d = dict()
    d['info'] = os.path.join(getCorlDataDir(), logFolder, "info.yaml")
    d['cameraPoses'] = os.path.join(getCorlDataDir(), logFolder, "posegraph.posegraph")
    d['registrationResult'] = os.path.join(getCorlDataDir(), logFolder, "registration_result.yaml")
    d['reconstruction'] = os.path.join(getCorlDataDir(), logFolder, "reconstructed_pointcloud.vtp")
    d['images'] = os.path.join(getCorlDataDir(), logFolder, "images")
    return d






