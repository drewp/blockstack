from __future__ import division
import gtk, numpy
from panda3d.core import Texture, Material, VBase4, PNMImage
from debug import logTime

class VideoWall(object):
    res = 256
    def __init__(self, loader, parentNodePath):
        w = loader.loadModel("plane")
        w.reparentTo(parentNodePath)
        size = 6
        w.setPos(3.5, 15, size / 2 - 3)
        w.setColor(1,0,0)
        w.setHpr(0, 180, 0)
        w.setScale(size, 1, size / 1.33)
        w.setTwoSided(True)
        
        self.tx = Texture("video")
        self.tx.setup2dTexture(self.res, self.res, Texture.TUnsignedByte, Texture.FRgb8)

        # this makes some important setup call
        self.tx.load(PNMImage(self.res, self.res))

        w.setTexture(self.tx)

        m = Material("vid")
        m.setTwoside(True)
        m.setEmission(VBase4(1,1,1,1))
        w.setMaterial(m)

        w.setFogOff()

    def updateFromPixbuf(self, pb):
        scaled = pb.scale_simple(self.res, self.res, gtk.gdk.INTERP_BILINEAR)

        # about 3ms
        n = numpy.fromstring(scaled.get_pixels(), dtype=numpy.uint8).reshape((-1,3))
        flipped = numpy.fliplr(n).tostring()
        
        self.tx.setRamImage(flipped)
