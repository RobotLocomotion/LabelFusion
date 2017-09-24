import numpy as np
import PythonQt
from PythonQt import QtGui, QtCore

from director import objectmodel as om
from director import ioUtils
from director import visualization as vis
from director import transformUtils
from director import filterUtils
from director import segmentation
from director import pointpicker
from director import lcmframe
from director import lcmUtils
from director import applogic
from director.debugVis import DebugData
from director import viewbehaviors
from director import vtkAll as vtk
from director import vtkNumpy as vnp
from director.shallowCopy import shallowCopy
from director.tasks.taskuserpanel import ImageBasedAffordanceFit

from . import utils


distanceToMeshThreshold = 0.2

class ImageFitter(ImageBasedAffordanceFit):

    def __init__(self, parent, pointCloud):
        ImageBasedAffordanceFit.__init__(self, imageView=parent.cameraView, numberOfPoints=3)
        self.parent = parent
        self.pointCloud = pointCloud
        self.pointCloudObjectName = 'openni point cloud'

    def getPointCloud(self):
        obj = om.findObjectByName(self.pointCloudObjectName)
        return obj.polyData if obj else vtk.vtkPolyData()

    def fit(self, polyData, points):
        self.parent.onImagePick(points)


def makeDebugPoints(points, radius=0.01):
    d = DebugData()
    for p in points:
        d.addSphere(p, radius=radius)
    return shallowCopy(d.getPolyData())


def computeLandmarkTransform(sourcePoints, targetPoints):
    '''
    Returns a vtkTransform for the transform sourceToTarget
    that can be used to transform the source points to the target.
    '''
    sourcePoints = vnp.getVtkPointsFromNumpy(np.array(sourcePoints))
    targetPoints = vnp.getVtkPointsFromNumpy(np.array(targetPoints))

    f = vtk.vtkLandmarkTransform()
    f.SetSourceLandmarks(sourcePoints)
    f.SetTargetLandmarks(targetPoints)
    f.SetModeToRigidBody()
    f.Update()

    mat = f.GetMatrix()
    t = vtk.vtkTransform()
    t.PostMultiply()
    t.SetMatrix(mat)
    return t


def computePointToSurfaceDistance(pointsPolyData, meshPolyData):

    cl = vtk.vtkCellLocator()
    cl.SetDataSet(meshPolyData)
    cl.BuildLocator()

    points = vnp.getNumpyFromVtk(pointsPolyData, 'Points')
    dists = np.zeros(len(points))


    closestPoint = np.zeros(3)
    closestPointDist = vtk.mutable(0.0)
    cellId = vtk.mutable(0)
    subId = vtk.mutable(0)

    for i in xrange(len(points)):
        cl.FindClosestPoint(points[i], closestPoint, cellId, subId, closestPointDist)
        dists[i] = closestPointDist

    return np.sqrt(dists)


