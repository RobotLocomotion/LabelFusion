======================
Automation of Pipeline
======================

This doc describes how to set up a cluster of computers to handle different parts of the pipeline.

Scripts live in :code:`/scripts/bin` (executable) and :code:`/automation/scripts` (Python source).

1. Steps
--------

To recap, the 5 steps are:

::

	run_no_trim         # or run_trim          
	run_prep           
	run_alignment_tool  # needs human input
	run_create_data    
	run_resize         


2. Automating steps
-------------------

Options:

- :code:`auto_no_trim_prep`
	- checks for any folders in :code:`logs_test` which meet:
		- pre:  :code:`./logs_test/log/*lcmlog*` exists
		- wip:  :code:`./logs_test/auto_no_trim_prep_in_progress.txt` doesn't exist
		- done: :code:`./logs_test/log/original_log.lcmlog` doesn't exist
	- creates :code:`./auto_no_trim_prep_in_progress.txt`
	- does    :code:`run_no_trim` and :code:`run_prep` for the first log found that meets this condition
	- deletes :code:`./auto_no_trim_prep_in_progress.txt`
- :code:`auto_alignment_tool`
	- checks for any folders in :code:`logs_test` which meet:
		- pre:  :code:`./logs_test/log/reconstructed_pointcloud.vtp` exists
		- wip:  :code:`./logs_test/auto_alignment_tool_in_progress.txt` doesn't exist
		- done: :code:`./logs_test/log/registration_result.yaml` doesn't exist
	- creates :code:`./auto_alignemnt_tool_in_progress.txt`
	- opens   :code:`run_alignment_tool` for the first log found that meets this condition
	- deletes :code:`./auto_alignemnt_tool_in_progress.txt`
- :code:`auto_create_data_and_resize`
	- checks for any folders in :code:`logs_test` which meet:
		- pre:  :code:`./logs_test/log/registration_result.yaml` exists
		- wip:  :code:`./logs_test/auto_create_data_and_resize_in_progress.txt` doesn't exist
		- done: :code:`./logs_test/log/resized_images` doesn't exist
	- creates :code:`./auto_create_data_and_resize_in_progress.txt`
	- does    :code:`run_create_data` and :code:`run_resize` for the first log found that meets this condition
	- deletes :code:`./auto_create_data_and_resize_in_progress.txt`


3. Setting up cronjobs
----------------------

To automatically run one of these scripts, set up a cronjob with

::

	crontab -e

And edit a line to include for example:

::

	* * * * * /full/path/to/auto_no_trim_prep


