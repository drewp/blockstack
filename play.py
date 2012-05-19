from __future__ import division
import random, time
import numpy
from math import atan2, pi
from debug import logTime
from pydispatch import dispatcher

class GameState(object):
    def __init__(self, sound, colors):
        self.sound = sound
        self.colors = colors
        self.animSound = {
            'entering' : 'match',
            'explode' : 'explode',
            }

        self.gameState = "none"
        self.timedGameRange = (0,0)
        self.gameMatches = 0
        
    def start(self):
        """once at process startup"""
        self._forceMatch = False        
        self.enterNewPose()
        self.scene.setLighting('train')

    def animPos(self, now, inState, default, bounce=False):
        """if we're in this state, return the anim fraction, else default"""
        if self.state != inState:
            return default
        f = (now - self.animStart) / (self.animEnd - self.animStart)
        f = min(1, max(0, f))
        if bounce:
            f = f**3
        return f

    def enterNewPose(self):
        if not hasattr(self, 'currentPose'):
            self.currentPose = {}
        prev = self.currentPose
        while self.currentPose == prev:
            # also i want to skip ones that are a close enough match
            # to the current blocks
            self.currentPose = self.makePose()
        self.startAnim("entering", .3)
        self.sound.playEffect('swoosh')


    def update(self, blobCenters=None, videoPixbuf=None):
        """blobCenters and videoPixbuf are only set when the video
        frame is new"""
        now = time.time()
        haveNewFrame = blobCenters is not None

        if self.state == 'hold' and (
            self._forceMatch or 
            (haveNewFrame and self.poseMatch(blobCenters, self.currentPose))):
            self._forceMatch = False
            self.gameMatches += 1
            solveTime = time.time() - self.poseStart
            self.setScore("Solved in %0.2f seconds" % solveTime)
            self.startAnim("explode", .7)

        if now > self.animEnd:
            if self.state == 'explode':
                if self.gameState not in ['ready', 'showScore']:
                    self.enterNewPose()
            elif self.state == 'entering':
                self.poseStart = now
                self.state = "hold"
            else:
                self.state = "hold"

        if self.gameState == "ready":
            self.scene.cornerMessage = None
            if now > self.timedGameRange[0]:
                self.timedGameStart()
        elif self.gameState == "playing":
            if now < self.timedGameRange[1]:
                match = "%s %s" % (self.gameMatches,
                                   "match" if self.gameMatches == 1 else "matches")
                self.scene.cornerMessage = (
                    "%s, %.1f seconds left" % (
                        match,
                        self.timedGameRange[1] - now))
            else:
                self.timedGameEnd(now)
        elif self.gameState == "showScore":
            if now > self.gameNext:
                self.scene.currentMessage = None
                self.gameState = "none"
                self.enterNewPose()
        else:
            self.scene.cornerMessage = "Training mode"

        if haveNewFrame:
            self.scene.videoFrame = videoPixbuf
            self.scene.updateVideo()
        
        self.scene.pose = self.currentPose
        self.scene.animSeed = self.animSeed
        self.scene.enter = self.animPos(now, 'entering', 1, bounce=True)
        self.scene.explode = self.animPos(now, 'explode', 0)
        self.scene.updateCubes()

    def timedGameMake(self):
        t = time.time() + 3
        self.timedGameRange = (t, t + 30)
        self.gameMatches = 0
        self.gameState = "ready"
        self.scene.currentMessage = "Ready"
        self.sound.playEffect("gameStart")
        self.currentPose = {}
        self.scene.pose = self.currentPose
        self.scene.setLighting('readyGame')

    def timedGameStart(self):
        self.scene.currentMessage = None
        self.gameState = "playing"
        self.enterNewPose()
        self.scene.setLighting('game')

    def timedGameEnd(self, now):
        self.sound.playEffect("gameOver")
        self.scene.currentMessage = "Game over %s %s" % (
            self.gameMatches, "match" if self.gameMatches == 1 else "matches")

        self.currentPose = {}
        self.gameState = "showScore"
        self.gameNext = now + 6
        self.scene.setLighting('train')

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
        colors = self.colors[:]
        random.shuffle(colors)
        colors = colors[:random.randrange(2, len(colors)+1)]

        out = {}
        y = .5
        prevWidth = 999
        while colors:
            maxWidth = min(prevWidth, len(colors))
            row = [colors.pop() for i in range(random.randrange(1, maxWidth+1))]
            x = - (len(row)-1) / 2
            for color in row:
                out[color] = (x, y)
                x += 1
            y += 1
            prevWidth = len(row)
        return out

    def poseMatch(self, positions1, positions2):
        if not positions1 or not positions2:
            return False
        pairs = colorPairs(positions2.keys())
        try:
            angles = []
            #print "\nuser:"
            for p in [positions1, positions2]:
                row = []
                for c1, c2 in pairs:
                    v = numpy.array(p[c1]) - p[c2]
                    v = v[:2]
                    offset = pi if p is positions1 else 0
                    flip = -1 if p is positions1 else 1
                    row.append(positiveAngle(flip*atan2(v[0], v[1]), offset))
                    #print "%s to %s %.3f" % (c1[0], c2[0], row[-1])
                #print ""
                angles.append(row)
            err = sum(x * x for x in map(diffAngle, zip(angles[0], angles[1])))
            dispatcher.send("err", txt="error=%.3f" % err)
            return err < .2
        except KeyError:
            return False

def colorPairs(colors):
    colors = sorted(colors)
    pairs = []
    for i in range(len(colors)):
        for j in range(i+1, len(colors)):
            pairs.append((colors[i], colors[j]))
    return pairs

def diffAngle((a1, a2)):
    if a2 < a1:
        a1,a2=a2,a1
    return min(a2-a1, 2*pi-a2+a1)

def positiveAngle(ang, offset):
    return (ang + pi + offset) % (2*pi)
