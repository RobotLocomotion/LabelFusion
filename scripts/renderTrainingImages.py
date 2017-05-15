'''
Usage:

  directorPython --script scripts/renderTrainingImages.py

Optionally you can pass --logFolder <logFolder> on the command line
where <logFolder> is the path to the lcm log folder relative to the
data folder.  For example: --logFolder logs/moving-camera
'''
import sys
import argparse
from director import mainwindowapp
import corl.utils
from corl.rendertrainingimages import RenderTrainingImages


if __name__ == '__main__':

    logFolder = "logs/moving-camera"
    if len(sys.argv) > 1:
	    logFolder = sys.argv[1]

    app = mainwindowapp.construct()
    app.view.setParent(None)
    app.view.show()

    print "logFolder = ", logFolder

    pathDict = corl.utils.getFilenames(logFolder)
    rti = RenderTrainingImages(app.view, app.viewOptions, pathDict)
    rti.renderAndSaveLabeledImages()
