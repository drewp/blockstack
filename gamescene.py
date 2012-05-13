from __future__ import division
from OpenGL import GL, GLUT, GLU
from gtk.gtkgl.apputils import GLScene
import numpy as num
import sys, random, pyglet, math, time, colorsys

import gtk
from timing import logTime

from pandac.PandaModules import loadPrcFileData, WindowProperties
from panda3d.core import PointLight,Spotlight, Vec4, Vec3, VBase4, PerspectiveLens, PandaNode
from panda3d.core import AmbientLight, DirectionalLight

class GameScene(object):
    def __init__(self, gtkParentWidget):
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
        
    def init(self):
        """setup calls that can be repeated on code reload"""
        self.resetNodes()
        panda = self.base.loader.loadModel("panda")
        panda.setColor(1,1,0)
        panda.reparentTo(self.base.render)
        panda.setPos(0, 40, -5)

        pl = self.base.render.attachNewNode( PointLight( "redPointLight" ) )
        pl.node().setColor( Vec4( .9, .8, .8, 1 ) )
        self.base.render.setLight(pl)
        pl.node().setAttenuation( Vec3( 0, 0, 0.05 ) ) 

        slight = Spotlight('slight')
        slight.setColor(VBase4(1, 1, 1, 1))
        lens = PerspectiveLens()
        slight.setLens(lens)
        slnp = self.base.render.attachNewNode(slight)
        slnp.setPos(2, 10, 0)
        mid = PandaNode('mid')
        panda.attachNewNode(mid)
    #    slnp.lookAt(mid)
        self.base.render.setLight(slnp)

    def resize_panda_window(self, widget, request) :
        props = WindowProperties().getDefault()
        props = WindowProperties(self.base.win.getProperties())
        props.setOrigin(0, 0)
        props.setSize(request.width, request.height)
        props.setParentWindow(widget.window.xid)
        self.base.win.requestProperties(props)


def cube(color=(1,1,1), center=(0,0,0), rot=(0, 0,0,0), side=1, wire=False,
         tess=1):
    glColor3f(*color)
    glMaterialfv(GL_FRONT, GL_DIFFUSE, (tuple(color)+(1,)))
    glPushMatrix()
    try:
        glTranslatef(*center)
        glRotatef(*rot)
        glScalef(side, side, side)
        if wire:
            GLUT.glutWireCube(1)
        else:
            tessCube(tess)
    finally:
        glPopMatrix()

_tcl = {} # tess : displaylist
def tessCube(tess):
    if tess not in _tcl:
        _tcl[tess] = glGenLists(1)
        glNewList(_tcl[tess], GL_COMPILE)
        A, B = -.5, .5
        glBegin(GL_QUADS)
        P = glVertex3f
        N = glNormal3f
        for x in range(tess):
            for y in range(tess):
                u, U = x/tess-.5, (x+1)/tess-.5 
                v, V = y/tess-.5, (y+1)/tess-.5
                N(-1,0,0); P(A,u,v); P(A,u,V); P(A,U,V); P(A,U,v) # left
                N(1,0,0);  P(B,u,v); P(B,U,v); P(B,U,V); P(B,u,V) # right
                N(0,-1,0); P(u,A,v); P(U,A,v); P(U,A,V); P(u,A,V) # bottom
                N(0,1,0);  P(u,B,v); P(u,B,V); P(U,B,V); P(U,B,v) # top
                N(0,0,-1); P(u,v,A); P(u,V,A); P(U,V,A); P(U,v,A) # back
                N(0,0,1);  P(u,v,B); P(U,v,B); P(U,V,B); P(u,V,B) # front
        glEnd()
        glEndList()
    glCallList(_tcl[tess])

def groundPlane():
    glPushMatrix()
    glTranslatef(1,0,0)
    glScalef(10, .01, 5)
    cube(color=colorsys.hsv_to_rgb(.6, .4, .005), tess=60)
    glPopMatrix()

