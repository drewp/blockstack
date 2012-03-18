from __future__ import division
import random
import numpy
from math import atan2, pi

class GameState(object):
    def __init__(self, sound):
        self.sound = sound
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
            self.sound.playMatch()
            print "draw some glow or connector lines between robot and human pics to show a match"
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
                v1 = v1[:2]
                v2 = v2[:2]
                offset = pi if p is positions1 else 0
                angles.append([positiveAngle(atan2(v1[0], v1[1]), offset),
                               positiveAngle(atan2(v2[0], v2[1]), offset)])
            err = sum(x * x for x in map(diffAngle, zip(angles[0], angles[1])))
            print angles[0], angles[1], err
            return err < .2
        except KeyError:
            return False

def diffAngle((a1, a2)):
    if a2 < a1:
        a1,a2=a2,a1
    return min(a2-a1, 2*pi-a2+a1)

def positiveAngle(ang, offset):
    return (ang + pi + offset) % (2*pi)
