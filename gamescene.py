from __future__ import division
from OpenGL.GL import *
from OpenGL import GL, GLUT, GLU
from gtk.gtkgl.apputils import GLScene
import numpy as num
import sys, random

import gtk
import time

def cube(color=(1,1,1), center=(0,0,0), rot=(0, 0,0,0), side=1, wire=False):
    glColor3f(*color)
    glPushMatrix()
    glTranslatef(*center)
    glRotatef(*rot)
    if wire:
        GLUT.glutWireCube(side)
    else:
        GLUT.glutSolidCube(side)
    glPopMatrix()

def groundPlane():
    glPushMatrix()
    glScalef(10, .01, 5)
    cube(color=[.005, .005, .010])
    glPopMatrix()

colors = {
    'red' : [255,0,0],
    'green' : [0,255,0],
    'blue' : [0,0,255],
    }

class GameScene(GLScene):
    def __init__(self):
        GLScene.__init__(self,
                         gtk.gdkgl.MODE_RGB   |
                         gtk.gdkgl.MODE_DEPTH |
                         gtk.gdkgl.MODE_DOUBLE)

        self.pose = {}
        self.enter = 1 # 0..1 flies in the cubes

    def init(self):
        
        GLUT.glutInit(sys.argv)

        glClearColor(0.0, 0.0, 0.0, 0.0)
        glShadeModel(GL_SMOOTH)

        glColorMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)

        glLightfv(GL_LIGHT0, GL_DIFFUSE, [.8, .8, .8, 1])
        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 3.0, 6.0, 0.0])
        glEnable(GL_LIGHT0)

        glLightfv(GL_LIGHT1, GL_DIFFUSE, [.6, .4, .4, 1])
        glLightfv(GL_LIGHT1, GL_POSITION, [4.0, 3.0, 6.0, 0.0])
        glEnable(GL_LIGHT1)

        #glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        glCullFace(GL_BACK)
        glEnable(GL_CULL_FACE)

        
        glFogfv(GL_FOG_COLOR, (0,0,0,1))
        glFogf(GL_FOG_DENSITY, 0.10)
        glFogf(GL_FOG_START, 5.0)
        glFogf(GL_FOG_END, 20.0)
        glEnable(GL_FOG)
        

        self.cardList = self.makeCard()

    def reshape(self, width, height):
        glViewport (0, 0, width, height)
        glMatrixMode (GL_PROJECTION)
        glLoadIdentity()
        glFrustum (-1.0, 1.0, -1.0, 1.0, 1.5, 20.0)
        glMatrixMode (GL_MODELVIEW)

    def display(self, width, height):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity ()
        GLU.gluLookAt (0.0, 2.0, 5.0,
                       0.0, 0.5, 0.0,
                       0.0, 1.0, 0.0)

        glDisable(GL_TEXTURE_2D)

        groundPlane()
        R = random.Random(self.animSeed)
        for name, pos in self.pose.items():
            pos = num.array(pos) + [0,0,-20*(1-self.enter)]
            rot = (0,0,0,0)
            if self.explode:
                noise= num.array([R.uniform(0,1), R.uniform(0,1), R.uniform(0,1)])
                jitter = (noise - [.5, 0, .5]) * [2,.1,5]
                explodeDir = (pos + jitter)
                pos = pos + explodeDir * 10 * self.explode
                rot = (200 * self.explode, 1,1,1)
            color = num.array(colors[name]) / 255
            cube(color=color, center=pos, rot=rot)

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
        textureData = multiImage.asImage()
        textureData = textureData.resize((256, 256)).tostring()

        glBindTexture(GL_TEXTURE_2D, 0)
        glTexImage2D( GL_TEXTURE_2D, 0, GL_RGB,
                      256, #multiImage.size()[0],
                      256, #multiImage.size()[1],
                      0,
                      GL_RGB, GL_UNSIGNED_BYTE, textureData)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        glCallList(self.cardList)
