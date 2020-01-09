from bg import *
from hc import *
#import random

import sys
import traceback


def isCloseTo(tx,tz, mx,mz):  #target and estiMated locations; true if close.
    thresh=1.5
    return ((abs(tx-mx)<thresh) and (abs(tz-mz)<thresh))


class CIceaMeat:
    def __init__(self):
        self.hunger=0.0
        self.thirst = 0.5

        self.BG = BasalGanglia(n=2)
        self.ptHC = PreTrainedHippocampus()
        self.target_x = 0.0
        self.target_z = 0.0

    def step(self, ins):
        print ins
        
        ins_pyrobrahms = ins[0]
        x=ins_pyrobrahms[0]
        z=ins_pyrobrahms[1]

        self.hunger += 0.02
        self.thirst += 0.03
        if self.hunger > 1.0:  #cap at 1.0 (full strength)
            self.hunger=1.0
        if self.thirst>1.0:
            self.thirst=1.0

        bg_input = [self.hunger, self.thirst]
        bg_out = self.BG.step(bg_input)

        #print "BGOUT:"
        #print bg_out
        
        x_hat, z_hat = self.ptHC.step(x,z,[])   #pretrained hippocampus step

        if isCloseTo(x, z, 0.0, 0.0):  #TODO should be HC estimates
           #we are at the center of the maze. Look at BG to decide where to go.
           if (bg_out[0] > bg_out[1]):
               self.target_x = 0.0
               self.target_z = 4.0
           else:
               self.target_x = 0.0
               self.target_z = -4.0

        #print "TARGET:",self.target_x,self.target_z
 
        return (self.target_x, self.target_z, x_hat, z_hat)




#hooks code for brahms module
print "hello from iceameat"
m=CIceaMeat()
def IceaMeat(ins):
    print "HELLO meat stepfun"
    try:
        return m.step(ins)
    except Exception ,detail:
	print "CAUGHT EXCEPTION:", detail,  sys.exc_info()[0]
	traceback.print_tb(sys.exc_info()[2])	









