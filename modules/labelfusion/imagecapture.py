"""
This class consumes and lcmlog, extracts the images and saves them
to png
"""
import os

# director imports
import director.vtkAll as vtk
from director import filterUtils
from director import lcmUtils
from director import cameraview
import bot_core as lcmbotcore

from . import utils


class ImageCapture(object):

    def __init__(self, imageManager, fileSaveLocation,
                 cameraName="OPENNI_FRAME_LEFT", setupCallback=False):
        self.imageManager = imageManager
        self.fileSaveLocation = fileSaveLocation
        self.cameraName = cameraName
        self.counter = 1
        self.initialized = False

        if setupCallback:
            self.setupCallback()

    def setupCallback(self):
        lcmUtils.addSubscriber("OPENNI_FRAME", lcmbotcore.images_t(),
                               self.onImageMessage)

    def saveImage(self, saveUtime=True, extension="rgb.png"):
        # construct filename where this image will be saved
        baseFilename = utils.convertImageIDToPaddedString(self.counter) + "_"
        baseFilename = os.path.join(self.fileSaveLocation, baseFilename)
        imageFilename = baseFilename + extension
        self.counter += 1

        # get the image and it's utime
        self.imageManager.updateImages()
        image = self.imageManager.getImage(self.cameraName)
        image = filterUtils.flipImage(image)
        print 'writing:', imageFilename
        ImageCapture.writeImage(image, imageFilename)

        if saveUtime:
            utime = self.imageManager.getUtime(self.cameraName)
            utimeFilename = baseFilename + "utime.txt"
            # now save the utime
            print 'writing:', utimeFilename
            text_file = open(utimeFilename, "w")
            text_file.write(str(utime))
            text_file.close()

    @staticmethod
    def writeImage(image, filename):
        """
        Writes given image to filename
        :param image: vtkImageData
        :param filename: full path to file where image should be saved
        :return:
        """
        writer = vtk.vtkPNGWriter()
        writer.SetInput(image)
        writer.SetFileName(filename)
        writer.Write()

    def onImageMessage(self, msg):
        """
        Just a trigger to save message
        :param msg:
        :return:
        """
        if not self.initialized:
            self.initialized = True
            return

        self.saveImage()


    @staticmethod
    def readFromLogFile(lcmLogFilename, fileSaveLocation, channelName="OPENNI_FRAME", cameraName="OPENNI_FRAME_LEFT", saveDepth=False):
        """
        Reads from lcmlog located at filename. Goes through each
        images_t() message on OPENNI_FRAME channel and saves it
        as a png in fileSaveLocation
        :param filename: Name of lcmlogfile
        :return:
        """

        # check if fileSaveLocation is an existing directory, if not create it.
        if not os.path.isdir(fileSaveLocation):
            os.makedirs(fileSaveLocation)


        # construct imageManager object
        imageManager = cameraview.ImageManager()
        if saveDepth:
            imageManager.queue.addCameraStream(channelName, cameraName, lcmbotcore.images_t.DEPTH_MM_ZIPPED)
        else:
            imageManager.queue.addCameraStream(channelName, cameraName, lcmbotcore.images_t.LEFT)
        imageManager.addImage(cameraName)

        # open the lcm log
        imageManager.queue.openLCMFile(lcmLogFilename)

        imageCapture = ImageCapture(imageManager, fileSaveLocation,
                 cameraName=cameraName, setupCallback=False)

        while imageManager.queue.readNextImagesMessage():
            if saveDepth:
                imageCapture.saveImage(saveUtime=False, extension="depth.png")
            else:
                imageCapture.saveImage(extension="rgb.png")

        print "reached end of lcm log"
        return

def captureImages(logFolder):
    corlPaths = utils.getFilenames(logFolder)
    ImageCapture.readFromLogFile(corlPaths['lcmlog'], corlPaths['images'], cameraName="OPENNI_FRAME_DEPTH_MM_ZIPPED", saveDepth=True)
    ImageCapture.readFromLogFile(corlPaths['lcmlog'], corlPaths['images'], cameraName="OPENNI_FRAME_LEFT")


def test():
    captureImages("logs/moving-camera")

