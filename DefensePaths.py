import math, random
from panda3d.core import *


def cloud(radius = 1):
    """
    Creates a vec3 of Random XYZ coordinates within range (-radius, radius)
    """
    x = 2 * random.random() - 1 #Coordinates will be range of -1,1
    y = 2 * random.random() - 1 #Coordinates will be range of -1,1
    z = 2 * random.random() - 1 #Coordinates will be range of -1,1
    
    unitVec = Vec3(x, y, z)
    unitVec.normalize()
    
    return unitVec * radius

def baseballSeams(step, numSeams, B, F= 1):
    time = step / float(numSeams) * 2 * math.pi
    
    F4 = 0
    
    R = 1
    
    xxx = math.cos(time) - B * math.cos(3 * time)
    yyy = math.sin(time) + B * math.sin(3 * time)
    zzz = F * math.cos(2 * time) + F4 * math.cos(4 * time)
    
    rrr = math.sqrt(xxx ** 2 + yyy ** 2 + zzz ** 2)
    
    x = R * xxx / rrr
    y = R * yyy / rrr
    z = R * zzz / rrr
    
    return Vec3(x, y, z)

def XYRing(position):
    x = math.cos(position * math.pi * 2.0)
    y = math.sin(position * math.pi * 2.0) 
    return Vec3(x, y, 0)

def YZRing(position):
    y = math.cos(position * math.pi * 2.0)
    z = math.sin(position * math.pi * 2.0) 
    return Vec3(0, y , z)

def XZRing(position):
    x = math.cos(position * math.pi * 2.0)
    z = math.sin(position * math.pi * 2.0)  
    return Vec3(x, 0, z)
    