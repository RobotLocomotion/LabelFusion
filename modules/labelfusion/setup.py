# sets up classes needed for LabelFusion in director

import os

from . import utils
from . import objectalignmenttool
from . import datacollection

from imagecapture import ImageCapture
import registration

from director import lcmframe
from director import lcmUtils
from director import vtkAll as vtk



def setCameraToWorld(cameraToWorld):
    cameraToWorldMsg = lcmframe.rigidTransformMessageFromFrame(cameraToWorld)
    lcmUtils.publish('OPENNI_FRAME_LEFT_TO_LOCAL', cameraToWorldMsg)


def setupLabelFusionDirector(affordanceManager, openniDepthPointCloud, logFolder="logs/moving-camera", globalsDict=None):
    """
    Setups the necessary callbacks for visualizing LabelFusion data in director

    :param logFolder: The name of folder relative to LabelFusion data dir
    :return:
    """

    filenames = utils.getFilenames(logFolder)

    # setup camera update callback. Sets pose of camera depending on time in lcmlog
    # if os.path.isfile(filenames['cameraposes']):
    #     utils.initCameraUpdateCallback(openniDepthPointCloud, setCameraToWorld, filename=filenames['cameraposes'])

    # check if we have already figured out a transform for this or not
    firstFrameToWorldTransform = utils.getFirstFrameToWorldTransform(filenames['transforms'])

    # only load these files in info.yaml exists
    if os.path.isfile(filenames['registrationResult']):
        utils.loadObjectMeshes(affordanceManager, filenames['registrationResult'], firstFrameToWorldTransform)

        imageCapture = ImageCapture(globalsDict['imageManager'], filenames['images'])
        globalsDict['imageCapture'] = imageCapture

    # firstFrameToWorldTransform = vtk.vtkTransform()
    utils.loadElasticFusionReconstruction(filenames['reconstruction'], transform=firstFrameToWorldTransform)

    globalRegistration = registration.GlobalRegistration(globalsDict['view'],
                                                         globalsDict['cameraView'],
                                                         globalsDict['measurementPanel'],
                                                         globalsDict['affordanceManager'],
                                                         logFolder=logFolder,
                                                         firstFrameToWorldTransform=firstFrameToWorldTransform)
    globalsDict['globalRegistration'] = globalRegistration
    globalsDict['gr'] = globalRegistration # hack for easy access


def testStartup(robotSystem, affordanceManager, openniDepthPointCloud, logFolder="logs/moving-camera", globalsDict=None):
    objectData = utils.loadObjectData()

    for objectName, data in objectData.iteritems():
        utils.loadObjectMesh(affordanceManager, objectName, visName=objectName)


def setupDataCollection(globalsDict):
    robotSystem = globalsDict['robotSystem']
    openniDepthPointCloud = globalsDict['openniDepthPointCloud']
    measurementPanel = globalsDict['measurementPanel']
    imageManager = globalsDict['imageManager']

    utils.setupKukaMountedCameraCallback(robotSystem)
    utils.initRobotTeleopCameraFrame(robotSystem)
    dataCollectionHelper = datacollection.DataCollectionHelper(robotSystem, openniDepthPointCloud)
    dataCollection = datacollection.DataCollection(robotSystem, openniDepthPointCloud, measurementPanel, imageManager)

    globalsDict['dch'] = dataCollectionHelper
    globalsDict['dc'] = dataCollection
