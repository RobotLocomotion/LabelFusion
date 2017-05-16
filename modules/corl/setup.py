# sets up classes needed for Corl in director
import utils as CorlUtils
from imagecapture import ImageCapture
import registration

def setupCorlDirector(robotSystem, openniDepthPointCloud, setCameraToWorld, logFolder="logs/moving-camera", globalsDict=None, extraInputs=None):
    """
    Setups the necessary callbacks for visualizing Corl data in director

    :param logFolder: The name of folder relative to Corl data dir
    :return:
    """

    filenames = CorlUtils.getFilenames(logFolder)

    # setup camera update callback. Sets pose of camera depending on time in lcmlog
    CorlUtils.initCameraUpdateCallback(openniDepthPointCloud, setCameraToWorld, filename=filenames['cameraPoses'])

    CorlUtils.loadObjectMeshes(robotSystem.affordanceManager, filenames['registrationResult'])
    CorlUtils.loadElasticFustionReconstruction(filenames['reconstruction'])

    imageCapture = ImageCapture(extraInputs['imageManager'], filenames['images'])

    # add necessary classes to globalsDict
    globalsDict['imageCapture'] = imageCapture

    globalRegistration = registration.GlobalRegistration(globalsDict['view'],
                                                         globalsDict['measurementPanel'])
    globalsDict['globalRegistration'] = globalRegistration
    globalsDict['gr'] = globalRegistration # hack for easy access