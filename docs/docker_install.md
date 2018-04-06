# LabelFusion docker installation

## Getting Started
1. Install [nvidia-docker](https://github.com/NVIDIA/nvidia-docker)
2. `git clone https://github.com/RobotLocomotion/LabelFusion.git`
3. `LabelFusion/docker/docker_run.sh /path/to/data-folder` where `path/to/data-folder` points to the top level directory of your LabelFusion data


## More details

The `docker_run.sh` script calls `nvidia-docker` to start the LabelFusion Docker container with an interactive bash session. The first time it runs the LabelFusion image will be downloaded from DockerHub automatically.

The script sets the required environment variables and mounts your local LabelFusion source directory as a volume inside the Docker container. There is no additional code that needs to be compiled. The LabelFusion image already contains all the required binary dependencies.

You can optionally give a path to a data directory. If the path to a data directory is given then the data directory is also mounted as a volume inside the container. The paths inside the Docker container will be

```
~/labelfusion <-- the mounted LabelFusion directory
~/labelfusion/data <-- the mounted data directory
```

When the Docker container starts it launches an interactive bash session. It automatically sources the file `~/labelfusion/setup_environment.sh` inside the image to setup the required environment variables for using LabelFusion tools.
