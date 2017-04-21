import os
from director import ioUtils
from director import actionhandlers
from director import screengrabberpanel as sgp
import scipy.misc

def loadCommandLineDataFiles():
    for filename in commandLineArgs.data_files:
        actionhandlers.onOpenFile(filename)


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
    viewOptions.setProperty('Background color', [0.9,0.9,0.9])
    #viewOptions.setProperty('Background color 2', [0,0,0])

    view.renderer().TexturedBackgroundOn()

    for obj in om.findObjectByName('data files').children():
        obj.actor.GetProperty().LightingOn()
        obj.setProperty('Color', _storedColors[obj.getProperty('Name')])
    view.forceRender()


def captureColorImage(filename):

    enableLighting()
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


#######################################################################################


om.findObjectByName('stand.vtp').setProperty('Color', [1,0,0])
om.findObjectByName('engine_crop.vtp').setProperty('Color', [0.6,0.6,0.65])
om.findObjectByName('engine_crop.vtp').actor.GetProperty().SetSpecular(0.2)

img = ioUtils.readImage('/home/pat/Desktop/IMG_4655.JPG')
tex = vtk.vtkTexture()
tex.SetInput(img)
view.renderer().SetBackgroundTexture(tex)
view.renderer().TexturedBackgroundOn()

gridObj.setProperty('Visible', False)

view.setFixedSize(480, 360)
view.camera().SetViewAngle(45)
view.resetCamera()


disableLighting()
enableLighting()


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

app.quit()
