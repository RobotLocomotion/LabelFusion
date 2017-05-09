import os
import numpy as np
import yaml

from director import vtkNumpy as vnp
from director import ioUtils
import director.vtkAll as vtk
from director import actionhandlers
from director import screengrabberpanel as sgp
from director import transformUtils
from director import visualization as vis

import utils as cutils
import scipy.misc


class RenderTrainingImages(object):

    def __init__(self, globalsDict, pathDict):
        """

        :param globalsDict: globalsDict of all globals in director
        :param pathDict: dictionary storing all the relevant paths
        """
        self.globalsDict = globalsDict
        self.pathDict = pathDict
        self.storedColors = {}
        self.objectToWorld = dict()
        self.initialize()

    def initialize(self):
        self.loadCameraPoses()
        self.loadObjectMeshes()


        backgroundImageFilename = cutils.getImageBasenameFromImageNumber(1, self.pathDict) + "_rgb.png"

        self.loadBackgroundImage(backgroundImageFilename)
        self.globalsDict['gridObj'].setProperty('Visible', False)

        view = self.globalsDict['view']
        view.setFixedSize(640, 480)
        setCameraInstrinsicsAsus(view)
        cameraToWorld = cutils.getDefaultCameraToWorld()
        setCameraTransform(view.camera(), cameraToWorld)
        view.forceRender()
        self.enableLighting()


    def disableLighting(self):
        view = self.globalsDict['view']
        viewOptions = self.globalsDict['viewOptions']
        om = self.globalsDict['om']

        viewOptions.setProperty('Gradient background', False)
        viewOptions.setProperty('Orientation widget', False)
        viewOptions.setProperty('Background color', [0, 0, 0])

        view.renderer().TexturedBackgroundOff()

        for obj in om.findObjectByName('data files').children():
            objName = obj.getProperty('Name')
            objLabel = cutils.getObjectLabel(objName)
            obj.actor.GetProperty().LightingOff()
            self.storedColors[obj.getProperty('Name')] = list(obj.getProperty('Color'))
            obj.setProperty('Color', [objLabel / 255.0] * 3)
        view.forceRender()

    def enableLighting(self):
        view = self.globalsDict['view']
        viewOptions = self.globalsDict['viewOptions']
        om = self.globalsDict['om']

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
        view = self.globalsDict['view']
        self.enableLighting()
        print 'writing:', filename
        im = sgp.saveScreenshot(view, filename, shouldWrite=True)
        return im


    def captureLabelImage(self, filename):
        view = self.globalsDict['view']
        self.disableLighting()
        im = sgp.saveScreenshot(view, filename, shouldWrite=False)

        if filename is not None:
            img = vnp.getNumpyFromVtk(im, 'ImageScalars')
            assert img.dtype == np.uint8

            img.shape = (im.GetDimensions()[1], im.GetDimensions()[0], 3)
            img = np.flipud(img)

            img = img[:,:,0]
            scipy.misc.imsave(filename, img)

        return im


    def saveImages(self, baseName):
        self.captureColorImage(baseName + '_color_labels.png')
        self.captureLabelImage(baseName + '_labels.png')


    def saveImagesTest(self):
        baseName = cutils.getImageBasenameFromImageNumber(1, self.pathDict)
        self.saveImages(baseName)
        self.enableLighting()


    def loadBackgroundImage(self, filename):
        view = self.globalsDict['view']
        img = ioUtils.readImage(filename)
        tex = vtk.vtkTexture()
        tex.SetInput(img)
        view.renderer().SetBackgroundTexture(tex)
        view.renderer().TexturedBackgroundOn()


    # TODO(manuelli): Not sure what this does, was just copy and pasted
    def moveCameraAndRenderImages(self):

        view = self.globalsDict['view']
        imageCounter = 0
        cam = view.camera()
        azSteps = 10
        elSteps = 4

        outDir = 'images'
        if not os.path.isdir(outDir):
            os.makedirs(outDir)

        for _ in xrange(elSteps):
            cam.Elevation(10)
            for _ in xrange(azSteps):
                cam.Azimuth(360.0/azSteps)

                self.saveImages(os.path.join(outDir, 'scene_%05d' % imageCounter))
                imageCounter += 1


    def loadCameraPoses(self):
        data = np.loadtxt(self.pathDict['cameraPoses'])
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


    def loadObjectMeshes(self):
        om = self.globalsDict['om']
        objData = cutils.getResultsConfig()['object-registration']
        dataDir = cutils.getCorlDataDir()

        stream = file(self.pathDict['registrationResult'])
        registrationResult = yaml.load(stream)

        cameraToWorld = cutils.getDefaultCameraToWorld()

        folder = om.getOrCreateContainer('data files')
        for objName, data in registrationResult.iteritems():

            filename = data['filename']
            if len(filename) == 0:
                filename = cutils.getObjectMeshFilename(objName)

            polyData = ioUtils.readPolyData(filename)
            color = vis.getRandomColor()
            obj = vis.showPolyData(polyData, name=objName, parent=folder, color=color)
            self.storedColors[objName] = color

            objToWorld = transformUtils.transformFromPose(*data['pose'])
            self.objectToWorld[objName] = objToWorld
            #objToCamera = transformUtils.concatneateTransforms([objToWorld, cameraToWorld.GetLinearInverse()])
            obj.actor.SetUserTransform(objToWorld)

    def setupImage(self, imageNumber, saveLabeledImages=False):
        """
        Loads the given imageNumber as background.
        Also updates the poses of the objects to match the image
        """
        baseName = cutils.getImageBasenameFromImageNumber(imageNumber, self.pathDict)
        imageFilename = baseName + "_rgb.png"
        if not os.path.exists(imageFilename):
            return False

        utimeFile = open(baseName + "_utime.txt", 'r')
        utime = int(utimeFile.read())

        # update camera transform
        cameraToCameraStart = self.getCameraPoseAtUTime(utime)
        t = transformUtils.concatenateTransforms([cameraToCameraStart, cutils.getDefaultCameraToWorld()])
        vis.updateFrame(t, 'camera pose')
        setCameraTransform(self.globalsDict['view'].camera(), t)

        cameraPose = self.globalsDict['om'].findObjectByName('camera pose')
        cameraPose.setProperty('Visible', False)

        self.loadBackgroundImage(imageFilename)
        self.globalsDict['view'].forceRender() # render it again

        if saveLabeledImages:
            self.saveImages(baseName)

        return True


    # def updateObjectPoses(self, imageNumber):
    #     baseName = cutils.getImageBasenameFromImageNumber(imageNumber, self.pathDict)
    #     utimeFile = open(baseName + "_utime.txt", 'r')
    #     utime = int(utimeFile.read())
    #
    #     (pos, quat) = self.getCameraPose(utime)
    #     cameraToCameraStart = transformUtils.transformFromPose(pos,quat)
    #     cameraStartToCameraCurrent = cameraToCameraStart.GetLinearInverse()
    #
    #     # iterate through objects updating their transforms
    #     for obj in om.findObjectByName('data files').children():
    #         # objToWorldNew = objToWorld
    #         objToWorld = self.objectToWorld[obj.getProperty('Name')]
    #         objToWorldNew = transformUtils.concatneateTransforms([objToWorld, cameraStartToCameraCurrent])
    #         obj.SetUserTransform(objToWorldNew)

    def renderAndSaveLabeledImages(self):
        imageNumber = 1
        while(self.setupImage(imageNumber, saveLabeledImages=True)):
            imageNumber += 1
        

    @staticmethod
    def makeDefault(globalsDict, logFolder="logs/moving-camera"):
        pathDict = cutils.getFilenames("logs/moving-camera")
        rti = RenderTrainingImages(globalsDict, pathDict)
        globalsDict['renderTrainingImages'] = rti
        return rti



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


