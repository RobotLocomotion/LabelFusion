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


def getCameraToKukaEndEffectorFrame():
    return transformUtils.frameFromPositionAndRPY([0.1, 0, 0.0], [-90, -22.5, -90])

def setCameraToWorld(cameraToWorld):
    cameraToWorldMsg = lcmframe.rigidTransformMessageFromFrame(cameraToWorld)
    lcmUtils.publish('OPENNI_FRAME_LEFT_TO_LOCAL', cameraToWorldMsg)

def initRobotKinematicsCameraFrame(robotSystem):
    endEffectorToWorld = robotSystem.robotStateModel.getLinkFrame('iiwa_link_ee')
    frameObj = vis.updateFrame(endEffectorToWorld, 'iiwa_link_ee', parent='debug', scale=0.15, visible=False)
    cameraToEE = getCameraToKukaEndEffectorFrame()
    cameraToWorld = transformUtils.concatenateTransforms([cameraToEE, endEffectorToWorld])
    obj = vis.updateFrame(cameraToWorld, 'camera frame', parent=frameObj, scale=0.15)
    frameObj.getFrameSync().addFrame(obj, ignoreIncoming=True)

    def onCameraFrameModified(f):
        setCameraToWorld(f.transform)

    obj.connectFrameModified(onCameraFrameModified)

def initRobotTeleopCameraFrame(robotSystem):
    endEffectorToWorld = robotSystem.teleopRobotModel.getLinkFrame('iiwa_link_ee')
    frameObj = vis.updateFrame(endEffectorToWorld, 'iiwa_link_ee_teleop', parent='debug', scale=0.15, visible=False)
    cameraToEE = getCameraToKukaEndEffectorFrame()
    cameraToWorld = transformUtils.concatenateTransforms([cameraToEE, endEffectorToWorld])
    obj = vis.updateFrame(cameraToWorld, 'camera frame Teleop', parent=frameObj, scale=0.15, visible=False)
    frameObj.getFrameSync().addFrame(obj, ignoreIncoming=True)


    def updateFrame(model):
        EEToWorld = model.getLinkFrame('iiwa_link_ee')
        frameObj = vis.updateFrame(EEToWorld, 'iiwa_link_ee_teleop', parent='debug', scale=0.15, visible=False)

    # setup the callback so it updates when we move the teleop model
    robotSystem.teleopRobotModel.connectModelChanged(updateFrame)


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


def loadObjectMesh(affordanceManager, objectName, visName=None, pose=None):
    if visName is None:
        visName = objectName + "_raw"
    filename = getObjectMeshFilename(objectName)

    if pose is None:
        pose = [[0,0,0],[1,0,0,0]]
    return loadAffordanceModel(affordanceManager, visName,
                        filename, pose)


def loadAffordanceModel(affordanceManager, name, filename, pose):
    return affordanceManager.newAffordanceFromDescription(
        dict(classname='MeshAffordanceItem', Name=name,
             pose=pose, Filename=filename))


def loadObjectMeshes(affordanceManager, registrationResultFilename,
                     firstFrameToWorldTransform):
    """
    Loads the object meshes from the registration_result.yaml file
    :param affordanceManager:
    :param registrationResultFilename: filename of registration_result.yaml, should be an absolute path
    :param transformsFilename: filename of transforms.yaml where firstFrameToWorld transform is.
    :return: None
    """

    stream = file(registrationResultFilename)
    registrationResult = yaml.load(stream)

    for objName, data in registrationResult.iteritems():
        objectMeshFilename = data['filename'] # should be relative to getCorlDataDir()
        if len(objectMeshFilename) == 0:
            objectMeshFilename = getObjectMeshFilename(objName)
        else:
            objectMeshFilename = os.path.join(getCorlDataDir(), objectMeshFilename)

        # figure out object pose in world frame
        # we have stored object pose in first camera frame
        objectToFirstFrame = transformUtils.transformFromPose(data['pose'][0], data['pose'][1])
        objectToWorld = transformUtils.concatenateTransforms([objectToFirstFrame, firstFrameToWorldTransform])
        pose = transformUtils.poseFromTransform(objectToWorld)

        loadAffordanceModel(
            affordanceManager,
            name=objName,
            filename=objectMeshFilename,
            pose=pose)


