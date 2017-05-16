# sets up classes needed for Corl in director
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
    CorlUtils.initCameraUpdateCallback(openniDepthPointCloud, setCameraToWorld, filename=filenames['cameraPoses'])

    CorlUtils.loadObjectMeshes(affordanceManager, filenames['registrationResult'])


    # check if we have already figured out a transform for this or not
    firstFrameToWorldTransform = CorlUtils.getFirstFrameToWorldTransform(filenames['transforms'])

    # firstFrameToWorldTransform = vtk.vtkTransform()
    CorlUtils.loadElasticFustionReconstruction(filenames['reconstruction'], transform=firstFrameToWorldTransform)

    imageCapture = ImageCapture(globalsDict['imageManager'], filenames['images'])

    # add necessary classes to globalsDict
    globalsDict['imageCapture'] = imageCapture

    globalRegistration = registration.GlobalRegistration(globalsDict['view'],
                                                         globalsDict['measurementPanel'])
    globalsDict['globalRegistration'] = globalRegistration
    globalsDict['gr'] = globalRegistration # hack for easy access