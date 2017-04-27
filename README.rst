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


Visualizing RGBD Data
---------------------

You can launch director with imageviewapp. You need to pass the :code:`-c` flag to director along with the config file::
	
	directorPython -m director.imageviewapp -c iiwaManip.cfg --channel OPENNI_FRAME --rgbd --pointcloud
