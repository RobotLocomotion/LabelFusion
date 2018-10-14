====================
LabelFusion Data Organization
====================


1. Highest level directory structure
--------------------

Here are the top-level files and directories inside :code:`LabelFusion_public_full` and their uses:

- :code:`logs*` - A number of logs folders, described in the next section
- :code:`dataset_status.csv` - Overall status script, described in Section 4.
- :code:`object-meshses` - Contains the meshes for all objects across all datasets
- :code:`segnet_examples` - Contains samples of SegNet performance.  Each subdirectory has an :code:`index.html` which can be viewed with a web browser.

2. Log high-level organization
------------------------------

The purpose of each of the :code:`logs*` directories are:

- :code:`logs_test` - These logs are WIP (work in progress).  All initial syncing should happen here.
- :code:`logs_stable` - These logs have been looked over to see that the training images look good.
- :code:`logs_archive` - These logs are imperfect (not right set of objects, too shaky for ElasticFusion, etc.) but we don't want to delete yet.

3. Each log organization
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

4. Dataset status
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

