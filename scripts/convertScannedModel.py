import os
import sys
import numpy as np
from director import objectmodel as om
from director import mainwindowapp
from director import ioUtils
from director import visualization as vis
from director import imageview
from director import vtkNumpy as vnp
from director import filterUtils
from director import vtkAll as vtk


if __name__ == '__main__':
    app = mainwindowapp.construct(globals())


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
        vis.showPolyData(polyData, 'merged pieces', parent=folder, visible=False)

        origin = np.array(filterUtils.computeCentroid(polyData))
        t = transformUtils.frameFromPositionAndRPY(-origin, [0.0, 0.0, 0.0])
        for obj in folder.children():
            obj.setPolyData(filterUtils.transformPolyData(obj.polyData, t))

        return folder.findChild('merged pieces').polyData


    filename = sys.argv[1]
    polyData = loadObjFile(filename)

    outFile = os.path.splitext(os.path.basename(filename))[0] + '.vtp'

    print 'writing output:', outFile
    ioUtils.writePolyData(polyData, outFile)

    app.app.start()
