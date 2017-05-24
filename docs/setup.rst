=====
Setup
=====

Data folder
-----------

Create a symlink from the shared MIT Dropbox `CORL217` folder to `spartan/src/CorlDev/data`.
For example.  (Make sure that ./data doesn't exist before calling this command, or the linking will be nested)::

    ln -s $HOME/Dropbox/CORL2017 ./data

If Dropbox is hosted on another computer, you can use sshfs to mount the data from the remote computer::

    mkdir -p ./data  # create mount point
    sshfs user@hostname:Dropbox/CORL2017 ./data


Environment
-----------

Source the `setup_environment.sh` file.  This file appends CorlDev/modules
to the `PYTHONPATH` so that Python scripts can import the corl module.
The corl module contains reusable functions and utilities that are used by
the scripts.

Director
--------

Checkout the branch :code:`corl-master` from the repository :code:`github.com/manuelli/director.git`. This will serve as our internal director branch. The idea is that these changes will make their way back to director/master eventually, but that process shouldn't slow down our workflow.


ElasticFusion
-------------

- Install CUDA (we have verified that ElasticFusion works on CUDA 7.5 and 8.0)
- Install ElasticFusion::

	git clone git@github.com:peteflorence/ElasticFusion.git
	cd ElasticFusion
	./build.sh

The build script is great, but if it doesn't work, follow the build instructions in the README.md.

SegNet
------

- Install SegNet scripts::

	cd /
	git clone git@github.com:peteflorence/SegNet-Tutorial.git
	mv SegNet-Tutorial SegNet && cd SegNet
	git checkout pf-moving-camera

- Install caffe-segnet inside of SegNet and test, and install Python bindings::

	git clone git@github.com:alexgkendall/caffe-segnet.git
	cp Makefile.config.example Makefile.config
	# Adjust Makefile.config (for example, if using Anaconda Python, or if cuDNN is desired)
	make all
	make test
	make runtest
	make pycaffe

These are the key commands, but if you need full instructions, see http://mi.eng.cam.ac.uk/projects/segnet/tutorial.html and http://caffe.berkeleyvision.org/installation.html.  (Note that caffe-segnet is particular distribution of segnet, you do not need to separately install caffe.)
