import os
import numpy as np
import scipy.misc
import matplotlib.cm as cm
import yaml

from director import vtkNumpy as vnp
from director import ioUtils
from director import vtkAll as vtk
from director import actionhandlers
from director import screengrabberpanel as sgp
from director import transformUtils
from director import visualization as vis
from director import objectmodel as om

from . import utils


class RenderTrainingImages(object):

    def __init__(self, view, viewOptions, pathDict):
        """
        :param pathDict: dictionary storing all the relevant paths
        """
        self.view = view
        self.viewOptions = viewOptions
        self.pathDict = pathDict
        self.objectData = utils.loadObjectData()
        self.storedColors = {}
        self.colors = cm.nipy_spectral(np.linspace(0, 1, len(self.objectData.keys())))
        self.colors = np.append(self.colors, [[0.5, 0.5, 0.5, 1.0]], axis=0)
        self.objectToWorld = dict()
        self.initialize()

    def initialize(self):
        self.loadcameraposes()
        self.loadObjectMeshes()

        backgroundImageFilename = utils.getImageBasenameFromImageNumber(1, self.pathDict) + "_rgb.png"

        self.loadBackgroundImage(backgroundImageFilename)
        om.findObjectByName('grid').setProperty('Visible', False)

        view = self.view
        view.setFixedSize(640, 480)
        setCameraInstrinsicsAsus(view)
        # cameraToWorld = utils.getDefaultCameraToWorld()
        # setCameraTransform(view.camera(), cameraToWorld)
        setCameraTransform(view.camera(), vtk.vtkTransform())
        view.forceRender()
        self.enableLighting()


    def disableLighting(self):
        view = self.view
        viewOptions = self.viewOptions

        viewOptions.setProperty('Gradient background', False)
        viewOptions.setProperty('Orientation widget', False)
        viewOptions.setProperty('Background color', [0, 0, 0])

        view.renderer().TexturedBackgroundOff()

        for obj in om.findObjectByName('data files').children():
            objName = obj.getProperty('Name')
            objLabel = utils.getObjectLabel(self.objectData, objName)
            obj.actor.GetProperty().LightingOff()
            self.storedColors[obj.getProperty('Name')] = list(obj.getProperty('Color'))
            obj.setProperty('Color', [objLabel / 255.0] * 3)
        view.forceRender()

    def enableLighting(self):
        view = self.view
        viewOptions = self.viewOptions

        viewOptions.setProperty('Gradient background', False)
        viewOptions.setProperty('Orientation widget', False)
        viewOptions.setProperty('Background color', [0.0,0.0,0.0])

        if view.renderer().GetBackgroundTexture():
            view.renderer().TexturedBackgroundOn()

        for obj in om.findObjectByName('data files').children():
            obj.actor.GetProperty().LightingOn()
            obj.setProperty('Color', self.storedColors[obj.getProperty('Name')])
        view.forceRender()


    def captureColorImage(self, filename):
        view = self.view
        self.enableLighting()
        print 'writing:', filename
        im = sgp.saveScreenshot(view, filename, shouldRender=False, shouldWrite=True)
        return im


    def captureLabelImage(self, filename):
        view = self.view
        self.disableLighting()
        im = sgp.saveScreenshot(view, filename, shouldRender=False, shouldWrite=False)

        if filename is not None:
            img = vnp.getNumpyFromVtk(im, 'ImageScalars')
            assert img.dtype == np.uint8

            img.shape = (im.GetDimensions()[1], im.GetDimensions()[0], 3)
            img = np.flipud(img)

            img = img[:,:,0]
            print 'writing:', filename
            scipy.misc.imsave(filename, img)

        return im


    def saveImages(self, baseName):
        self.captureColorImage(baseName + '_color_labels.png')
        self.captureLabelImage(baseName + '_labels.png')


    def saveImagesTest(self):
        baseName = utils.getImageBasenameFromImageNumber(1, self.pathDict)
        self.saveImages(baseName)
        self.enableLighting()


    def loadBackgroundImage(self, filename):
        view = self.view
        img = ioUtils.readImage(filename)
        tex = vtk.vtkTexture()
        tex.SetInput(img)
        view.renderer().SetBackgroundTexture(tex)
        view.renderer().TexturedBackgroundOn()

    def loadcameraposes(self):
        filename = self.pathDict['cameraposes_smoothed']
        if not os.path.isfile(filename):
            filename = self.pathDict['cameraposes']
        assert os.path.isfile(filename)
        print 'reading:', filename
        data = np.loadtxt(filename)
        self.poseTimes = np.array(data[:,0]*1e6, dtype=int)
        self.poses = []
        for pose in data[:,1:]:
            pos = pose[:3]
            quat = pose[6], pose[3], pose[4], pose[5] # quat data from file is ordered as x, y, z, w
            self.poses.append((pos, quat))

    def getCameraPoseAtUTime(self, utime):
        idx = np.searchsorted(self.poseTimes, utime, side='left')
        if idx == len(self.poseTimes):
            idx = len(self.poseTimes) - 1

        (pos, quat) = self.poses[idx]
        return transformUtils.transformFromPose(pos, quat)

    def getColorFromIndex(self, objName):
        objLabel = utils.getObjectLabel(self.objectData, objName)
        return self.colors[objLabel][:3]

    def loadObjectMeshes(self):
        stream = file(self.pathDict['registrationResult'])
        registrationResult = yaml.load(stream)

        folder = om.getOrCreateContainer('data files')
        for objName, data in registrationResult.iteritems():

            filename = data['filename']
            if len(filename) == 0:
                filename = utils.getObjectMeshFilename(self.objectData, objName)
            else:
                filename = os.path.join(utils.getLabelFusionDataDir(), filename)

            polyData = ioUtils.readPolyData(filename)
            color = self.getColorFromIndex(objName)
            obj = vis.showPolyData(polyData, name=objName, parent=folder, color=color)
            self.storedColors[objName] = color

            objToWorld = transformUtils.transformFromPose(*data['pose'])
            self.objectToWorld[objName] = objToWorld
            obj.actor.SetUserTransform(objToWorld)

    def setupImage(self, imageNumber, saveColorLabeledImages=False, saveLabeledImages=False, savePoses=False):

        """
        Loads the given imageNumber as background.
        Also updates the poses of the objects to match the image
        """
        baseName = utils.getImageBasenameFromImageNumber(imageNumber, self.pathDict)
        imageFilename = baseName + "_rgb.png"
        if not os.path.exists(imageFilename):
            return False

        utimeFile = open(baseName + "_utime.txt", 'r')
        utime = int(utimeFile.read())

        # update camera transform
        cameraToCameraStart = self.getCameraPoseAtUTime(utime)
        t = cameraToCameraStart
        vis.updateFrame(t, 'camera pose')
        setCameraTransform(self.view.camera(), t)

        cameraPose = om.findObjectByName('camera pose')
        cameraPose.setProperty('Visible', False)

        if saveColorLabeledImages:
            self.loadBackgroundImage(imageFilename)
            #self.view.forceRender() # render it again
            self.captureColorImage(baseName + '_color_labels.png')

        if saveLabeledImages:
            self.captureLabelImage(baseName + '_labels.png')

        if savePoses:
            self.saveObjectPoses(imageFilename.replace("_rgb.png", "_labels.png"), cameraToCameraStart, baseName)

        return True

    def saveObjectPoses(self, imageFilename, cameraToCameraStart, baseName):
        # count pixels
        img = scipy.misc.imread(imageFilename)
        assert img.dtype == np.uint8
        
        if img.ndim in  (3, 4):
            img = img[:,:,0]
        else:
            assert img.ndim == 2

        labels, counts = np.unique(img, return_counts=True)
        labelToCount = dict(zip(labels, counts))

        num_pixels_per_class = np.array([])

        for i in xrange(0, img.max()+1):
            num_pixels = labelToCount.get(i, 0)
            num_pixels_per_class = np.append(num_pixels_per_class, num_pixels)

        pose_file_name = baseName + "_poses.yaml"
        target = open(pose_file_name, 'w')
        print 'writing:', pose_file_name

        # iterate through each class with 1 or more pixel and save pose...
        for index, val in enumerate(num_pixels_per_class):
            if index == 0:
                # don't save for background class
                continue 
            if val > 0:
                cameraStartToCamera = cameraToCameraStart.GetLinearInverse()
                objectName = utils.getObjectName(self.objectData, index)
                target.write(objectName + ":")
                target.write("\n")
                target.write("  label: " + str(index))
                target.write("\n")
                target.write("  num_pixels: " + str(val))
                target.write("\n")
                objToCameraStart = self.objectToWorld[objectName]
                objToCamera = transformUtils.concatenateTransforms([objToCameraStart, cameraStartToCamera])
                pose = transformUtils.poseFromTransform(objToCamera)
                poseAsList = [pose[0].tolist(), pose[1].tolist()]
                target.write("  pose: " + str(poseAsList))
                target.write("\n")

        target.close()
                
    def renderAndSaveLabeledImages(self):
        imageNumber = 1
        while(self.setupImage(imageNumber, saveColorLabeledImages=True, saveLabeledImages=False, savePoses=False)):
            imageNumber += 1

        imageNumber = 1
        while(self.setupImage(imageNumber, saveColorLabeledImages=False, saveLabeledImages=True, savePoses=True)):
            imageNumber += 1


