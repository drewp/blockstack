from __future__ import division
import random
import numpy
from math import atan2

class GameState(object):
    def start(self):
        self._forceMatch = False
        
        self.currentPose = self.makePose()
        
        self.drawPose(self.currentPose)

    def drawPose(self, pose):
        self.scene.pose = pose
        self.scene.invalidate()

    def onFrame(self, blobCenters):
        if self._forceMatch or self.poseMatch(blobCenters, self.currentPose):
            self._forceMatch = False
            self.currentPose = self.makePose()
            print "match! now", self.currentPose
            self.drawPose(self.currentPose)

    def forceMatch(self):
        self._forceMatch = True

    def makePose(self):
        colors = ['red', 'blue', 'green']
        random.shuffle(colors)
        orient = random.choice(['flat', 'tri', 'tall'])
        if orient == 'flat':
            return {colors[0] : (-1, .5, 0),
                    colors[1] : (0, .5, 0),
                    colors[2] : (1, .5, 0)}
        elif orient == 'tall':
            return {colors[0] : (0, .5, 0),
                    colors[1] : (0, 1.5, 0),
                    colors[2] : (0, 2.5, 0)}
        elif orient == 'tri':
            return {colors[0] : (0, .5, 0),
                    colors[1] : (.5, 1.5, 0),
                    colors[2] : (1, 0.5, 0)}

    def poseMatch(self, positions1, positions2):
        try:
            angles = []
            for p in [positions1, positions2]:
                v1 = numpy.array(p['green']) - p['red']
                v2 = numpy.array(p['blue']) - p['green']
                angles.append(numpy.array([fixNegative(atan2(v1[0], v1[1])),
                                           fixNegative(atan2(v2[0], v2[1]))]))
            print angles[0], angles[1]
            err = sum(x * x for x in (angles[0] - angles[1]))
            return err < .5
        except KeyError:
            return False


def fixNegative(ang):
    if ang < -3.0:
        return 3.1415
    return ang
