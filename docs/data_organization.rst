====================
LabelFusion Data Organization
====================


Introduction
------------
This document overviews the organization of the data in LabelFusion


Mounting into docker
--------------------

If you use our provided docker image, the LabelFusion data folder is a directory that lives on your host machine. When you launch the `docker` container with

::

	LabelFusion/docker/docker_run.sh /path/to/data-folder


this directory gets mounted inside the docker to `/root/labelfusion/data`.


Highest level directory structure
--------------------

Here are the top-level files and directories inside :code:`LabelFusion_public_full` and their uses:

- :code:`logs*` - A number of logs folders, described in the next section
- :code:`dataset_status.csv` - Overall status script, described in Section 4.
- :code:`object-meshses` - Contains the meshes for all objects across all datasets
- :code:`object_data.yaml` - Critical file which is a dictionary of all objects in the database, their pixel label (i.e. "1" is the oil_bottle), and the mesh (.vtp or .obj, etc) that is used for this object.

Object Meshes
--------------

LabelFusion requires object meshes to perform the model alignment and rendering of masks. The default location for `object-meshes` is 

::

	data\
	  object-meshes\
	      drill_mesh.vtp


When running the alignment tool the software needs to know where to find the mesh for a specific object. In particular the call
`gr.launchObjectAlignment(<objectName>)` will try to look up the mesh for `<objectName>`. It is assused that this information is contained in a file `object_data.yaml` which is in location

::

	data\
  		object_data.yaml


Each entry in this yaml file is of the form

::

	drill:
	  mesh: object-meshes/handheld-scanner/drill_decimated_mesh.vtp
	  label: 1


The `mesh` entry points to the mesh file location, relative to the top-level `data` directory. The `label` entry is the global label for this object. When the greyscale mask image gets rendered pixels with a value of `1` will correspond to the drill, in this case. Note that **`0` always represents the background so it cannot be used it as an object label**.



Log high-level organization
------------------------------

The purpose of each of the :code:`logs*` directories are:

- :code:`logs_test` - These are where all of our logs are.  It's a bit of a misnomer, but it's there for historical reasons.
- :code:`logs_arch` - These logs are imperfect (not right set of objects, too shaky for ElasticFusion, etc.) but we don't want to delete yet.

Each log organization
------------------------

Each log should have a unique name across all datasets.  Optionally this can be a unique date in the form:

- :code:`YYYY-MM-DD-##`

Where ## is that day's number of log.

The subdirectory should be named this log's name.

Inside each log should start with the following files and directories:

::

	logs_test/
		2017-06-07-01/
			*lcmlog*

After running through all scripts, the following files and directories will be created:

::

	logs_test/
		2017-06-07-01/
			info.yaml
			original_log.lcmlog
			trimmed_log.lcmlog         # if trimmed
			images/                    
				..._rgb.png
				..._color_labels.png
				..._labels.png
				..._utime.txt
				..._poses.yaml
			resized_images/            # downsized to 480 x 360 for training
				..._rgb.png
				..._labels.png
			above_table_pointcloud.vtp
			reconstructed_pointcloud.vtp
			converted_to_ascii.ply
			converted_to_ascii_modified_header.ply
			posegraph.posegraph
			registration_result.yaml
			transforms.yaml

Script for viewing dataset status
-----------------

The :code:`dataset_update_status` script provides a way to keep track of status for each log.

Each log can be commented on by adding for example a :code:`comment: this log looks good` line to :code:`info.yaml`.  Note that to keep terminal output nicely formatted, only a small amount of chars for this comment will be displayed.

The :code:`dataset_update_status` script will look for the existence of the following for each step:

::

	run_trim           - check for info.yaml
	run_prep           - check for reconstructed_pointcloud.vtp
	run_alignment_tool - check for registration_result.yaml
	run_create_data    - check for images/0000000001_color_labels.png
	run_resize         - check for resize_images/0000000001_labels.png


Note:

- The script checks for each of these and writes a :code:`x` or :code:`_` for each of these 5 steps.
- The number of images is also counted and displayed.

The script creates :code:`dataset_status.csv` and will :code:`cat` the output in terminal, for example:

:code:`dataset_update_status`

::

	logs_test/2017-05-04-00 x x _ _ imgs ----- |                         |
	logs_test/2017-05-04-01 x x x x imgs 01880 |                         |
	logs_test/2017-05-04-02 x x x x imgs 01730 |looks good               |
	logs_test/2017-05-04-03 x x x x imgs 00172 |                         |
	logs_test/2017-05-04-04 x x x x imgs 01821 |                         |
	logs_test/2017-05-04-05 x x _ _ imgs ----- |                         |
	logs_test/2017-05-04-06 x x _ _ imgs ----- |                         |
	logs_test/2017-05-04-07 x x x _ imgs ----- |                         |
	logs_test/2017-05-25-00 _ _ _ _ imgs ----- |                         |
	logs_test/2017-05-25-01 x x x _ imgs ----- |ready for alignment      |

Passing the :code:`-o` arg will check for the existence of objects in each log:

:code:`dataset_update_status -o`

::

	logs_test/2017-05-04-00 x x _ _ imgs ----- |                         | []
	logs_test/2017-05-04-01 x x x x imgs 01880 |                         | |['phone', 'robot']|
	logs_test/2017-05-04-02 x x x x imgs 01730 |looks good               | |['phone', 'robot']|
	logs_test/2017-05-04-03 x x x x imgs 00172 |                         | |['phone', 'robot', 'tissue_box']|
	logs_test/2017-05-04-04 x x x x imgs 01821 |                         | |['phone', 'robot', 'tissue_box']|
	logs_test/2017-05-04-05 x x _ _ imgs ----- |                         | []
	logs_test/2017-05-04-06 x x _ _ imgs ----- |                         | []
	logs_test/2017-05-04-07 x x x _ imgs ----- |                         | |['phone', 'robot']|
	logs_test/2017-05-25-00 _ _ _ _ imgs ----- |                         | []
	logs_test/2017-05-25-01 x x x _ imgs ----- |ready for alignment      | |['oil_bottle', 'phone']|

