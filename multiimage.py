from __future__ import division
import pygame
import Image, ImageFilter
import numpy as num

class MultiImage(object):
    def __init__(self, string, w, h, flipColor=False):
        self.w, self.h = w, h
        self.flipColor = flipColor
        assert len(string) == w * h * 3
        self.string = string

    def size(self):
        return self.w, self.h
        
    def asArray(self):
        a = num.fromstring(self.string, num.uint8)
        a.shape = self.h, self.w, 3

        if self.flipColor:
            red = num.copy(a[:,:,2])
            a[:,:,2] = a[:,:,0]
            a[:,:,0] = red
        
        return a

    def asSurface(self):
        return pygame.image.fromstring(self.string, (self.w, self.h), "RGB")

    def asImage(self):
        # findBlocks is going to modify the pic in place
        #if hasattr(self, 'pilImage'):
        #    return self.pilImage

        self.pilImage = Image.fromstring("RGB", (self.w, self.h), self.string)
        b,g,r = self.pilImage.split()
        self.pilImage = Image.merge("RGB", (r,g,b))
        return self.pilImage

    def asRgbString(self):
        return self.string

def writeArray():
    raise NotImplementedError
    h,w = L.shape
    b = num.repeat(L, 3, 1)
    b.shape = h,w,3   
    Image.fromstring("RGB",
                     (b.shape[1], b.shape[0]),
                     num.clip(b, 0, 255).astype('b').tostring()
                     ).save("diff.ppm")
    
