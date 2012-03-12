from OpenGL.GL import *
from OpenGL import GL, GLUT, GLU
from gtk.gtkgl.apputils import GLScene, GLArea
import numpy as num
import random, sys

import gtk
import time

def cube(color=(1,1,1), center=(0,0,0), side=1, wire=False):
    glColor3f(*color)
    glPushMatrix()
    glTranslatef(*center)
    if wire:
        GLUT.glutWireCube(side)
    else:
        GLUT.glutSolidCube(side)
    glPopMatrix()

def groundPlane():
    glPushMatrix()
    glScalef(10, .01, 5)
    cube(color=(.2, .2, 1))
    glPopMatrix()

colors = {
    'red' : [255,0,0],
    'green' : [0,255,0],
    'blue' : [0,0,255],
    }

class GameScene(GLScene):
    def init(self):
        GLScene.__init__(self,
                         gtk.gdkgl.MODE_RGB   |
                         gtk.gdkgl.MODE_DEPTH |
                         gtk.gdkgl.MODE_DOUBLE)

        self.pose = {}
        GLUT.glutInit(sys.argv)

        glClearColor(0.0, 0.0, 0.0, 0.0)
#        glShadeModel(GL_SMOOTH)
        glEnable(GL_COLOR_MATERIAL)

        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 3.0, 6.0, 0.0])
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
#        glEnable(GL_DEPTH_TEST)
        glCullFace(GL_BACK)
        glEnable(GL_CULL_FACE)

        self.cardList = self.makeCard()

    def reshape(self, width, height):
        glViewport (0, 0, width, height)
        glMatrixMode (GL_PROJECTION)
        glLoadIdentity()
        glFrustum (-1.0, 1.0, -1.0, 1.0, 1.5, 20.0)
        glMatrixMode (GL_MODELVIEW)

    def display(self, width, height):
        t1 = time.time()

        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity ()
        GLU.gluLookAt (0.0, 2.0, 5.0,
                       0.0, 0.5, 0.0,
                       0.0, 1.0, 0.0)

        glDisable(GL_TEXTURE_2D)

        groundPlane()

        for name, pos in self.pose.items():
            color = num.array(colors[name]) / 255
            cube(color=color, center=pos)
            cube(color=color, center=pos, wire=True)

        glFlush()

        print "draw", time.time() - t1

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
