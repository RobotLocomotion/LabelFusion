'''
Usage:

directorPython convertScannerModel.py

  directorPython scripts/convertScannedModel.py          \
    data/object-meshes/turntable-scanner/robot.obj       \
    data/object-meshes/turntable-scanner/mobil1_v1.obj   \
    data/object-meshes/turntable-scanner/toothpaste.obj  \
    data/object-meshes/turntable-scanner/phone.obj       \
    --no-window \
    --output-dir data/object-meshes/

'''

import os
import sys
import numpy as np
import argparse
from director import objectmodel as om
from director import mainwindowapp
from director import ioUtils
from director import visualization as vis
from director import imageview
from director import vtkNumpy as vnp
from director import filterUtils
from director import vtkAll as vtk


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str, nargs='+', help='.obj file from scanner')
    parser.add_argument('--output-dir', type=str, default='.',
        help='output directory to write files (default is the current working dir)')
    parser.add_argument('--no-window', action='store_true', help='Disable visualization window.')
    args = parser.parse_args()


    imageViews = []

    def showImage(image):
        imageView = imageview.ImageView()
        imageView.setImage(image)
        imageView.view.show()
        imageView.resetCamera()
        imageViews.append(imageView)

    def loadObjFile(filename, scaleFactor=0.001):

        baseName = os.path.basename(filename)
        folder = om.getOrCreateContainer(baseName)
        meshes, actors = ioUtils.readObjMtl(filename)

        print 'loaded %d meshes from file: %s' % (len(meshes), filename)
        for i, mesh, actor in zip(xrange(len(meshes)), meshes, actors):

            mesh = filterUtils.cleanPolyData(mesh)
            mesh = filterUtils.computeNormals(mesh)

            obj = vis.showPolyData(mesh, baseName + ' piece %d'%i, parent=folder)
            obj.setProperty('Color', actor.GetProperty().GetColor())
            obj.actor.SetTexture(actor.GetTexture())

            pts = vnp.getNumpyFromVtk(obj.polyData, 'Points')
            pts *= scaleFactor

            print '  mesh %d, num points %d' % (i, obj.polyData.GetNumberOfPoints())

            #if actor.GetTexture():
            #    showImage(actor.GetTexture().GetInput())

        polyData = filterUtils.appendPolyData([obj.polyData for obj in folder.children()])
        vis.showPolyData(polyData, baseName + ' merged', parent=folder, visible=False)

        print '  total points:', polyData.GetNumberOfPoints()

        # compute centroid and subtract from points to move the mesh to the origin
        origin = np.array(filterUtils.computeCentroid(polyData))
        t = transformUtils.frameFromPositionAndRPY(-origin, [0.0, 0.0, 0.0])
        for obj in folder.children():
            obj.setPolyData(filterUtils.transformPolyData(obj.polyData, t))

        return folder.children()[-1].polyData



    app = mainwindowapp.construct(globals())

    outDir = args.output_dir
    if not os.path.isdir(outDir):
        os.makedirs(outDir)

    for filename in args.filename:
        print 'reading:', filename
        polyData = loadObjFile(filename)
        outFile = os.path.splitext(os.path.basename(filename))[0] + '.vtp'
        outFile = os.path.join(outDir, outFile)
        print 'writing:', outFile
        ioUtils.writePolyData(polyData, outFile)

    if not args.no_window:
        app.app.start()
