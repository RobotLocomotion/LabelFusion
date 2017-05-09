'''
Usage:

  drake-visualizer --script scripts/renderTrainingImages.py logFolder

Loads director window with renderTrainingImages as a RenderTrainingImages object.
logFolder is optional. Call `renderAndSaveLabeledImages()` method on it to create the labeled images

uid_labels.png and uid_color_labels.png

in the data/logFolder directory. 


# For running headless
app.mainWindow.hide()
view.setParent(None)
view.show()
rti.renderAndSaveLabeledImages()
'''
import argparse
import corl.rendertrainingimages as rendertrainingimages

logFolder = "logs/moving-camera"
if len(_argv) > 1:
	logFolder = _argv[1]

print "logFolder = ", logFolder
rti = rendertrainingimages.RenderTrainingImages.makeDefault(globals())

