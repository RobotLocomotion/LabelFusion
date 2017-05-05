=====
Setup
=====

Data folder
-----------

Create a symlink from the shared MIT Dropbox `CORL217` folder to `spartan/src/CorlDev/data`.
For example::

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

ElasticFusion
----

ElasticFusion wants CUDA 7.5.

Grab www.github.com/patmarion/ElasticFusion, and follow build instructions.  Pat's fork of ElasticFusion adds lcm bridge.


====
Pipeline
====

1. Collect RGBD data
----
In first terminal, :code:`use_spartan` and then launch:

- :code:`kuka_iiwa_procman`
- Ctrl+R on vision-drivers --> openni-driver (unplug-replug if not working)
- Ctrl+R on bot-spy
- Verify that OPENNI_FRAME traffic is coming over lcm

In second terminal, :code:`use_spartan` and then:

- :code:`lcm-logger`
- Ctrl+C when done logging

Your data should now be saved as :code:`lcmlog-*`

2. Run RGBD data through ElasticFusion
----

Navigate to ElasticFusion executable (in :code:`ElasticFusion/GUI/build`) and then run::

	./ElasticFusion -l ~/Desktop/moving-camera.lcmlog  -f | tee moving-camera.lcmlog.mylog
	
Where :code:`~Desktop/moving-camera.lcmlog` is the full path to RGBD lcm data

Note that :code:`-f` option flips the blue/green, which is needed.

Run on the log for some time, then click Pause, then click “Save” to save a .ply file.  The .ply file will take the lcm log filename +.ply.  Close the program (click X in top left of window) and that will save the .posegraph.  NOTE: do not ctrl+C to exit -- this will not save the .posegraph!

3. Convert ElasticFusion .ply output to .vtp
----

First, open the .ply file in Meshlab, and save it (this will convert to an ASCII .ply file)

Next, convert to .vtp (Pat will document)



====
Misc
====

Visualizing RGBD Data
---------------------

You can launch director with imageviewapp. You need to pass the :code:`-c` flag to director along with the config file::
	
	cds && cd apps/iiwa
	directorPython -m director.imageviewapp -c iiwaManip.cfg --channel OPENNI_FRAME --rgbd --pointcloud
	
	
	
