#!/bin/bash
#
# This script is sourced by bash when the docker container starts.
#

echo "sourcing ${BASH_SOURCE[0]}"

LABELFUSION_SOURCE_DIR=$(cd $(dirname ${BASH_SOURCE[0]})/.. && pwd)
DIRECTOR_INSTALL_DIR=/root/install

. ${LABELFUSION_SOURCE_DIR}/setup_environment.sh
