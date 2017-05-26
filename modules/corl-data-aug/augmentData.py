"""
This class implements a some data augmentation techniques for SegNet
TODO: do resizing at the same time

Basic PIL library transformations
1.combinatorial cropping
2.random cropping
3.horizontalflipping
4.rotations
5.color jittering
6.lighting noise

Keras library trasnfromations
"""
import utils as CorlUtil
import os
import random

# director imports
import keras
import director.vtkAll as vtk
from director import filterUtils
from PIL import Image, ImageFilter



class DataAugmentation(object):

    def __init__(self, location, params):
        self.location = location
        self.counter = getTrainingCount(location)
        self.data_gen_args = dict(featurewise_center=True,
                     featurewise_std_normalization=True,
                     rotation_range=90.,
                     width_shift_range=0.1,
                     height_shift_range=0.1,
                     zoom_range=0.2)

#IO
    def saveImage(self, labeled_image, rgb_image):
       
    	rgbFilename,labelFilename = generateFileNames()
        print 'writing:', rgbFilename
        rbg_image.save(rgbFilename, 'png')
        labeled_image.save(labelFilename, 'png')
        # now save the utime
        print 'writing:', utimeFilename
        text_file = open(utimeFilename, "w")
        text_file.write(str(utime))
        text_file.close()

    @staticmethod
    def getTrainingCount():
    	pass

    def generateFileNames():
    	baseFilename = CorlUtil.convertImageIDToPaddedString(self.counter) + "_"
        baseFilename = os.path.join(self.fileSaveLocation, baseFilename)
        rgbFilename = baseFilename + "rbg.png"
        labelFilename = baseFilename + "label.png"

        utimeFilename = baseFilename + "utime.txt"
        self.counter += 1
        return (rgbFilename,labelFilename)

#augmentation PIL
	def rotate(image,degrees):
		return image.transpose()
	
	def blur(image, blur_param):
		#might need to refine edgesfor pixelwise labeling part
		return image.filter(ImageFilter.GassianBlur(blur_param))

	def randomCrop(labeled, rgb, image, width, height):
		im_width, im_height = im.size
		#cropping logic
		return (labeled.resize((im_width,im_height)),rgb.resize((im_width,im_height)))

#augmentation keras
	#find workaround for having to move files to 2 directories

	def augmentWithKeras(images_dir, labels_dir):
		image_datagen = ImageDataGenerator(**self.data_gen_args)
		mask_datagen = ImageDataGenerator(**self.data_gen_args)
		seed = 1
		image_datagen.fit(images, augment=True, seed=seed)
		mask_datagen.fit(masks, augment=True, seed=seed)

		image_generator = image_datagen.flow_from_directory(
   		'data/images',
    	class_mode=None,
    	seed=seed,
    	save_to_dir = "Documents",
    	save_format = "png",
    	save_prefix = "prefix")

		mask_generator = mask_datagen.flow_from_directory(
    	'data/masks',
    	class_mode=None,
    	seed=seed,
    	save_to_dir = "Documents",
    	save_format = "png",
    	save_prefix = "prefix")


