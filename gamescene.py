from __future__ import division
import numpy as num
import random, colorsys
import gtk
from debug import logTime

from pandac.PandaModules import WindowProperties, DynamicTextFont, AntialiasAttrib
from panda3d.core import PointLight,Spotlight, Vec3, VBase4, PerspectiveLens, AmbientLight, DirectionalLight, ModelNode, Fog, Texture, Material, TextureStage, PNMImage
from direct.gui.OnscreenText import OnscreenText

class GameScene(object):
    def __init__(self, gtkParentWidget):
        self.pose = {}
        self.enter = 1 # 0..1 flies in the cubes
        self.currentMessage = self.cornerMessage = None
        self.videoFrame = None
        self.animSeed = 0
        self.cubeNodes = {} # color: NodePath
        
        self.gtkParentWidget = gtkParentWidget

        self.base = base # from DirectStart

        props = WindowProperties().getDefault()
        props.setOrigin(0, 0)
        props.setSize(1,1)
        props.setParentWindow(self.gtkParentWidget.window.xid)
        self.base.openDefaultWindow(props=props)

        self.gtkParentWidget.connect("size_allocate", self.resize_panda_window)
        self.originalNodes = self.base.render.getChildren()

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

        self.base.setBackgroundColor(0, .2, 0)
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

        if 1:
            self.cubes = self.base.render.attachNewNode(ModelNode("cubes"))
            self.cubes.setPos(-2.3, 20, -3)
            ground = self.makeGround(self.cubes)

        if 1:
            pl = self.base.render.attachNewNode(PointLight("point"))
            pl.setPos(2, 10, 10)
            #pl.node().setColor(VBase4(.7, .7, .7, 1))
            pl.node().setAttenuation( Vec3( 0, 0, 0.005 ) )
            #pl.node().setShadowCaster(True, 512, 512)
            self.base.render.setLight(pl)

        if 1:
            spot = Spotlight('spot')
            spot.setColor(VBase4(1, 1, 1, 1))
            lens = PerspectiveLens()
            lens.setFov(5)
            spot.setLens(lens)
            
            spotNode = self.base.render.attachNewNode(spot)
            spotNode.setPos(2, 0, 10)
            spotNode.lookAt(self.cubes)
            self.base.render.setLight(spotNode)

        self.centerMessageNode, self.cornerMessageNode = self.makeMessages()

        self.updateCubes()
        self.base.render.ls()

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
                              font=font, scale=.1, pos=(-1, .9),
                              shadow=(0,0,0,1), shadowOffset=(.1, .1),
                              )
        return center, corner
    
    def makeGround(self, parent):
        ground = self.base.loader.loadModel("plane")
        ground.setHpr(0, -90, 0)
        ground.setScale(10)
        ground.setColor(*colorsys.hsv_to_rgb(.6, .4, .55))
        ground.reparentTo(parent)

        m = Material("gnd")
        m.setDiffuse(VBase4(1,1,1,1))
        ground.setMaterial(m)
        
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
                jitter = (noise - [.5, .5, 0]) * [2,5,.1]
                explodeDir = (pos + jitter)
                pos = pos + explodeDir * 10 * self.explode
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