def getCameraTransform(camera):
    return transformUtils.getLookAtTransform(
              camera.GetFocalPoint(),
              camera.GetPosition(),
              camera.GetViewUp())

def setCameraTransform(camera, transform):
    '''Set camera transform so that view direction is +Z and view up is -Y'''
    origin = np.array(transform.GetPosition())
    axes = transformUtils.getAxesFromTransform(transform)
    camera.SetPosition(origin)
    camera.SetFocalPoint(origin+axes[2])
    camera.SetViewUp(-axes[1])

def focalLengthToViewAngle(focalLength, imageHeight):
    '''Returns a view angle in degrees that can be set on a vtkCamera'''
    return np.degrees(2.0 * np.arctan2(imageHeight/2.0, focalLength))


def viewAngleToFocalLength(viewAngle, imageHeight):
    '''Returns the focal length given a view angle in degrees from a vtkCamera'''
    return (imageHeight/2.0)/np.tan(np.radians(viewAngle/2.0))


def setCameraIntrinsics(view, principalX, principalY, focalLength):
    '''Note, call this function after setting the view dimensions'''

    imageWidth = view.width
    imageHeight = view.height

    wcx = -2*(principalX - float(imageWidth)/2) / imageWidth
    wcy =  2*(principalY - float(imageHeight)/2) / imageHeight
    viewAngle = focalLengthToViewAngle(focalLength, imageHeight)

    camera = view.camera()
    camera.SetWindowCenter(wcx, wcy)
    camera.SetViewAngle(viewAngle)


def setCameraInstrinsicsAsus(view):
    principalX = 320.0
    principalY = 240.0
    focalLength = 528.0
    setCameraIntrinsics(view, principalX, principalY, focalLength)

#######################################################################################


