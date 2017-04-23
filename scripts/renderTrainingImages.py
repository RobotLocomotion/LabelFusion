'''
Usage:

  drake-visualizer --script scripts/renderTrainingImages.py

Outputs test_color.png and test_labels.png.  You can plot
the label image with:

  python scripts/plotLabels test_labels.png
'''

import os
from director import ioUtils
from director import actionhandlers
from director import screengrabberpanel as sgp
import corl.utils as cutils
import scipy.misc



_storedColors = {}

def disableLighting():

    viewOptions.setProperty('Gradient background', False)
    viewOptions.setProperty('Orientation widget', False)
    viewOptions.setProperty('Background color', [0,0,0])

    view.renderer().TexturedBackgroundOff()

    for i, obj in enumerate(om.findObjectByName('data files').children()):
        objLabel = i+1
        obj.actor.GetProperty().LightingOff()
        _storedColors[obj.getProperty('Name')] = list(obj.getProperty('Color'))
        obj.setProperty('Color', [objLabel/255.0]*3)
    view.forceRender()


def enableLighting():

    viewOptions.setProperty('Gradient background', False)
    viewOptions.setProperty('Orientation widget', False)
    viewOptions.setProperty('Background color', [0.0,0.0,0.0])

    if view.renderer().GetBackgroundTexture():
        view.renderer().TexturedBackgroundOn()

    for obj in om.findObjectByName('data files').children():
        obj.actor.GetProperty().LightingOn()
        obj.setProperty('Color', _storedColors[obj.getProperty('Name')])
    view.forceRender()


def captureColorImage(filename):
    enableLighting()
    print 'writing:', filename
    im = sgp.saveScreenshot(view, filename, shouldWrite=True)
    return im


def captureLabelImage(filename):

    disableLighting()
    im = sgp.saveScreenshot(view, filename, shouldWrite=False)

    if filename is not None:
        img = vnp.getNumpyFromVtk(im, 'ImageScalars')
        assert img.dtype == np.uint8

        img.shape = (im.GetDimensions()[1], im.GetDimensions()[0], 3)
        img = np.flipud(img)

        img = img[:,:,0]
        scipy.misc.imsave(filename, img)


    return im


def saveImages(baseName):
    captureColorImage(baseName + '_color.png')
    captureLabelImage(baseName + '_labels.png')


def loadBackgroundImage(filename):
    img = ioUtils.readImage(filename)
    tex = vtk.vtkTexture()
    tex.SetInput(img)
    view.renderer().SetBackgroundTexture(tex)
    view.renderer().TexturedBackgroundOn()

def moveCameraAndRenderImages():

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

            saveImages(os.path.join(outDir, 'scene_%05d' % imageCounter))
            imageCounter += 1


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


def loadCameraPoses():
    filename = os.path.join(getCorlDataDir(), getResultsConfig()['camera-poses'])
    data = np.loadtxt(filename)
    poseTimes = np.array(data[:,0]*1e6, dtype=int)
    poses = []
    for pose in data[:,1:]:
        pos = pose[:3]
        quat = pose[6], pose[3], pose[4], pose[5] # quat data from file is ordered as x, y, z, w
        poses.append((pos, quat))
    return poses


def loadObjectMeshes():

    objData = cutils.getResultsConfig()['object-registration']
    dataDir = cutils.getCorlDataDir()

    cameraToWorld = cutils.getDefaultCameraToWorld()

    folder = om.getOrCreateContainer('data files')
    for data in objData:

        filename = os.path.join(dataDir, data['filename'])
        polyData = ioUtils.readPolyData(filename)
        obj = vis.showPolyData(polyData, name=data['name'], parent=folder, color=vis.getRandomColor())

        objToWorld = transformUtils.transformFromPose(*data['pose'])
        #objToCamera = transformUtils.concatneateTransforms([objToWorld, cameraToWorld.GetLinearInverse()])
        obj.actor.SetUserTransform(objToWorld)



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



loadObjectMeshes()

cameraToWorld = cutils.getDefaultCameraToWorld()

rgbImage = os.path.join(cutils.getCorlDataDir(), 'training-images/moving-camera/0000001_rgb.png')
loadBackgroundImage(rgbImage)
gridObj.setProperty('Visible', False)

view.setFixedSize(640, 480)
setCameraInstrinsicsAsus(view)
setCameraTransform(view.camera(), cameraToWorld)

view.forceRender()
disableLighting()

saveImages('./test')
enableLighting()

#app.quit()
