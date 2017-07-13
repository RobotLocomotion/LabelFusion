#!/bin/bash
#
# This script is sourced by bash when the docker container starts.
#

echo "sourcing ${BASH_SOURCE[0]}"

export LABELFUSION_SOURCE_DIR=$(cd $(dirname ${BASH_SOURCE[0]})/.. && pwd)
export DIRECTOR_INSTALL_DIR=/root/install

source ${LABELFUSION_SOURCE_DIR}/setup_environment.sh
