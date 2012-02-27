from __future__ import division
from math import atan2
import numpy as num

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
