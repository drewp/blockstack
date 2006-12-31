from __future__ import division
import pygame
import Image, ImageFilter
import Numeric as num

class MultiImage(object):
    def __init__(self, string, w, h):
        self.w, self.h = w, h
        self.string = string[:self.w * self.h * 3]

    def size(self):
        return self.w, self.h
        
    def asArray(self):
        a = num.fromstring(self.string, num.UnsignedInt8)
        a.shape = self.h, self.w, 3
        return a

    def asSurface(self):
        return pygame.image.fromstring(self.string, (self.w, self.h), "RGB")

    def asImage(self):
        return Image.fromstring("RGB", (self.w, self.h), self.string)

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
    
