"""
This class implements some data augmentation techniques for SegNet training

TODO: do resizing at the same time as augmentation
TODO: store labels and images in separate directories so you dont have to do this before putting the data trhough Keras data augmentation

Keras library trasnfromations
can do all the data transformations at once! More info at - https://keras.io/preprocessing/image/   https://blog.keras.io/building-powerful-image-classification-models-using-very-little-data.html

dependancies= PIL, TensorFlow, Keras

seems its also possible to do augmentation on the fly with custom Caffe Training data layer- have not tested it though https://github.com/NVIDIA/DIGITS/issues/1034


Other basic PIL library transformations to try
1.combinatorial cropping
2.random cropping
3.horizontalflipping
4.rotations
5.color jittering
6.lighting noise
"""

from labelfusion import utils as LabelFusionUtils
import os
import random
import keras
from keras.preprocessing.image import ImageDataGenerator

import director.vtkAll as vtk
from director import filterUtils
from PIL import Image, ImageFilter
import glob, os, shutil
import itertools


class DataAugmentation(object):

    def __init__(self, img_target_size = (256, 256), params = dict(rotation_range=90.,
                                                        width_shift_range=0.1,
                                                        height_shift_range=0.1,
                                                        zoom_range=0.2)):
        self.target_size = img_target_size
        self.data_gen_args = params

   
    def augmentWithKeras(self,log_folder):
        d = LabelFusionUtils.getFilenames(log_folder)
        path_to_img = d["images"]
        labels = glob.iglob(os.path.join(path_to_img, "*labels.png"))
        images = glob.iglob(os.path.join(path_to_img, "*rgb.png"))
        #create two directories for generators
        lab_dir = "labels_tmp/"
        img_dir = "images_tmp/"
        lab_dir_full_path = lab_dir+"images"
        img_dir_full_path = img_dir + "images"
        os.makedirs(lab_dir_full_path)
        os.makedirs(img_dir_full_path)
        for label, pic in itertools.izip(labels,images):
            shutil.copy2(label, lab_dir_full_path)
            shutil.copy2(pic, img_dir_full_path)

        self.generateAugmentedImages(img_dir,lab_dir,path_to_img) #note overwrites aug-prefixed images in folder
        shutil.rmtree(lab_dir)
        shutil.rmtree(img_dir)


    def generateAugmentedImages(self,images_dir, labels_dir, save_dir):
        image_datagen = ImageDataGenerator(**self.data_gen_args)
        mask_datagen = ImageDataGenerator(**self.data_gen_args)
        seed = 1
        # image_datagen.fit(images, augment=True, seed=seed)
        # mask_datagen.fit(masks, augment=True, seed=seed)

        """
        next 2 blocks of code are typically used as generator for model training in keras. Instead you can hack the generator by iterating over batches and using the save_to_dir param to save augmented_images.
        """
        i = 0
        num_batches = 20
        for batch in image_datagen.flow_from_directory(
        images_dir,
        class_mode=None,
        seed=seed,
        save_to_dir = save_dir,
        save_format = "png",
        save_prefix = "aug_images",
        target_size = self.target_size):
            i+=1
            if i>num_batches:
                break

        i = 0
        for batch in mask_datagen.flow_from_directory(
        labels_dir,
        class_mode=None,
        seed=seed,
        save_to_dir = save_dir,
        save_format = "png",
        save_prefix = "aug_label",
        target_size = self.target_size):
            i+=1
            if i>num_batches:
                break





""" io functions and simple PIL transformations for augmentations

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

 
    def generateFileNames():
        baseFilename = LabelFusionUtils.convertImageIDToPaddedString(self.counter) + "_"
        baseFilename = os.path.join(self.fileSaveLocation, baseFilename)
        rgbFilename = baseFilename + "rbg.png"
        labelFilename = baseFilename + "label.png"

        utimeFilename = baseFilename + "utime.txt"
        self.counter += 1
        return (rgbFilename,labelFilename)


    def rotate(image,degrees):
        return image.transpose(degrees)
    
    def blur(image, blur_param):
        #might need to refine edge sfor pixelwise labeling part
        return image.filter(ImageFilter.GassianBlur(blur_param))

    def randomCrop(labeled, rgb, image, width, height):
        im_width, im_height = im.size
        #cropping logic
        return (labeled.resize((im_width,im_height)),rgb.resize((im_width,im_height)))
"""
