# sets up classes needed for Corl in director

import os

import utils as CorlUtils
from imagecapture import ImageCapture
import registration

from director import lcmframe
from director import lcmUtils
from director import vtkAll as vtk


def setCameraToWorld(cameraToWorld):
    cameraToWorldMsg = lcmframe.rigidTransformMessageFromFrame(cameraToWorld)
    lcmUtils.publish('OPENNI_FRAME_LEFT_TO_LOCAL', cameraToWorldMsg)

def setupCorlDirector(affordanceManager, openniDepthPointCloud, logFolder="logs/moving-camera", globalsDict=None):
    """
    Setups the necessary callbacks for visualizing Corl data in director

    :param logFolder: The name of folder relative to Corl data dir
    :return:
    """

    filenames = CorlUtils.getFilenames(logFolder)

    # setup camera update callback. Sets pose of camera depending on time in lcmlog
    if os.path.isfile(filenames['cameraPoses']):
        CorlUtils.initCameraUpdateCallback(openniDepthPointCloud, setCameraToWorld, filename=filenames['cameraPoses'])

    # check if we have already figured out a transform for this or not
    firstFrameToWorldTransform = CorlUtils.getFirstFrameToWorldTransform(filenames['transforms'])

    # only load these files in info.yaml exists
    if os.path.isfile(filenames['registrationResult']):
        CorlUtils.loadObjectMeshes(affordanceManager, filenames['registrationResult'], firstFrameToWorldTransform)

        imageCapture = ImageCapture(globalsDict['imageManager'], filenames['images'])
        globalsDict['imageCapture'] = imageCapture

    # firstFrameToWorldTransform = vtk.vtkTransform()
    CorlUtils.loadElasticFustionReconstruction(filenames['reconstruction'], transform=firstFrameToWorldTransform)


    globalRegistration = registration.GlobalRegistration(globalsDict['view'],
                                                         globalsDict['measurementPanel'],
                                                         logFolder=logFolder,
                                                         firstFrameToWorldTransform=firstFrameToWorldTransform)
    globalsDict['globalRegistration'] = globalRegistration
    globalsDict['gr'] = globalRegistration # hack for easy access