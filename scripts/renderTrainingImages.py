'''
Usage:

  directorPython scripts/renderTrainingImages.py --bot-config $LABELFUSION_SOURCE_DIR/config/bot_frames.cfg --logFolder logs/moving-camera

Optionally you can pass --logFolder <logFolder> on the command line
where <logFolder> is the path to the lcm log folder relative to the
data folder.  For example: --logFolder logs/moving-camera
'''


from director import drcargs
from director import mainwindowapp
import labelfusion.utils
from labelfusion.rendertrainingimages import RenderTrainingImages
import os

if __name__ == '__main__':
    print os.getcwd()
    if os.path.isfile(os.path.join(os.getcwd(), "images/0000000001_labels.png")):
        print ""
        print "Already made labels? Skipping..."
        print "To re-extract, either move or delete ./images/"
        print ""
        quit()

    parser = drcargs.getGlobalArgParser().getParser()
    parser.add_argument('--logFolder', type=str, dest='logFolder',
                        help='location of top level folder for this log, relative to LabelFusion/data')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    app = mainwindowapp.construct(disable_anti_alias=True)
    app.view.setParent(None)
    app.view.show()

    print "logFolder = ", args.logFolder

    pathDict = labelfusion.utils.getFilenames(args.logFolder)
    rti = RenderTrainingImages(app.view, app.viewOptions, pathDict)
    if args.debug:
        globals().update(rti=rti)
        app.app.start()
    else:
        rti.renderAndSaveLabeledImages()
