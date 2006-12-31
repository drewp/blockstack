from __future__ import division
import Image
import Numeric as num
from multiimage import MultiImage

colors = dict(red=(203, 131, 146),
              blue=(135, 148, 199),
              green=(37, 102, 118))

def findBlocks(multiImage, feedbackSurf=None):
    """colorName : (x,y)
    in relative (0 to 1) coords. Draws on the optional pygame surface"""
    
    thumb = multiImage.asImage()
    thumb.thumbnail((43//2, 36//2), Image.ANTIALIAS)

    a = MultiImage(thumb.tostring(), thumb.size[0], thumb.size[1]).asArray()

    ret = {}
    for colorName, detectColor in colors.items():
        b = num.absolute(a.astype('f') - detectColor)

        L = num.sum(b, -1)

        goodMatch = L < 100

        hits = 0
        ctr = num.zeros(2)

        for y in range(a.shape[0]):
            for x in range(a.shape[1]):
                if goodMatch[y][x]:
                    if feedbackSurf:
                        x1, y1 = (num.array([x, y]) /
                                  [a.shape[1], a.shape[0]] * multiImage.size())
                        feedbackSurf.fill((0,0,0), (x1-1, y1-1, 10, 10))
                        feedbackSurf.fill(detectColor, (x1, y1, 8, 8))
                    hits += 1
                    ctr += [x, y]
        if hits > .10 * (a.shape[0] *  a.shape[1]):
            ctr = ctr / hits
            ret[colorName] = ctr[0] / a.shape[1], 1 - (ctr[1] / a.shape[0])

            if feedbackSurf:
                x, y = ctr / [a.shape[1], a.shape[0]] * multiImage.size()
                feedbackSurf.fill((255,255,255), (x, y, 10, 10))

    return ret
