"""
This class consumes and lcmlog, extracts the images and saves them
to png
"""
import utils as CorlUtil
import os
# director imports
import director.vtkAll as vtk
from director import filterUtils

class ImageCapture(object):

    def __init__(self, imageManager, fileSaveLocation,
                 cameraName = "OPENNI_FRAME_LEFT"):
        self.imageManager = imageManager
        self.fileSaveLocation = fileSaveLocation
        self.cameraName = cameraName
        self.counter = 1

    def saveImage(self, extension="rbg.png"):
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
        ImageCapture.writeImage(image, rgbFilename)

        # now save the utime
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
