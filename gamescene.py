from __future__ import division
import numpy as num
import random, colorsys, time
from math import sin, cos
import gtk
from debug import logTime

from pandac.PandaModules import WindowProperties, DynamicTextFont, AntialiasAttrib
from panda3d.core import PointLight,Spotlight, Vec3, VBase3, VBase4, PerspectiveLens, AmbientLight, DirectionalLight, ModelNode, Fog, Texture, Material, TextureStage, PNMImage, Point3
from direct.gui.OnscreenText import OnscreenText

class GameScene(object):
    def __init__(self, gtkParentWidget):
        self.pose = {}
        self.enter = 1 # 0..1 flies in the cubes
        self.currentMessage = self.cornerMessage = None
        self.videoFrame = None
        self.animSeed = 0
        self.cubeNodes = {} # color: NodePath
        self.currentLighting = 'train'
        
        self.gtkParentWidget = gtkParentWidget

        self.base = base # from DirectStart

        props = WindowProperties().getDefault()
        props.setOrigin(0, 0)
        props.setSize(1,1)
        props.setParentWindow(self.gtkParentWidget.window.xid)
        self.base.openDefaultWindow(props=props)

        self.gtkParentWidget.connect("size_allocate", self.resize_panda_window)
        self.originalNodes = self.base.render.getChildren()

        self.init()

    def resetNodes(self):
        [n.removeNode()
         for n in self.base.render.getChildren()
         if n not in self.originalNodes]
        self.base.render.setLightOff()
        self.cubeNodes = {}

        for n in ['centerMessageNode', 'cornerMessageNode']:
            if getattr(self, n, None):
                getattr(self, n).destroy()
        
    def init(self):
        """setup calls that can be repeated on code reload"""
        self.resetNodes()

        self.base.setBackgroundColor(0, 0, 0)
        self.base.render.setShaderAuto() # pp shading
        self.base.render.setAttrib(
            AntialiasAttrib.make(AntialiasAttrib.MMultisample))
        
        if 1:
            cam = self.base.render.find("camera")
            # I don't know how to set cam position

            f = Fog("fog")
            f.setColor(0,0,0)
            f.setLinearRange(18, 25)
            self.base.render.setFog(f) 

            import videowall
            reload(videowall)
            self.videoWall = videowall.VideoWall(self.base.loader, self.base.render)

        self.cubes = self.base.render.attachNewNode(ModelNode("cubes"))
        self.cubes.setPos(-4.3, 18, -3)
        ground = self.makeGround(self.cubes)

        lights = self.base.render.attachNewNode("lights")
        self.makeLights(lights)

        self.centerMessageNode, self.cornerMessageNode = self.makeMessages()

        self.setLighting(self.currentLighting)
        self.base.render.ls()

    def makeLights(self, lights):
        def makeSpot(parent, color=VBase4(1,1,1,1), fov=8, atten=.003):
            x = parent.attachNewNode(Spotlight("spot"))
            x.node().setColor(color)
            lens = PerspectiveLens()
            lens.setFov(fov)
            x.node().setLens(lens)
            x.node().setAttenuation(VBase3(0,0,atten))
            return x

        self.trainLights = lights.attachNewNode("trainLights")
        if 1:
            pl = self.trainLights.attachNewNode(PointLight("point"))
            pl.setPos(2, 10, 10)
            #pl.node().setColor(VBase4(.7, .7, .7, 1))
            pl.node().setAttenuation( Vec3( 0, 0, 0.005 ) )
            #pl.node().setShadowCaster(True, 512, 512)
            self.base.render.setLight(pl)
            pl.node().setShadowCaster(True)

            spot = makeSpot(self.trainLights, VBase4(1, 1, 1, 1), 8)
            spot.setPos(2, 0, 18)
            spot.lookAt(self.cubes, Point3(0,.6,0))
            self.base.render.setLight(spot)

        self.gameLights = lights.attachNewNode("gameLights")
        if 1:
            bg = self.gameLights.attachNewNode(PointLight("point"))
            bg.node().setColor(VBase4(.1,.2,.6,1))
            bg.setPos(-6, 15, 2)
            self.base.render.setLight(bg)
            bg.node().setShadowCaster(True)


            up = makeSpot(self.gameLights, color=VBase4(.6,.6,.6,1), fov=25,
                          atten=.009)
            up.setPos(self.cubes.getPos().x, 10, .4)
            up.lookAt(self.cubes, Point3(0, 0, 1.3))
            self.base.render.setLight(up)

            self.rotLights = []
            for color, pos in [
                (VBase4(1, 1, 0, 1), Point3(4, 10, 10)),
                (VBase4(0, .7, 0, 1), Point3(-4, 10, 10)),
                (VBase4(0, .6, 1, 1), Point3(0, 20, 10)),
                ]:
                s1 = makeSpot(self.gameLights, color=color, fov=8)
                s1.setPos(pos)
                s1.lookAt(self.cubes)
                self.base.render.setLight(s1)
                self.rotLights.append(s1)

    def setLighting(self, mode):
        self.currentLighting = mode
        r = self.base.render
        if mode == 'train':
            map(r.setLight, self.trainLights.getChildren())
            map(r.clearLight, self.gameLights.getChildren())
        elif mode == 'readyGame':
            map(r.clearLight, self.trainLights.getChildren())
            map(r.setLight, self.gameLights.getChildren())
        elif mode == 'game':
            1
        print "\nnew lighting"
        self.base.render.ls()

    def updateLighting(self):
        now = time.time()
        for i, x in enumerate(self.rotLights):
            x.setPos(30 * sin(now / 15 + i*2), 20 + 30 * cos(now / 15 +i*2), 5)
            x.lookAt(self.cubes)

    def makeMessages(self):
        # note, Blox2 has nothing but a-zA-z0-9, and other chars will
        # make panda segfault
        font = DynamicTextFont("/usr/share/fonts/truetype/aenigma/Blox2.ttf")
        font.setPixelSize(90)
        center = OnscreenText(text="cEnTeR mEsSaGe", fg=(1,1,1,1),
                              font=font, scale=.3,
                              shadow=(0,0,0,1), shadowOffset=(.1, .1),
                              )

        font = DynamicTextFont("/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-B.ttf")
        font.setPixelSize(30)
        corner = OnscreenText(text="corner message", fg=(1,1,1,1),
                              font=font, scale=.09, pos=(-1.3, .9),
                              shadow=(0,0,0,1), shadowOffset=(.1, .1),
                              )
        return center, corner
    
    def makeGround(self, parent):
        ground = self.base.loader.loadModel("cube")
        ground.setScale(20, 5, .2)
        ground.setPos(0, 0, -.2)
        ground.setColor(VBase4(.33,.42,.55,1))#*colorsys.hsv_to_rgb(.6, .4, .55))
        ground.reparentTo(parent)

        m = Material("gnd")
        m.setDiffuse(VBase4(1,1,1,1))
        #ground.setMaterial(m)
        
        return ground

    def getOrCreateCube(self, name):
        if name not in self.cubeNodes:
            cube = self.base.loader.loadModel("cube")
            cube.setName(name)
            cube.setScale(.5)
            cube.reparentTo(self.cubes)
            cube.setPos(0, 0, 1)
            self.cubeNodes[name] = cube
        c = self.cubeNodes[name]
        c.setColor(*self.previewColor(name))
        return c

    def updateVideo(self):
        if not getattr(self, 'videoWall', None):
            return
        self.videoWall.updateFromPixbuf(self.videoFrame)
 
    def updateMessages(self):
        if not getattr(self, 'centerMessageNode', None):
            return
        altCase = ''.join([c.upper() if i % 2 else c.lower()
                           for i,c in enumerate(self.currentMessage or "")])
        self.centerMessageNode.setText(altCase)
        self.cornerMessageNode.setText(self.cornerMessage or "")

    def updateCubes(self):
        if not getattr(self, 'cubes', None):
            return
        R = random.Random(self.animSeed)
        for name, pos in self.pose.items():
            pos = num.array(pos) + [0, 10 * (1 - self.enter), 0]
            if self.explode:
                noise= num.array([R.uniform(0,1),
                                  R.uniform(0,1),
                                  R.uniform(0,1)])
                jitter = (noise - [.5, .8, 0]) * [2,5,.1]
                explodeDir = (pos + jitter)
                pos = pos + explodeDir * 10 * (self.explode ** .8)
            c = self.getOrCreateCube(name)
            c.setPos(*pos[:3])
            c.setHpr(200 * self.explode, 200 * self.explode, 0)
        self.hideUnusedCubes(self.pose.keys())

    def hideUnusedCubes(self, used):
        [c.setPos(0, -100, 0)
         for n, c in self.cubeNodes.items()
         if n not in used]

    def resize_panda_window(self, widget, request) :
        props = WindowProperties().getDefault()
        props = WindowProperties(self.base.win.getProperties())
        props.setOrigin(0, 0)
        props.setSize(request.width, request.height)
        props.setParentWindow(widget.window.xid)
        self.base.win.requestProperties(props)
