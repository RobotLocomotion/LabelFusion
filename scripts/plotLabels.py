import os
import sys
import numpy as np
import scipy.misc
import matplotlib.pyplot as plt


filename = sys.argv[1]
print 'reading:', filename

# load image
img = scipy.misc.imread(filename)

assert img.dtype == np.uint8



print 'width x height: %d x %d' % (img.shape[1], img.shape[0])
print 'shape:', img.shape
print 'ndim:', img.ndim

# extract one channel
if img.ndim in  (3, 4):
    print 'num channels:', img.shape[2]
    img = img[:,:,0]
else:
    assert img.ndim == 2
    print 'num channels: 1'

print 'min/max pixel values: %d, %d' % (img.min(), img.max())

labels, counts = np.unique(img, return_counts=True)
labelToCount = dict(zip(labels, counts))

print 'num unique labels:', len(labels)
print 'labels:', labels

num_pixels_per_class = np.array([])

for i in xrange(0, img.max()+1):
	num_pixels = labelToCount.get(i, 0)
	print 'class %d: %d pixels' % (i, num_pixels)
	num_pixels_per_class = np.append(num_pixels_per_class, num_pixels)

print 'median frequency labeling:'
median_frequency = np.median(num_pixels_per_class)
for i in xrange(0, img.max()+1):
	print 'class_weighting:', median_frequency/num_pixels_per_class[i]

#execfile(os.environ['PYTHONSTARTUP'])


# plot

fig = plt.figure()

a = fig.add_subplot(1,2,1)
plt.imshow(img)
a.set_title('Labels')
plt.colorbar(ticks=labels, orientation ='horizontal', label='labels')

a = fig.add_subplot(1,2,2)
plt.hist(img.ravel(), bins=range(img.min(), img.max()+2))
a.set_title('Histogram')


plt.show()