def getCorlBaseDir():
    return os.path.join(os.environ['SPARTAN_SOURCE_DIR'], 'src/CorlDev')

def getCorlRelativePath(path):
    return os.path.join(getCorlBaseDir(), path)

def getCorlDataRelativePath(path):
    return os.path.join(getCorlDataDir(), path)

def getCorlDataDir():
    return getCorlRelativePath('data')

def getSuper4PCSBaseDir():
    return os.getenv("SUPER4PCS_BASE_DIR")

def getGoICPBaseDir():
    return os.getenv("GOICP_BASE_DIR")

def getGRBaseDir():
    return os.getenv('FGR_BASE_DIR')

def getObjectDataFilename():
    return os.path.join(getCorlBaseDir(), 'config/object_data.yaml')

def getObjectDataYamlFile():
    stream = file(getObjectDataFilename())
    return yaml.load(stream)

def getDictFromYamlFilename(filename):
    stream = file(filename)
    return yaml.load(stream)

objectDataFilename = os.path.join(getCorlBaseDir(), 'config/object_data.yaml')
objectData = yaml.load(file(objectDataFilename))

def getObjectMeshFilename(objectName):
    """
    Returns the filename of mesh corresponding to this object.
    Filename is relative to getCorlDataDir()
    """

    if objectName not in objectData:
        raise ValueError('there is no data for ' + objectName)

    return os.path.join(getCorlDataDir(), objectData[objectName]['mesh'])

def getObjectPolyData(objectName):
    filename = getObjectMeshFilename(objectName)
    return ioUtils.readPolyData(filename)

def getObjectLabel(objectName):
    """
    Returns the object label specified in object_data.yaml
    :param objectName:
    :return:
    """

    if objectName not in objectData:
        raise ValueError('there is no data for ' + objectName)

    return objectData[objectName]['label']


def convertImageIDToPaddedString(n, numCharacters=10):
    """
    Converts the integer n to a padded string with leading zeros
    """
    t = str(n)
    return t.rjust(numCharacters, '0')

def getImageBasenameFromImageNumber(imageNum, pathDict):
    """

    :param imageNum:
    :param pathDict: dict containing key 'images' with path to images folder
    :return: full path to corresponding image, minus _rgb.png etc.
    """
    filename = convertImageIDToPaddedString(imageNum)
    return os.path.join(pathDict['images'], filename)


def evalFileAsString(filename):
    context = dict()
    return eval(open(filename, 'r').read(), context)


def getResultsConfig():
    filename = getCorlRelativePath('config/registration_result.py')
    return evalFileAsString(filename)


def loadElasticFusionReconstruction(filename, transform=None):
    """
    Loads reconstructed pointcloud into director view
    :param filename:
    :return:
    """

    if transform is None:
        transform = getDefaultCameraToWorld()

    polyData = ioUtils.readPolyData(filename)
    polyData = filterUtils.transformPolyData(polyData, transform)
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

def setupKukaMountedCameraCallback(robotSystem):
    initRobotKinematicsCameraFrame(robotSystem)
    robotSystem.robotStateModel.connectModelChanged(updateCameraPoseFromRobotKinematics)

def getFirstFrameToWorldTransform(transformsFile):
    if os.path.isfile(transformsFile):
        print("using user specified transform")
        stream = file(transformsFile)
        transformYaml = yaml.load(stream)
        pose = transformYaml['firstFrameToWorld']
        transform = transformUtils.transformFromPose(pose[0], pose[1])
        return transform
    else:
        return vtk.vtkTransform()


