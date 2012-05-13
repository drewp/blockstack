from __future__ import division
from OpenGL import GL, GLUT, GLU
from gtk.gtkgl.apputils import GLScene
import numpy as num
import sys, random, pyglet, math, time, colorsys

import gtk
from timing import logTime

from pandac.PandaModules import loadPrcFileData, WindowProperties
from panda3d.core import PointLight,Spotlight, Vec4, Vec3, VBase4, PerspectiveLens, PandaNode
from panda3d.core import AmbientLight, DirectionalLight, ModelNode, PlaneNode, Fog, Texture, Material

class GameScene(object):
    def __init__(self, gtkParentWidget):


        self.pose = {}
        self.enter = 1 # 0..1 flies in the cubes
        self.currentMessage = self.cornerMessage = None
        self.videoFrame = None
        self.animSeed = 0

        self.gtkParentWidget = gtkParentWidget
        loadPrcFileData("", "window-type none")

        import direct.directbase.DirectStart # this sticks a ton into __builtins__
        self.base = base

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
        self.cubeNodes = {} # color: NodePath
        
    def init(self):
        """setup calls that can be repeated on code reload"""
        self.resetNodes()

        self.base.setBackgroundColor(0,0,0)

        cam = self.base.render.find("camera")
        # I don't know how to set cam position

        f = Fog("fog")
        f.setColor(0,0,0)
        f.setLinearRange(18, 25)
        self.base.render.setFog(f)

        self.videoWall, self.videoTexture = self.makeVideoWall(self.base.render)

        self.cubes = self.base.render.attachNewNode(ModelNode("cubes"))
        self.cubes.setPos(0, 20, -3)

        self.makeGround(self.cubes)
            
        pl = self.base.render.attachNewNode(PointLight("point"))
        pl.setPos(3, 10, 10)
        pl.node().setColor(Vec4(1, 1, 1, 1))
        self.base.render.setLight(pl)
        pl.node().setAttenuation( Vec3( 0, 0, 0.003 ) ) 

        slight = Spotlight('slight')
        slight.setColor(VBase4(1, 1, 1, 1))
        lens = PerspectiveLens()
        slight.setLens(lens)
        slnp = self.base.render.attachNewNode(slight)
        slnp.setPos(2, 50, 0)
        #self.base.render.setLight(slnp)

        self.base.render.ls()
        self.updateCubes()

    def makeVideoWall(self, parent): 
        w = self.base.loader.loadModel("plane")
        w.reparentTo(parent)
        w.setPos(5,20,0)
        w.setHpr(0, 180, 0)
        w.setScale(5, 1, 5)
        w.setTwoSided(True)
        tx = Texture("video")
        tx.setup2dTexture(256, 256, Texture.TUnsignedByte, Texture.FRgb8)
        tx.setRamImage("\x6f"*(256*256*3))
        w.setTexture(tx)

        m = Material("vid")
        m.setTwoside(True)
        m.setEmission((1,1,1,1))
        w.setMaterial(m)

        w.setFogOff()
        return w, tx

    def makeGround(self, parent):
        ground = self.base.loader.loadModel("plane")
        ground.setHpr(0, -90, 0)
        ground.setScale(10)
        ground.setColor(*colorsys.hsv_to_rgb(.6, .4, .35))
        ground.reparentTo(parent)

        m = Material("gnd")
        m.setAmbient(1,0,0)
        ground.setMaterial(m)
        
        return ground

    def getOrCreateCube(self, name):
        if name not in self.cubeNodes:
            cube = self.base.loader.loadModel("cube")
            cube.setName(name)
            cube.setScale(.5)
            cube.setColor(*self.previewColor(name))
            cube.reparentTo(self.cubes)
            cube.setPos(0, 0, 1)
            self.cubeNodes[name] = cube
            self.base.render.ls()
        return self.cubeNodes[name]

    def updateVideo(self):
        scl = self.videoFrame.scale_simple(256, 256, gtk.gdk.INTERP_BILINEAR)
        self.videoTexture.setRamImage(scl.get_pixels())

    def updateCubes(self):
        self.updateVideo()
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

    def refresh(self):
        if self.videoFrame:
            glPushMatrix()
            try:
                glTranslatef(4, 1.2, -1)
                glScalef(1.6, 1.2, 1)
                glScalef(1.2, 1.2, 1)
                self.imageCard(self.videoFrame)
            finally:
                glPopMatrix()

    def resize_panda_window(self, widget, request) :
        props = WindowProperties().getDefault()
        props = WindowProperties(self.base.win.getProperties())
        props.setOrigin(0, 0)
        props.setSize(request.width, request.height)
        props.setParentWindow(widget.window.xid)
        self.base.win.requestProperties(props)

class GameScenex(GLScene):

    def drawLightning(self, pos):
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glColor3f(1,1,0)
        glLineWidth(3)
        for s, e in pos:
            glBegin(GL_LINE_STRIP)
            for t in range(0, 100):
                t /= 100
                glVertex3f(s[0] + t*(e[0]-s[0]) + random.random()**4 * .2,
                           s[1] + t*(e[1]-s[1]) + random.random()**4 * .1,
                           3*math.sin(t*math.pi) + random.random()**4 * .1,
                           )
            glEnd()
        glPopAttrib()

    def display2d(self):
        if not self.currentMessage and not self.cornerMessage:
            return
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        GLU.gluOrtho2D(0, 640, 0, 480)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glDisable(GL_LIGHTING)
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        glColor3f(1,1,1)
        try:
            if self.currentMessage:
                glPushMatrix()
                try:
                    glTranslatef(640/2, 480/2, 0)
                    t = pyglet.text.Label(font_name='Arial', font_size=40,
                                          anchor_x="center", anchor_y="center",
                                          text=self.currentMessage)
                    t.draw()
                finally:
                    glPopMatrix()

            if self.cornerMessage:
                glPushMatrix()
                try:
                    glTranslatef(640-30, 480-30, 0)
                    t = pyglet.text.Label(font_name='Arial', font_size=20,
                                          anchor_x="right", anchor_y="bottom",
                                          text=self.cornerMessage)
                    t.draw()
                finally:
                    glPopMatrix()
            
        finally:
            glEnable(GL_LIGHTING)

    def imageCard(self, multiImage):
        """card facing +Z from -1<x<1 -1<y<1"""

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        try:
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_TEXTURE_2D)
            glDisable(GL_FOG)

            pixels = (multiImage
                      .scale_simple(256, 256, gtk.gdk.INTERP_BILINEAR)
                      .get_pixels_array())

            if not hasattr(self, "texId"):
                self.texId = glGenTextures(1)
                glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glBindTexture(GL_TEXTURE_2D, self.texId)

            # faster way would be to make an empty power-of-2 texture,
            # then use subimage2d to write the video-aspect rect into
            # it. Pick the video part with the tx coords.
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB,
                         pixels.shape[0], pixels.shape[1], 0,
                         GL_RGB, GL_UNSIGNED_BYTE, pixels)                

            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glDisable(GL_LIGHTING)

            glCallList(self.cardList)
        finally:
            glPopAttrib()
