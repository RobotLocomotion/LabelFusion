#!/bin/bash
#
# This script is run by the dockerfile during the docker build.
#

set -ex

apt-get update

apt-get install -y \
  bash-completion \
  build-essential \
  cmake \
  freeglut3-dev \
  git \
  libboost-all-dev \
  libglew-dev \
  libjpeg-dev \
  libeigen3-dev \
  libopencv-dev \
  libopenni2-dev \
  libqhull-dev \
  libqt4-dev \
  libqwt-dev \
  libsuitesparse-dev \
  libudev-dev \
  libusb-1.0-0-dev \
  libvtk5-dev \
  libvtk5-qt4-dev \
  mesa-utils \
  openjdk-8-jdk \
  zlib1g-dev \
  libyaml-cpp-dev \
  python-dev \
  python-matplotlib \
  python-numpy \
  python-pip \
  python-scipy \
  python-vtk \
  python-yaml \
  sudo


  # optional cleanup to make the docker image smaller
  # rm -rf /var/lib/apt/lists/*
