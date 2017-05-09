'''
Usage:

  drake-visualizer --script scripts/renderTrainingImages.py

Loads director window with renderTrainingImages as a RenderTrainingImages object.
Call `saveImagesTest()` method on it to create the labeled images 

0000000001_labels.png and 0000000001_color_labels.png

in the data/logs/moving-camera/images folder.
'''

import corl.rendertrainingimages as rendertrainingimages
rendertrainingimages.RenderTrainingImages.makeDefault(globals())

