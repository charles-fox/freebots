#standard stuff

import math
import pdb
import pprint
import inspect

def v(myobj):
    try:
        l=len(myobj) #is it a container - if so, recurse
        for x in myobj:
            v(x)
    except (TypeError, AttributeError):
        try:
            print myobj.toString() #does it have a nice toString method? If so, use it!
        except AttributeError:
            pprint.pprint(inspect.getmembers(myobj)) #else, use cheap version

def overlaps(s1,e1,s2,e2):  #start and ends of two objects 
    return ((s1<=e2-1)and(e2-1<=e1-1) or (s1<=s2)and(s2<=e1-1) or (s2<=s1)and(e1-1<=e2-1))

def frange(start, stop, step):
    r=[]
    x=float(start)
    while not(x>=stop-0.0000001):  #this is subtle for floats!
        r.append(x)
        x+=step
    return r


def fixAngle(th):   #ensure is always in [-math.pi,+math.pi)
        while th<-math.pi:
            th+=2*math.pi
        while th>=math.pi:
            th-=2*math.pi
        return th

def rescale(oldmin, oldmax, newmin, newmax, x):
    return float(newmin) +   float(x-oldmin)*float(newmax-newmin)/float(oldmax-oldmin)

