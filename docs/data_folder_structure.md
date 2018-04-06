
# LabelFusion data directory structure

The LabelFusion data folder is a directory that lives on your host machine. When you launch the `docker` container with

```
LabelFusion/docker/docker_run.sh /path/to/data-folder
```

this directory gets mounted inside the docker to `/root/labelfusion/data`.

## Object Meshes
LabelFusion requires object meshes to perform the model alignment and rendering of masks. The default location for `object-meshes` is 

```
data\
  object_meshes\
      drill_mesh.vtp
````

When running the alignment tool the software needs to know where to find the mesh for a specific object. In particular the call
`gr.launchObjectAlignment(<objectName>)` will try to look up the mesh for `<objectName>`. It is assused that this information is contained in a file `object_data.yaml` which is in location

```
data\
  object_data.yaml
```

Each entry in this yaml file is of the form

```
drill:
  mesh: object-meshes/handheld-scanner/drill_decimated_mesh.vtp
  label: 1
```

The `mesh` entry points to the mesh file location, relative to the top-level `data` directory. The `label` entry is the global label for this object. When the greyscale mask image gets rendered pixels with a value of `1` will correspond to the drill, in this case. Note that **`0` always represents the background so it cannot be used it as an object label**.