class ObjectAlignmentTool(object):

    def __init__(self, cameraView, modelPolyData=None, pointCloud=None, resultsDict=None, visualize=True, callback=None):
        self.modelPolyData = modelPolyData
        self.pointCloud = pointCloud
        self.resultsDict = resultsDict
        self.visualize = visualize
        self.callback = callback
        self.parent = om.getOrCreateContainer('object alignment')

        self.meshPoints = None
        self.imagePoints = None
        self.cameraView = cameraView

        # viewer for the object
        self.view = PythonQt.dd.ddQVTKWidgetView()

        # add some special logic to show colors if they exist
        colorByName = 'RGB255'
        if not self.modelPolyData.GetPointData().GetArray(colorByName):
            colorByName = None
        vis.showPolyData(self.modelPolyData, 'object poly data', view=self.view,
                         parent=self.parent, colorByName=colorByName)

        self.imageFitter = ImageFitter(self, pointCloud)



        self.picker = pointpicker.PointPicker(self.view)
        self.picker.pickType = 'cells' # might need to change this
        self.picker.numberOfPoints = 3
        self.picker.annotationName = 'mesh annotation'
        self.picker.annotationFunc = self.onPickPoints
        self.picker.start()

        # viewer for the pointcloud
        self.sceneView = PythonQt.dd.ddQVTKWidgetView()
        vis.showPolyData(self.pointCloud, 'pointcloud', view=self.sceneView, colorByName='RGB', parent=self.parent)
        self.scenePicker = pointpicker.PointPicker(self.sceneView)
        self.scenePicker.pickType = 'points'  # might need to change this
        self.scenePicker.numberOfPoints = 3
        self.scenePicker.annotationName = 'pointcloud annotation'
        self.scenePicker.annotationFunc = self.onScenePickPoints
        self.scenePicker.start()

        # workaround bug in PointPicker implementation
        for name in [self.picker.annotationName, self.scenePicker.annotationName]:
            om.removeFromObjectModel(om.findObjectByName(name))

        self.widget = QtGui.QWidget()
        layout = QtGui.QHBoxLayout(self.widget)
        # layout.addWidget(self.cameraView.view)
        layout.addWidget(self.sceneView)
        layout.addWidget(self.view)
        # self.widget.resize(800, 400)
        self.widget.showMaximized()
        self.widget.setWindowTitle('Camera Alignment Tool')
        self.widget.show()

        self.viewBehaviors = viewbehaviors.ViewBehaviors(self.view)
        applogic.resetCamera(viewDirection=[0,1,0], view=self.view)
        applogic.setCameraTerrainModeEnabled(self.view, True)

        self.sceneViewBehaviors = viewbehaviors.ViewBehaviors(self.sceneView)
        applogic.resetCamera(viewDirection=[0, 1, 0], view=self.sceneView)
        applogic.setCameraTerrainModeEnabled(self.sceneView, True)

    def onImagePick(self, points):
        """
        These are points picked in the rgb image
        :param points:
        :return:
        """
        self.imagePoints = np.array(points)
        vis.showPolyData(makeDebugPoints(self.imagePoints), 'image pick points', color=[1,0,0], view=self.view, parent=self.parent)
        self.align()

    def onPickPoints(self, *points):
        """
        These are points picked in self.view which is model mesh view
        :param points:
        :return:
        """
        self.meshPoints = np.array(points)
        vis.showPolyData(makeDebugPoints(self.meshPoints), 'mesh pick points', color=[0,1,0], view=self.view, parent=self.parent)
        self.align()

    def onScenePickPoints(self, *points):
        """
        These are points picked in self.view which is model mesh view
        :param points:
        :return:
        """
        self.imagePoints = np.array(points)
        vis.showPolyData(makeDebugPoints(self.imagePoints), 'scene pick points', color=[1,0,0], view=self.sceneView, parent=self.parent)
        self.align()

    def align(self):

        if self.meshPoints is None or self.imagePoints is None:
            return

        t1 = computeLandmarkTransform(self.imagePoints, self.meshPoints)
        polyData = filterUtils.transformPolyData(self.pointCloud, t1)

        vis.showPolyData(polyData, 'transformed pointcloud', view=self.view, colorByName='rgb_colors', visible=True)
        vis.showPolyData(filterUtils.transformPolyData(makeDebugPoints(self.imagePoints), t1), 'transformed image pick points', color=[0,0,1], view=self.view, parent=self.parent)

        sceneToModelTransform = t1
        modelToSceneTransform = t1.GetLinearInverse()

        alignedModel = filterUtils.transformPolyData(self.modelPolyData, modelToSceneTransform)
        vis.showPolyData(alignedModel, 'aligned model', view=self.sceneView, parent=self.parent)


        #
        # boxBounds = [[-0.5,0.50], [-0.3,0.3], [0.15,1.5]] #xmin,xmax,  ymin,ymax,  zmin,zmax
        #
        # polyData = segmentation.cropToBounds(polyData, self.robotBaseFrame, [[-0.5,0.50],[-0.3,0.3],[0.15,1.5]])
        #
        # #arrayName = 'distance_to_mesh'
        # #dists = computePointToSurfaceDistance(polyData, self.robotMesh)
        # #vnp.addNumpyToVtk(polyData, dists, arrayName)
        # #polyData = filterUtils.thresholdPoints(polyData, arrayName, [0.0, distanceToMeshThreshold])
        #
        #
        # #polyData = segmentation.applyVoxelGrid(polyData, leafSize=0.01)
        # #polyData = segmentation.applyEuclideanClustering(polyData, clusterTolerance=0.04)
        # #polyData = segmentation.thresholdPoints(polyData, 'cluster_labels', [1,1])
        #
        # vis.showPolyData(polyData, 'filtered points for icp', color=[0,1,0], view=self.view, visible=True)
        #
        # t2 = segmentation.applyICP(polyData, self.robotMesh)
        #
        # vis.showPolyData(filterUtils.transformPolyData(polyData, t2), 'filtered points after icp', color=[0,1,0], view=self.view, visible=False)
        #
        #
        # cameraToWorld = transformUtils.concatenateTransforms([t1, t2])
        # polyData = filterUtils.transformPolyData(self.pointCloud, cameraToWorld)
        # vis.showPolyData(polyData, 'aligned pointcloud', colorByName='rgb_colors', view=self.view, visible=True)
        #
        # # cameraToWorldMsg = lcmframe.rigidTransformMessageFromFrame(cameraToWorld)
        # # lcmUtils.publish('OPENNI_FRAME_LEFT_TO_LOCAL', cameraToWorldMsg)
        #
        #
        if self.resultsDict is not None:
            self.resultsDict['modelToSceneTransform'] = modelToSceneTransform
            self.resultsDict['alignedModel'] = alignedModel


        if self.callback is not None:
            self.callback()

def main(robotSystem, cameraView):

    global w
    w = TestFitCamera(robotSystem, cameraView)


class ObjectAlignmentToolWrapper(object):
    """
    Wrapper with some convenience methods for interfacing with LabelFusion data
    """

    @staticmethod
    def makeAlignmentTool(cameraView, pathDict, objectName='phone'):
        # check if we have already figured out a transform for this or not
        firstFrameToWorldTransform = utils.getFirstFrameToWorldTransform(pathDict['transforms'])

        pointCloud = ioUtils.readPolyData(pathDict['reconstruction'])
        pointCloud = filterUtils.transformPolyData(pointCloud, firstFrameToWorldTransform)
        objectMesh = utils.getObjectPolyData(utils.loadObjectData(), objectName)

        alignmentTool = ObjectAlignmentTool(cameraView, modelPolyData=objectMesh, pointCloud=pointCloud)

        return alignmentTool
