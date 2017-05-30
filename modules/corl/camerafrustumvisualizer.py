import numpy as np

from director import visualization as vis
from director.debugVis import DebugData
from director import objectmodel as om



class CameraFrustumVisualizer(object):

    def __init__(self, imageManager, cameraName, frame,
                 visFolder=None, name=None, verbose=False):
        self.cameraName = cameraName
        self.imageManager = imageManager
        self.rayLength = 2.0
        self.frame = frame
        self.verbose = verbose

        self.visFolder = visFolder
        if visFolder is None:
            self.visFolder = om.getOrCreateContainer('camera frustrum')

        self.name = name
        if name is None:
            self.name = self.frame.getProperty('Name') + ' camera frustrum'

        self.frame.connectFrameModified(self.update)
        self.update(self.frame)
        self.visObj = om.findObjectByName(self.name, parent=self.visFolder)

    def getCameraFrustumRays(self, cameraToLocal):
        '''
        Returns (cameraPositions, rays)
        cameraPosition is in world frame.
        rays are four unit length vectors in world frame that point in the
        direction of the camera frustum edges
        '''

        cameraPos = np.array(cameraToLocal.GetPosition())

        camRays = []
        rays = np.array(self.imageManager.queue.getCameraFrustumBounds(self.cameraName))
        for i in xrange(4):
            ray = np.array(cameraToLocal.TransformVector(rays[i*3:i*3+3]))
            ray /= np.linalg.norm(ray)
            camRays.append(ray)

        return cameraPos, camRays

    def getCameraFrustumGeometry(self, rayLength, cameraToLocal):

        camPos, rays = self.getCameraFrustumRays(cameraToLocal)

        rays = [rayLength*r for r in rays]

        d = DebugData()
        d.addLine(camPos, camPos+rays[0])
        d.addLine(camPos, camPos+rays[1])
        d.addLine(camPos, camPos+rays[2])
        d.addLine(camPos, camPos+rays[3])
        d.addLine(camPos+rays[0], camPos+rays[1])
        d.addLine(camPos+rays[1], camPos+rays[2])
        d.addLine(camPos+rays[2], camPos+rays[3])
        d.addLine(camPos+rays[3], camPos+rays[0])
        return d.getPolyData()

    def update(self, frame):
        if self.verbose:
            print self.name + " modified "

        obj = om.findObjectByName(self.name, parent=self.visFolder)
        frameToLocal = self.frame.transform

        if obj and not obj.getProperty('Visible'):
            return

        cameraFrustrumGeometry = self.getCameraFrustumGeometry(self.rayLength, frameToLocal)
        vis.updatePolyData(cameraFrustrumGeometry, self.name, parent=self.visFolder, visible=False)
