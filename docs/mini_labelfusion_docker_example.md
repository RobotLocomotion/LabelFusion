
# Under Construction


# Getting started with LabelFusion
This document outlines how to get started with the LabelFusion data collection pipeline. The basic steps are

1. Download the example dataset
2. Clone the repo and launch the docker container

## Downloading the example dataset

Download the example dataset from `https://data.csail.mit.edu/labelfusion/LabelFusionExampleData/mini-labelfusion-drill.tar.gz`. See [this](data_folder_structure.md) file for an explanation of the data folder structure.

## Launching the docker container
Follow the [docker](docker_installation.md) instructions. Set `path/to/data-folder` to the location where you extracted `mini-labelfusion-drill.tar.gz`. Now you can launch the alignment tool on a scene where the labeling has already been performed.
  ```
  cd /root/labelfusion/data/logs_test/2017-06-13-01 && run_alignment_tool
  ```
This opens up the `director` window and you can see what the final product of the alignment looks like. If you want to try using teh alignment tool for yourself then run


```
cd /root/labelfusion/data/logs_test/2017-06-13-01_unaliged && run_alignment_tool
```

and follow the Global Object Pose Fitting section of the [pipeline instructions](pipeline.rst)
