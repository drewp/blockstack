from __future__ import division
import random, time
import numpy
from math import atan2, pi

class GameState(object):
    def __init__(self, sound):
        self.sound = sound
        self.animSound = {
            'entering' : 'match',
            'explode' : 'explode',
            }

        self.gameState = "none"
        self.timedGameStart = self.timedGameEnd = self.gameMatches = 0
        
    def start(self):
        self._forceMatch = False
        
        self.enterNewPose()
        
        self.drawPose(self.currentPose)

    def animPos(self, now, inState, default):
        """if we're in this state, return the anim fraction, else default"""
        if self.state != inState:
            return default
        f = (now - self.animStart) / (self.animEnd - self.animStart)
        f = min(1, max(0, f))
        blend = f**8
        f = f * blend + 1.16 * f * (1 - blend)
        return f

    def enterNewPose(self):
        self.currentPose = self.makePose()
        self.startAnim("entering", .5)
        self.playedSwoosh = False

    def drawPose(self, pose):
        self.scene.pose = pose

        now = time.time()
        if now > self.animEnd:
            if self.state == 'explode':
                self.enterNewPose()
            elif self.state == 'entering':
                self.poseStart = now
                self.state = "hold"
            else:
                self.state = "hold"

        if (self.state == 'entering' and
            not self.playedSwoosh and
            self.animPos(now, 'entering', 1) > .6):
            self.playedSwoosh = True
            self.sound.playEffect('swoosh')

        if self.gameState == "playing":
            if now < self.timedGameEnd:
                self.setGameDesc(
                    "%s block %s, %.2f seconds left" % (
                        self.gameMatches,
                        "match" if self.gameMatches == 1 else "matches",
                        self.timedGameEnd - now))
            else:
                self.sound.playEffect("gameOver")
                self.setGameDesc("Game over: %d matches in %g seconds" %
                                 (self.gameMatches,
                                  self.timedGameEnd - self.timedGameStart))
                self.gameState = "showScore"
                
        self.scene.animSeed = self.animSeed
        self.scene.enter = self.animPos(now, 'entering', 1)
        self.scene.explode = self.animPos(now, 'explode', 0)
        self.scene.invalidate()


    def onFrame(self, blobCenters):
        if self.state == 'hold' and (
            self._forceMatch or 
            self.poseMatch(blobCenters, self.currentPose)):
            self._forceMatch = False
            self.gameMatches += 1
            solveTime = time.time() - self.poseStart
            self.setScore("Solved in %0.2f seconds" % solveTime)
            self.startAnim("explode", 1)
            if self.gameState == 'showScore':
                self.setGameDesc('')
                self.gameState = 'none'
        self.drawPose(self.currentPose)

    def startTimedGame(self):
        self.timedGameStart = time.time()
        self.timedGameEnd = self.timedGameStart + 8
        self.gameMatches = 0
        self.gameState = "playing"
        self.sound.playEffect("gameStart")
        self.enterNewPose()

    def forceMatch(self):
        self._forceMatch = True

    def startAnim(self, state, duration):
        self.state = state
        if state in self.animSound:
            self.sound.playEffect(self.animSound[state])

        self.animSeed = random.random()
        self.animStart = time.time()
        self.animEnd = self.animStart + duration
       
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
