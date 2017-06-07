import os
import numpy as np
import scipy.misc


# Call this script from the /train folder to compute label weights for training set

counter = 0

num_pixels_per_class = np.zeros(12)

def addFrequencyInFile(filename_full_path):
	global num_pixels_per_class
	img = scipy.misc.imread(filename_full_path)
	assert img.dtype == np.uint8

	# extract one channel
	if img.ndim in  (3, 4):
	    img = img[:,:,0]
	else:
	    assert img.ndim == 2
	    print 'num channels: 1'

	labels, counts = np.unique(img, return_counts=True)
	labelToCount = dict(zip(labels, counts))

	for i in xrange(0, img.max()+1):
		num_pixels = labelToCount.get(i, 0)
		print 'class %d: %d pixels' % (i, num_pixels)
		num_pixels_per_class[i] += num_pixels



def crawlDir(dir_local):
    global counter
    cwd = os.getcwd()
    path_to_folder = cwd + "/" + dir_local
   
    for root, dirs, files in os.walk(path_to_folder):
        for filename in sorted(files):
            filename_full_path = os.path.join(root, filename)
            if filename_full_path.endswith("labels.png") and not filename_full_path.endswith("color_labels.png"):
            	print filename_full_path
            	addFrequencyInFile(filename_full_path)
            	counter+=1
            

def computeAndPrintWeights():
	print 'median frequency labeling:'
	median_frequency = np.median(num_pixels_per_class)
	for i in range(len(num_pixels_per_class)):
		if num_pixels_per_class[i] == 0:
			print 'class_weighting:', 0.0
		else: 
			print 'class_weighting:', median_frequency/num_pixels_per_class[i]

crawlDir("") # empty string gets everything in current dir
computeAndPrintWeights()

print "counter ", counter

