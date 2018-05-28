=====
LabelFusion
=====

This readme is to document how to create your own data with LabelFusion.

If you're looking to download the example LabelFusion dataset, go here: http://labelfusion.csail.mit.edu/#data

=====
Setup
=====

Recommended setup is through our Docker_.

.. _Docker: https://hub.docker.com/r/robotlocomotion/labelfusion/

If instead you'd prefer a native install, go to:  "Setup Instructions".

.. _Setup_Instructions: https://github.com/RobotLocomotion/LabelFusion/blob/master/docs/setup.rst

===========================
Quick Pipeline Instructions
===========================

This is the quick version.  If you'd prefer to go step-by-step manually, see Pipeline_Instructions_.

.. _Pipeline_Instructions: https://github.com/RobotLocomotion/LabelFusion/blob/master/docs/pipeline.rst

Collect raw data from Xtion
---------------------------

First, :code:`cdlf && cd data/logs`, then make a new directory for your data.  In one terminal, run:

::

	openni2-camera-lcm

In another, run:

::

	lcm-logger

Your data will be saved in current directory as :code:`lcmlog-*`.


Process into labeled training data
----------------------------------

First we will launch a log player with a slider, and a viewer.  The terminal will prompt for a start and end time to trim the log, then save the outputs:

::

	run_trim

Next, we prepare for object pose fitting, by running ElasticFusion and formatting the output:

::

	run_prep

Next, launch the object alignment tool.  See Pipeline_Instructions_ for how to use the alignment tool:

::

	run_alignment_tool


After the alignment outputs have been saved, we can create the labeled data:

::

	run_create_data
	
By default, only RGB images and labels will be saved.  If you'd also like to save depth images, use the :code:`-d` flag:

::

	run_create_data -d



Train SegNet on labeled data
----------------------------

Navigate to :code:`/SegNet/MovingCamera/`

Copy all the data you want to use (created by :code:`run_create_data` from different datasets) into :code:`./train`

Use a different subdirectory inside :code:`/train/` for each log, i.e.:

::

        /train/log-1
        /train/log-2

Then resize all of the training images to a better size for training::

	python resize_all_images.py

Finally, create the description of image-label pairs needed as SegNet input::

	python create_traiing_set_list.py

To train SegNet::

	cd /
	./SegNet/caffe-segnet/build/tools/caffe train -gpu 0 -solver /SegNet/Models/moving_camera_solver.prototxt

