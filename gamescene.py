from OpenGL.GL import *
from OpenGL import GL, GLUT, GLU
from gtk.gtkgl.apputils import GLScene, GLArea
import numpy as num
import random, sys

import gtk
import time

import vision

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



class GameScene(GLScene):
    def init(self):
        GLScene.__init__(self,
                         gtk.gdkgl.MODE_RGB   |
                         gtk.gdkgl.MODE_DEPTH |
                         gtk.gdkgl.MODE_DOUBLE)

        self.positions2 = {}
        
        GLUT.glutInit(sys.argv)

        glClearColor (0.0, 0.0, 0.0, 0.0)
        glShadeModel (GL_SMOOTH)
        glEnable(GL_COLOR_MATERIAL)

        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 3.0, 3.0, 0.0])
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        glLightModelfv(GL_LIGHT_MODEL_LOCAL_VIEWER, [0])

        #glFrontFace(GL_CW)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        #glEnable(GL_AUTO_NORMAL)
        #glEnable(GL_NORMALIZE)
        glEnable(GL_DEPTH_TEST) 

        self.cardList = glGenLists(1)
        glNewList(self.cardList, GL_COMPILE)
        glColor3f(1,1,1)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0); glVertex3f(-1.0, -1.0,  1.0)
        glTexCoord2f(1.0, 1.0); glVertex3f( 1.0, -1.0,  1.0)
        glTexCoord2f(1.0, 0.0); glVertex3f( 1.0, 1.0,  1.0)
        glTexCoord2f(0.0, 0.0); glVertex3f(-1.0, 1.0,  1.0)
        glEnd()
        glEndList()

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
        GLU.gluLookAt (0.0, 0.7, 8.0,
                       0.0, 0.5, 0.0,
                       0.0, 1.0, 0.0)

        glDisable(GL_TEXTURE_2D)

        #global positions2, correctFrameStart

        groundPlane()

        matching = False
        glPushMatrix()
        if 0:
            glTranslatef(1, -.9, 3.2)
            # flip to compensate for the camera facing the user
            glScalef(-1, 1, 1)

            glDisable(GL_LIGHTING)
            glEnable(GL_TEXTURE_2D)

            # without threads, i call grab() here
            #grab.grab()

            if 0:#grab.lastFrame:
                self.imageCard(grab.lastFrame)
                if grab.lastPosition:
                    for colorName, pos in grab.lastPosition.items():
                        cube(color=(x / 255 for x in vision.colors[colorName]),
                             center=(pos[0] * 2 - 1, pos[1] * 2 - 1, 1),
                             side=.1, wire=True)

                    matching = vision.comparePose(grab.lastPosition, positions2)

            glEnable(GL_LIGHTING)
            glDisable(GL_TEXTURE_2D)
        glPopMatrix()

        for name, pos in self.positions2.items():
            color = num.array(vision.colors[name]) / 255
            if matching:
                color = [.7 + .3 * x for x in color]
            cube(color=color, center=pos)

        if matching:
            if correctFrameStart is None:
                correctFrameStart = time.time()
            if time.time() > correctFrameStart + .5:
                self.positions2 = newPositions()
                correctFrameStart = None
                beep.play()
        else:
            correctFrameStart = None


        glFlush()

        print "draw", time.time() - t1

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
