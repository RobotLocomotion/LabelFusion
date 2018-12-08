#!/bin/bash
#
# This script runs docker build to create the labelfusion docker image.
#

set -exu
source ./config.sh

root_dir=$(cd $(dirname $0)/../ && pwd)

docker build \
    -f $root_dir/docker/labelfusion.dockerfile \
    -t ${image_name} \
    $root_dir/docker
