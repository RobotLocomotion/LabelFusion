from director import mainwindowapp
from director import drcargs
from director import cameraview
from director import objectmodel as om
from director import segmentation
from director import vtkAll as vtk
from director import affordancemanager
import bot_core as lcmbotcore

import PythonQt
from PythonQt import QtCore, QtGui

import labelfusion.setup
import labelfusion.utils

def initImageManager():
    imageManager = cameraview.ImageManager()
    cameraview.imageManager = imageManager
    return imageManager

def initDepthPointCloud(imageManager, view):

    openniDepthPointCloud = segmentation.DisparityPointCloudItem('openni point cloud', 'OPENNI_FRAME', 'OPENNI_FRAME_LEFT', imageManager)
    openniDepthPointCloud.addToView(view)
    om.addToObjectModel(openniDepthPointCloud, parentObj=om.findObjectByName('sensors'))
    openniDepthPointCloud.setProperty('Visible', True)
    openniDepthPointCloud.setProperty('Target FPS', 30)
    return openniDepthPointCloud

def newCameraView(imageManager, channelName='OPENNI_FRAME', cameraName='OPENNI_FRAME_LEFT', viewName='OpenNI Frame'):

    view = PythonQt.dd.ddQVTKWidgetView()
    view.orientationMarkerWidget().Off()
    view.backgroundRenderer().SetBackground([0,0,0])
    view.backgroundRenderer().SetBackground2([0,0,0])

    imageManager.queue.addCameraStream(channelName, cameraName, lcmbotcore.images_t.LEFT)
    imageManager.addImage(cameraName)

    cameraView = cameraview.CameraImageView(imageManager, cameraName, viewName=viewName, view=view)
    cameraView.eventFilterEnabled = False
    view.renderWindow().GetInteractor().SetInteractorStyle(vtk.vtkInteractorStyleImage())

    return cameraView

if __name__ == '__main__':

    # parse args first
    parser = drcargs.getGlobalArgParser().getParser()
    parser.add_argument('--logFolder', type=str, dest='logFolder',
                          help='location of top level folder for this log, relative to LabelFusion/data')

    args = parser.parse_args()
    print 'log folder:', args.logFolder

    # construct the app
    fields = mainwindowapp.construct()

    imageManager = initImageManager()
    openniDepthPointCloud = initDepthPointCloud(imageManager, fields.view)
    cameraView = newCameraView(imageManager)
    affordanceManager = affordancemanager.AffordanceObjectModelManager(fields.view)

    myObjects = dict()
    myObjects['imageManager'] = imageManager
    myObjects['openniDepthPointCloud'] = openniDepthPointCloud
    myObjects['cameraView'] = cameraView
    myObjects['affordanceManager'] = affordanceManager

    # these lines are used to update the globals for the interactive python console
    fields.globalsDict.update(**dict(fields))
    globals().update(**fields.globalsDict)
    globals().update(**myObjects)

    # # add custom code here
    labelfusion.setup.setupLabelFusionDirector(affordanceManager,
                                 openniDepthPointCloud,
                                 logFolder=args.logFolder,
                                 globalsDict=globals())


    # labelfusion.setup.testStartup(affordanceManager,
    #                              openniDepthPointCloud,
    #                              logFolder=args.logFolder,
    #                              globalsDict=globals())

    # show the main window and start the app
    fields.app.start()
