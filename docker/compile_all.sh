#!/bin/bash
#
# This script is run by the dockerfile during the docker build.
#

set -exu

root_dir=$(pwd)
install_dir=$root_dir/install

build_director()
{
  cd $root_dir
  git clone https://github.com/RobotLocomotion/director.git
  cd director
  git remote add pf https://github.com/peteflorence/director.git
  git fetch pf
  git checkout pf/corl-master
  cd ..

  mkdir director-build
  cd director-build

  cmake ../director/distro/superbuild \
      -DUSE_EXTERNAL_INSTALL:BOOL=ON \
      -DUSE_DRAKE:BOOL=OFF \
      -DUSE_LCM:BOOL=ON \
      -DUSE_LIBBOT:BOOL=ON \
      -DUSE_SYSTEM_EIGEN:BOOL=ON \
      -DUSE_SYSTEM_LCM:BOOL=OFF \
      -DUSE_SYSTEM_LIBBOT:BOOL=OFF \
      -DUSE_SYSTEM_VTK:BOOL=ON \
      -DUSE_PCL:BOOL=ON \
      -DUSE_APRILTAGS:BOOL=ON \
      -DUSE_KINECT:BOOL=ON \
      -DCMAKE_INSTALL_PREFIX:PATH=$install_dir \
      -DCMAKE_BUILD_TYPE:STRING=Release

  make -j$(nproc)

  # cleanup to make the docker image smaller
  cd ..
  rm -rf director-build
}

build_elasticfusion()
{
  cd $root_dir
  git clone https://github.com/peteflorence/ElasticFusion.git
  cd ElasticFusion
  git checkout pf-lm-debug-jpeg

  git clone https://github.com/stevenlovegrove/Pangolin.git
  cd Pangolin
  mkdir build
  cd build
  cmake ../ -DAVFORMAT_INCLUDE_DIR="" -DCPP11_NO_BOOST=ON
  make -j$(nproc)
  cd ../..

  export CMAKE_PREFIX_PATH=$install_dir
  cd Core
  mkdir build
  cd build
  cmake ../src
  make -j$(nproc)

  cd ../../GPUTest
  mkdir build
  cd build
  cmake ../src
  make -j$(nproc)

  cd ../../GUI
  mkdir build
  cd build
  cmake ../src
  make -j$(nproc)

  ln -s $(pwd)/ElasticFusion $install_dir/bin

  # cleanup to make the docker image smaller
  cd ../..
  find . -name \*.o | xargs rm
}


build_director
build_elasticfusion
