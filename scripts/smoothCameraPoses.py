'''
Usage:

# cd into a scene directory that contains a posegraph.posegraph file to be smoothed
cd scene_dir

# run smoothing script
# it will read posegraph.posegraph from the current working director and save posegraph_smoothed.posegraph
directorPython smoothCameraPoses.py


'''

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from director import transformUtils


def smooth(x, window_len=11, window='hanning'):
    """
    This is code (with slight modifications) is from:

        http://scipy-cookbook.readthedocs.io/items/SignalSmooth.html

    smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
        x: the input signal
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal

    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)

    see also:

    np.hanning, np.hamming, np.bartlett, np.blackman, np.convolve
    scipy.signal.lfilter

    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """

    if x.ndim != 1:
        raise (ValueError, "smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise (ValueError, "Input vector needs to be bigger than window size.")


    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise (ValueError, "Window is one of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")


    #s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    s = x
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='same')
    return y


def to_xyzrpy(pose):
    pos = pose[:3]
    quat = pose[6], pose[3], pose[4], pose[5]
    rpy = transformUtils.quaternionToRollPitchYaw(quat)
    return np.hstack([pos, rpy])

def to_xyzquat(pose):
    pos = pose[:3]
    rpy = pose[3:]
    quat = transformUtils.rollPitchYawToQuaternion(rpy)
    return np.hstack([pos, quat[1], quat[2], quat[3], quat[0]])


def plot(poses, poseTimes):
    for i in xrange(6):
        y = smooth(poses[:,i], window_len=11, window='hanning')
        plt.plot(poseTimes, y)
        plt.plot(poseTimes, poses[:,i])
    plt.show()


def main():

    filename = 'posegraph.posegraph'
    plot = False
    windowLength = 11
    windowType = 'hanning'

    if not os.path.isfile(filename):
        print 'could not find posegraph file:', filename
        sys.exit(1)

    data = np.loadtxt(filename)
    poseTimes = data[:,0]
    poses = np.array(data[:,1:])
    poses = np.array([to_xyzrpy(pose) for pose in poses])
    poses[:,3:] = np.unwrap(poses[:,3:])

    for i in range(poses.shape[1]):
        poses[:,i] = smooth(poses[:,i], window_len=windowLength, window=windowType)

    if plot:
        plot(poses, poseTimes)

    poses = np.array([to_xyzquat(pose) for pose in poses])
    poses = np.hstack([np.reshape(poseTimes, (-1,1)), poses])
    np.savetxt('posegraph_smoothed.posegraph', poses)


if __name__ == '__main__':
    main()
