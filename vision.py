from __future__ import division
from math import atan2
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
            # xflip is for the camera facing the user;
            # yflip is for some other reason I can't remember
            ret[colorName] = [1 - (ctr[0] / a.shape[1]),
                              1 - (ctr[1] / a.shape[0])]

            if feedbackSurf:
                x, y = ctr / [a.shape[1], a.shape[0]] * multiImage.size()
                feedbackSurf.fill((255,255,255), (x, y, 10, 10))

    return ret


def fixNegative(ang):
    if ang < -3.0:
        return 3.1415
    return ang

def comparePose(positions1, positions2):
    try:
        angles = []
        for p in [positions1, positions2]:
            v1 = num.array(p['green']) - p['red']
            v2 = num.array(p['blue']) - p['green']
            angles.append(num.array([fixNegative(atan2(v1[0], v1[1])),
                                     fixNegative(atan2(v2[0], v2[1]))]))
        #print angles[0], angles[1]
        err = sum(x * x for x in (angles[0] - angles[1]))
        return err < .5
    except KeyError:
        return False
