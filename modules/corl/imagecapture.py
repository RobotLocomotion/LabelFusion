"""
This class consumes and lcmlog, extracts the images and saves them
to png
"""
import utils as CorlUtil
import os

# director imports
import director.vtkAll as vtk
from director import filterUtils
from director import lcmUtils
from director import cameraview

# lcm imports
import bot_core as lcmbotcore



class ImageCapture(object):

    def __init__(self, imageManager, fileSaveLocation,
                 cameraName = "OPENNI_FRAME_LEFT", setupCallback=False):
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

    def saveImage(self, extension="rgb.png"):
        # construct filename where this image will be saved
        baseFilename = CorlUtil.convertImageIDToPaddedString(self.counter) + "_"
        baseFilename = os.path.join(self.fileSaveLocation, baseFilename)
        rgbFilename = baseFilename + extension
        utimeFilename = baseFilename + "utime.txt"
        self.counter += 1

        # get the image and it's utime
        self.imageManager.updateImages()
        image = self.imageManager.getImage(self.cameraName)
        utime = self.imageManager.getUtime(self.cameraName)
        image = filterUtils.flipImage(image)
        print 'writing:', rgbFilename
        ImageCapture.writeImage(image, rgbFilename)

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
    def readFromLogFile(lcmLogFilename, fileSaveLocation, channelName="OPENNI_FRAME",
                        cameraName="OPENNI_FRAME_LEFT"):
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

        # first construct imageManager object
        imageManager = cameraview.ImageManager()
        imageManager.queue.addCameraStream(channelName, cameraName, lcmbotcore.images_t.LEFT)
        imageManager.addImage(cameraName)

        # open the lcm log
        imageManager.queue.openLCMFile(lcmLogFilename)

        imageCapture = ImageCapture(imageManager, fileSaveLocation,
                 cameraName = "OPENNI_FRAME_LEFT", setupCallback=False)

        while imageManager.queue.readNextImagesMessage():
            imageCapture.saveImage()

        print "reached end of lcm log"
        return

def captureImages(logFolder):
    corlPaths = CorlUtil.getFilenames(logFolder)
    ImageCapture.readFromLogFile(corlPaths['lcmlog'], corlPaths['images'])


def test():
    captureImages("logs/moving-camera")

