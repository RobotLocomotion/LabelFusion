FROM nvidia/cuda:8.0-devel-ubuntu16.04

WORKDIR /root

COPY install_dependencies.sh /tmp
RUN /tmp/install_dependencies.sh

COPY compile_all.sh /tmp
RUN /tmp/compile_all.sh

ENTRYPOINT bash -c "source /root/labelfusion/docker/docker_startup.sh && /bin/bash"
