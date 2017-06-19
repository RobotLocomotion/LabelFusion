'''
usage:

python scripts/computeIntersectionOverUnion image1.png image2.png

'''

import os
import sys
import numpy as np
import scipy.misc
import matplotlib.pyplot as plt


def computeIntersectionOverUnion(img1, img2, plotClassId=None):
    '''
    Given two images as numpy ndarray WxH and dtype uint8, this function
    computes the pixelwise intersection/union for each class id found
    in the given images.

    Returns a dictionary where keys are class id and values are class IoU.
    '''

    images = [img1, img2]

    # images must be shape WxH of data type uint8
    for img in images:
        assert img.dtype == np.uint8
        assert img.ndim == 2

    classIds = np.unique(np.hstack(images))
    classIoU = {}

    for classId in classIds:

        classImages = [img == classId for img in images]
        union = np.logical_or(*classImages)
        intersection = np.logical_and(*classImages)

        classIoU[classId] = np.sum(intersection) / float(np.sum(union))

        if classId == plotClassId:

            fig = plt.figure()
            subplot = fig.add_subplot(2,3,1)
            plt.imshow(classImages[0])
            subplot.set_title('image 1 class %d' % classId)

            subplot = fig.add_subplot(2,3,2)
            plt.imshow(classImages[1])
            subplot.set_title('image 2 class %d' % classId)

            subplot = fig.add_subplot(2,3,4)
            plt.imshow(intersection)
            subplot.set_title('class %d intersection' % classId)

            subplot = fig.add_subplot(2,3,5)
            plt.imshow(union)
            subplot.set_title('class %d union' % classId)

            subplot = fig.add_subplot(2,3,6)
            plt.imshow(intersection.astype(int) + union.astype(int))
            subplot.set_title('class %d IoU' % classId)

            plt.suptitle('class %d IoU = %.5f' % (classId, classIoU[classId]), fontsize=24)
            plt.show()

    return classIoU


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print 'usage: %s <image1.png> <image2.png>' % sys.argv[0]
        sys.exit(1)

    filenames = [sys.argv[1], sys.argv[2]]
    images = [scipy.misc.imread(filename) for filename in filenames]
    classIoU = computeIntersectionOverUnion(images[0], images[1], plotClassId=0)

    for classId in sorted(classIoU.keys()):
        print 'class %d IoU:' % classId, classIoU[classId]

    meanClassIoU = np.mean(classIoU.values())
    print 'mean classIoU:', meanClassIoU