class GameScenex(GLScene):
    def __init__(self):
        GLScene.__init__(self,
                         gtk.gdkgl.MODE_RGB   |
                         gtk.gdkgl.MODE_DEPTH |
                         gtk.gdkgl.MODE_DOUBLE)

        self.pose = {}
        self.enter = 1 # 0..1 flies in the cubes
        self.currentMessage = self.cornerMessage = None
        self.videoFrame = None
        self.animSeed = 0

    def init(self):
        
        GLUT.glutInit(sys.argv)

        glClearColor(0.0, 0.0, 0.0, 0.0)
        glShadeModel(GL_FLAT)
        glEnable(GL_LINE_SMOOTH)

        glColorMaterial(GL_FRONT, GL_DIFFUSE)
        glDisable(GL_COLOR_MATERIAL)

        glLightfv(GL_LIGHT0, GL_DIFFUSE, colorsys.hsv_to_rgb(0,0,3.8) + (1,))
        glLightfv(GL_LIGHT0, GL_SPECULAR, [.5,.5,.5, 1])
        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 3.0, 5.5, 0.0])
        glEnable(GL_LIGHT0)

        glLightfv(GL_LIGHT1, GL_DIFFUSE, colorsys.hsv_to_rgb(0,0,.5) + (1,))
        glLightfv(GL_LIGHT1, GL_POSITION, [10.0, 3.0, 3.0, 0.0])
        glEnable(GL_LIGHT1)

        glLightfv(GL_LIGHT2, GL_DIFFUSE, [.8, .8, .8, 1])
        glLightfv(GL_LIGHT2, GL_SPECULAR, [.7, .7, .7, 1])
        glDisable(GL_LIGHT2)

        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.0, 0.0, 0.0, 1.0])
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glClearDepth(1.0)
        glCullFace(GL_BACK)
        glEnable(GL_CULL_FACE)

        glFogfv(GL_FOG_COLOR, (0,0,0,1))
        glFogf(GL_FOG_DENSITY, 0.10)
        glFogf(GL_FOG_START, 2)
        glFogf(GL_FOG_END, 50)
        glFogf(GL_FOG_COORD_SRC, GL_FRAGMENT_DEPTH)
        glHint(GL_FOG_HINT, GL_NICEST)
        glEnable(GL_FOG)
        
        self.cardList = self.makeCard()

    def reshape(self, width, height):
        glViewport (0, 0, width, height)

    def setup3d(self, width, height):
        glMatrixMode (GL_PROJECTION)
        glLoadIdentity()
        glFrustum(-1.0, 1.0, -height/width, height/width, 1.5, 20.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        GLU.gluLookAt(1.7, 1.5, 6.1,
                      1.7, 0.8, 0.0,
                      0.0, 1.0, 0.0)

    def display(self, width, height):
        self._display(width, height)

    def _display(self, width, height):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.setup3d(width, height)

        if 0: # light testing
            glLightfv(GL_LIGHT0, GL_POSITION,
                      [math.cos(time.time()),
                       3.0 + 2.3*math.sin(time.time()),
                       7.6, 0.0])

            glLightfv(GL_LIGHT2, GL_POSITION,
                      [4 * math.cos(time.time()),
                       .3,
                       4 * math.sin(time.time()),
                       0.0])

        glDisable(GL_TEXTURE_2D)

        glMaterialfv(GL_FRONT, GL_AMBIENT, [0,0,0,0])
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0,0,0,0])
        glMaterialf(GL_FRONT, GL_SHININESS, 10)      
        groundPlane()

        glMaterialfv(GL_FRONT, GL_AMBIENT, [0,0,0,0])
        glMaterialfv(GL_FRONT, GL_SPECULAR, [.5,.5,.5,1])
        glMaterialf(GL_FRONT, GL_SHININESS, 10)
        self.drawCubes()

        #self.drawLightning([((4,2,0), (-1, 1.5, 0))])

        if self.videoFrame:
            glPushMatrix()
            try:
                glTranslatef(4, 1.2, -1)
                glScalef(1.6, 1.2, 1)
                glScalef(1.2, 1.2, 1)
                self.imageCard(self.videoFrame)
            finally:
                glPopMatrix()

        #glCopyPixels(0,0,width,height, GL_DEPTH)
        self.display2d()

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

    def drawCubes(self):
        R = random.Random(self.animSeed)
        for name, pos in self.pose.items():
            pos = num.array(pos) + [0,6*(1-self.enter),0]
            rot = (0,0,0,0)
            if self.explode:
                noise= num.array([R.uniform(0,1),
                                  R.uniform(0,1),
                                  R.uniform(0,1)])
                jitter = (noise - [.5, 0, .5]) * [2,.1,5]
                explodeDir = (pos + jitter)
                pos = pos + explodeDir * 10 * self.explode
                rot = (200 * self.explode, 1,1,1)
            color = num.array(self.previewColor(name))
            cube(color=color, center=pos, rot=rot, tess=10)

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

    def makeCard(self):
        n = glGenLists(1)
        glNewList(n, GL_COMPILE)
        glColor3f(1,1,1)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0); glVertex3f(-1.0, -1.0,  1.0)
        glTexCoord2f(1.0, 1.0); glVertex3f( 1.0, -1.0,  1.0)
        glTexCoord2f(1.0, 0.0); glVertex3f( 1.0, 1.0,  1.0)
        glTexCoord2f(0.0, 0.0); glVertex3f(-1.0, 1.0,  1.0)
        glEnd()
        glEndList()
        return n

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
