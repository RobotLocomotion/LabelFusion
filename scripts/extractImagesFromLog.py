import os
import argparse

import corl.utils as CorlUtils
import corl.imagecapture

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--logFolder', type=str, dest='logFolder', help='location of top level folder for this log, relative to CorlDev/data')
    args = parser.parse_args()
    print "logFolder = ", args.logFolder
    corl.imagecapture.captureImages(args.logFolder)

