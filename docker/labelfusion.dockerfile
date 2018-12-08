FROM ianre657/cuda8gl:latetest

WORKDIR /root

#COPY build_scripts /tmp/build_scripts

RUN apt-get update && apt-get upgrade -y
# install_dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-utils \
    && apt-get install  -y --no-install-recommends \
    \
    # basic packages
    sudo git bash-completion lsb-core wget software-properties-common \
    \
    # for debugging
    \
    cmake-curses-gui vim apt-file \
    && apt-file update \ 
    \
    \ && apt-get update && apt-get install -y --no-install-recommends \
    # vtk5 with qt4
    qt4-default  qt4-dev-tools  libqt4-opengl-dev libqt4-dev libgl1-mesa-dev \
    libglu1-mesa-dev freeglut3-dev libvtk-java openjdk-8-jdk \
    \
    # dependency for Director
    build-essential cmake libglib2.0-dev libqt4-dev \
    libx11-dev libxext-dev libxt-dev \
    python-dev python-pip python-lxml python-numpy python-scipy python-yaml python-vtk python-matplotlib \
    libvtk5-qt4-dev libvtk5-dev \
    libqwt-dev openjdk-8-jdk qtbase5-private-dev \
    libboost-all-dev libeigen3-dev liblua5.2-dev libyaml-cpp-dev libopencv-dev libqhull-dev \
    \
    # dependency for ElasticFusion
    git libsuitesparse-dev cmake-qt-gui build-essential libusb-1.0-0-dev libudev-dev \
    freeglut3-dev libglew-dev libeigen3-dev zlib1g-dev libjpeg-dev libopenni2-dev \
    gcc-5 g++-5


# fix some path issue
RUN ln -sf /usr/include/eigen3/Eigen /usr/include/Eigen && \
    ln -sf /usr/include/eigen3/unsupported /usr/include/unsupported && \
    ln -s /usr/lib/python2.7/dist-packages/vtk/libvtkRenderingPythonTkWidgets.x86_64-linux-gnu.so /usr/lib/x86_64-linux-gnu/libvtkRenderingPythonTkWidgets.so && \
    ln -s /usr/local/cuda-8.0 /usr/local/cuda


# compile director
#RUN /tmp/build_scripts/compile_director.sh
RUN git clone -b labelFusion-director https://github.com/ianre657/director.git \
    && mkdir director-build && cd director-build \
    && cmake ../director/distro/superbuild \
        -DUSE_EXTERNAL_INSTALL:BOOL=ON \
        -DUSE_DRAKE:BOOL=OFF \
        -DUSE_LCM:BOOL=ON \
        -DUSE_LIBBOT:BOOL=ON \
        -DUSE_SYSTEM_EIGEN:BOOL=ON \
        -DUSE_SYSTEM_LCM:BOOL=OFF \
        -DUSE_SYSTEM_LIBBOT:BOOL=OFF \
        -DUSE_SYSTEM_VTK:BOOL=ON \
        -DUSE_PCL:BOOL=ON \
        -DUSE_APRILTAGS:BOOL=OFF \
        -DUSE_KINECT:BOOL=ON \
        -DCMAKE_INSTALL_PREFIX:PATH=/root/install \
        -DCMAKE_BUILD_TYPE:STRING=Release \
        -DDD_QT_VERSION:STRING=4 \
    && make -j"$(nproc)" -l"$(nproc)" \
    #cleanup to make the docker image smaller
    && cd .. && rm -rf director-build

# compile elasticfusion
#RUN /tmp/build_scripts/compile_elasticfusion.sh
ARG root_dir=/root
ARG install_dir=/root/install
RUN git clone -b pf-lm-debug-jpeg https://github.com/ianre657/ElasticFusion.git \
    && cd ElasticFusion \
    \
    # Build Pangolin
    && git clone https://github.com/stevenlovegrove/Pangolin.git && cd Pangolin \
        && mkdir build && cd build \
        && cmake ../ -DAVFORMAT_INCLUDE_DIR="" -DCPP11_NO_BOOST=ON \
        && make -j$(nproc) -l$(nproc) \
        && cd ../.. \
    \
    # Build Elasticfusion
    && export CMAKE_PREFIX_PATH=$install_dir \
    && cd Core \
        && mkdir build && cd build \
        && cmake ../src \
        && make -j$(nproc) -l$(nproc) \
        && cd ../.. \
    && cd GPUTest \
        && mkdir build && cd build \
        && cmake ../src \
        && make -j$(nproc) -l$(nproc) \
        && cd ../.. \
    && cd GUI \
        && mkdir build && cd build \
        && cmake ../src \
        && make -j$(nproc) -l$(nproc) \
        && cd ../.. \
    && ln -s /root/ElasticFusion/GUI/build/ElasticFusion $install_dir/bin \
    \
    # cleanup to make the docker image smaller
    && find . -name \*.o | xargs rm


RUN rm -rf /var/lib/apt/lists/*
ENTRYPOINT bash -c "source /root/labelfusion/docker/docker_startup.sh && /bin/bash"