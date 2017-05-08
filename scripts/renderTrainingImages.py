'''
Usage:

  drake-visualizer --script scripts/renderTrainingImages.py

Outputs test_color.png and test_labels.png.  You can plot
the label image with:

  python scripts/plotLabels test_labels.png
'''

import corl.rendertrainingimages as rendertrainingimages
rendertrainingimages.RenderTrainingImages.makeDefault(globals())

