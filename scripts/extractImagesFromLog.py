'''
Usage:

directorPython scripts/extractImagesFromLog.py --logFolder logs/moving-camera --bot-config $SPARTAN_SOURCE_DIR/apps/iiwa/iiwaManip.cfg
'''

import os
import argparse

from director import drcargs

import corl.utils as CorlUtils
import corl.imagecapture

if __name__ == '__main__':

	print os.getcwd()
	if os.path.isfile(os.path.join(os.getcwd(), "images/0000000001_rgb.png")):
		print ""
		print "Already extracted images? Skipping..."
		print "To re-extract, either move or delete ./images/"
		print ""
		quit()

	parser = drcargs.getGlobalArgParser().getParser()
	parser.add_argument('--logFolder', type=str, dest='logFolder', help='location of top level folder for this log, relative to CorlDev/data')
	args = parser.parse_args()
	print "logFolder = ", args.logFolder
	corl.imagecapture.captureImages(args.logFolder)

