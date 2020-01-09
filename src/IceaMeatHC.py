
from hc import *
#import random

import sys
import traceback


class CIceaMeatHC:
    def __init__(self):       
        self.ptHC = PreTrainedHippocampus()
       

    def step(self, ins):
        #print "HC ins:", ins
        #print "A"
        
        ins_pyrobrahms = ins[0]
        #print "B"

        
        #print ins_pyrobrahms
        
        x=ins_pyrobrahms[0]
        z=ins_pyrobrahms[1]     
        
        x_hat, z_hat = self.ptHC.step(x,z,[])   #pretrained hippocampus step

        #print "C"
        return (x,z,x_hat, z_hat)



#hooks code for brahms module
iceaMeatHC=CIceaMeatHC()          #careful with global names here!!
def IceaMeatHC(ins):
    #print "HELLO meatHC stepfun"
    try:
        return iceaMeatHC.step(ins)
    except Exception ,detail:
	print "CAUGHT EXCEPTION:", detail,  sys.exc_info()[0]
	traceback.print_tb(sys.exc_info()[2])	