def getFilenames(logFolder):
    """
    Parse some standard filenames into a dict given the logFolder
    :param logFolder:
    :return:
    """
    d = dict()
    d['info'] = os.path.join(getCorlDataDir(), logFolder, "info.yaml")

    stream = file(d['info'])
    infoYaml = yaml.load(stream)

    d['lcmlog'] = os.path.join(getCorlDataDir(), logFolder, infoYaml['lcmlog'])
    d['cameraPoses'] = os.path.join(getCorlDataDir(), logFolder, "posegraph.posegraph")
    d['registrationResult'] = os.path.join(getCorlDataDir(), logFolder, "registration_result.yaml")
    d['reconstruction'] = os.path.join(getCorlDataDir(), logFolder, "reconstructed_pointcloud.vtp")
    d['aboveTablePointcloud'] = os.path.join(getCorlDataDir(), logFolder, "above_table_pointcloud.vtp")
    d['images'] = os.path.join(getCorlDataDir(), logFolder, "images")
    d['topLevelFolder'] = os.path.join(getCorlDataDir(), logFolder)
    d['transforms'] = os.path.join(getCorlDataDir(), logFolder, 'transforms.yaml')
    return d

def saveDictToYaml(data, filename):
    with open(filename, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

def saveObjectPolyData(objectName):
    visObj = om.findObjectByName(objectName)
    filename = os.path.join(getCorlDataDir(),'object-meshes',objectName + '_aligned.vtp')
    polyData = filterUtils.transformPolyData(visObj.polyData, visObj.actor.GetUserTransform())
    ioUtils.writePolyData(polyData, filename)

def loadHandheldScannerMesh(affordanceManager, filename='oil_bottle.obj', name='oil_bottle', scaleDown=True):
    filename = os.path.join(getCorlDataDir(),'object-meshes/handheld-scanner', filename)
    print filename
    pose = [[0,0,0],[1,0,0,0]]
    visObj = loadAffordanceModel(affordanceManager, name, filename, pose)
    t = visObj.getChildFrame().transform
    center = visObj.polyData.GetCenter()
    translation = -np.array(center)
    t.Translate(translation)
    scale = 0.001
    t.Scale(scale, scale, scale)
    polyData = filterUtils.transformPolyData(visObj.polyData, t)

    om.removeFromObjectModel(visObj)

    scaledVisObj = vis.showPolyData(polyData, name+'_small')
    vis.addChildFrame(scaledVisObj)

def centerObject(visObj):
    polyData = filterUtils.transformPolyData(visObj.polyData, visObj.actor.GetUserTransform())
    name = visObj.getProperty('Name')

    om.removeFromObjectModel(visObj)
    newVisObj = vis.showPolyData(polyData, name)
    vis.addChildFrame(newVisObj)

def saveObject(visObj, filename=None, overwrite=False, pathToDir='handheld-scanner'):
    if filename is None:
        filename = visObj.getProperty('Name') + '.vtp'

    filename = os.path.join(getCorlDataDir(),'object-meshes', pathToDir, filename)
    polyData = visObj.polyData

    if not overwrite:
        if os.path.exists(filename):
            raise ValueError('file already exists, not overwriting')
            return

    userTransform = visObj.actor.GetUserTransform()
    if userTransform is not None:
        polyData = filterUtils.transformPolyData(polyData, visObj.actor.GetUserTransform())

    ioUtils.writePolyData(polyData, filename)

def loadCube(subdivisions=30):
    d = DebugData()
    dim = np.array([0.11,0.11,0.12])
    center = np.array([0,0,0])
    d.addCube(dim, center, subdivisions=subdivisions)
    polyData = d.getPolyData()
    visObj = vis.showPolyData(polyData, 'tissue_box_subdivision')
    print "number of points = ", polyData.GetNumberOfPoints()

    sampledPolyData = segmentation.applyVoxelGrid(polyData, leafSize=0.0001)
    visObj2 = vis.showPolyData(sampledPolyData, 'voxel grid', color=[0,1,0])

    print "voxel number of points ", sampledPolyData.GetNumberOfPoints()
    return (visObj, visObj2)



