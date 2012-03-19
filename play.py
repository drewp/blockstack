from __future__ import division
import random, time
import numpy
from math import atan2, pi
from timing import logTime
from louie import dispatcher

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
            self.currentPose = self.makePose()
        self.startAnim("entering", .3)
        self.sound.playEffect('swoosh')

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

        if self.gameState == "ready":
            if now > self.timedGameStart:
                self.scene.currentMessage = None
                self.gameState = "playing"
                self.enterNewPose()
                
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
                self.currentMessage = "Game over: %s matches" % self.gameMatches
                self.currentPose = {}
                self.gameState = "showScore"
                self.gameNext = now + 3
        elif self.gameState == "showScore":
            if now  > self.gameNext:
                self.currentMessage = None
                self.gameState = "none"
                self.setGameDesc("")
                self.enterNewPose()
                
        self.scene.animSeed = self.animSeed
        self.scene.enter = self.animPos(now, 'entering', 1, bounce=True)
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
            self.startAnim("explode", .7)

        self.drawPose(self.currentPose)

    def startTimedGame(self):
        self.timedGameStart = time.time() + 5
        self.timedGameEnd = self.timedGameStart + 60
        self.gameMatches = 0
        self.gameState = "ready"
        self.scene.currentMessage = "Ready"
        self.sound.playEffect("gameStart")
        self.currentPose = {}

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
        colors = ['yellow', 'blue', 'green', 'purple']
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
                out[color] = (x, y, 0)
                x += 1
            y += 1
            prevWidth = len(row)
        return out

    def poseMatch(self, positions1, positions2):
        pairs = colorPairs(positions2.keys())
        try:
            angles = []
            for p in [positions1, positions2]:
                row = []
                for c1, c2 in pairs:
                    v = numpy.array(p[c1]) - p[c2]
                    v = v[:2]
                    offset = pi if p is positions1 else 0
                    flip = -1 if p is positions1 else 1
                    row.append(positiveAngle(flip*atan2(v[0], v[1]), offset))
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
