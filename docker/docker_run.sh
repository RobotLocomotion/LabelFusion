#!/bin/bash
#
# Usage:  ./docker_run.sh [/path/to/data]
#
# This script calls `docker` with `nvidia-docker2 runtime` to start the 
# labelfusion container with an interactive bash session.  This script 
# sets the required environment variables and mounts the labelfusion 
# source directory as a volume in the docker container.  If the path 
# to a data directory is given then the data directory is also mounted 
# as a volume.
#

source ./config.sh
source_dir=$(cd $(dirname $0)/.. && pwd)

if [ ! -z "$1" ]; then

  data_dir=$1
  if [ ! -d "$data_dir" ]; then
    echo "directory does not exist: $data_dir"
    exit 1
  fi

  data_mount_arg="-v $data_dir:/root/labelfusion/data"
fi

xhost +
docker run -it \
  --rm \
  --runtime=nvidia \
  -e DISPLAY \
  --privileged \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $source_dir:/root/labelfusion $data_mount_arg \
  -v /dev/bus/usb:/dev/bus/usb \
  $image_name
xhost -
