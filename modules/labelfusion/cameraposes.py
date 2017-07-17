# class to help manage loading stored camera poses
import numpy as np

from director import transformUtils


class CameraPoses(object):

    def __init__(self, posegraphFile=None):
        self.posegraphFile = posegraphFile

        if self.posegraphFile is not None:
            self.loadCameraPoses(posegraphFile)


    def loadCameraPoses(self, posegraphFile):
        data = np.loadtxt(posegraphFile)
        self.poseTimes = np.array(data[:,0]*1e6, dtype=int)
        self.poses = []
        for pose in data[:,1:]:
            pos = pose[:3]
            quat = pose[6], pose[3], pose[4], pose[5] # quat data from file is ordered as x, y, z, w
            self.poses.append((pos, quat))

    def getCameraPoseAtUTime(self, utime):
        idx = np.searchsorted(self.poseTimes, utime, side='left')
        if idx == len(self.poseTimes):
            idx = len(self.poseTimes) - 1

        (pos, quat) = self.poses[idx]
        return transformUtils.transformFromPose(pos, quat)