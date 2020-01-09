from bg import *
#import random

import sys
import traceback


def isCloseTo(tx,tz, mx,mz):  #target and estiMated locations; true if close.
    thresh=2.01
    return ((abs(tx-mx)<thresh) and (abs(tz-mz)<thresh))


class CIceaMeatBG:
    def __init__(self):
        self.hunger=0.0
        self.thirst = 0.5

        self.BG = BasalGanglia(n=2)

        self.target_x = 0.0
        self.target_z = 0.0

        self.x_hat_smooth = -5.0
        self.z_hat_smooth = 0

        self.init_countdown=5; #needed as there are some weird init issues

    def step(self, ins):
        print "meatBG step"
        print ins
        
        ins_pyrobrahms = ins[0]
        x=ins_pyrobrahms[0]
        z=ins_pyrobrahms[1]
        x_hat=ins_pyrobrahms[2]
        z_hat=ins_pyrobrahms[3]



        alpha=0.7
        self.x_hat_smooth = alpha*self.x_hat_smooth + (1-alpha)*x_hat
        self.z_hat_smooth = alpha*self.z_hat_smooth + (1-alpha)*z_hat


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

        if self.init_countdown<0:
            if isCloseTo(self.x_hat_smooth, self.z_hat_smooth, 0, 0):  #TODO should be HC estimates
  
                print "TARGET RACHED: calling BG"
                
                if (bg_out[0] > bg_out[1]):
                    self.target_x = 0.0
                    self.target_z = 4.0
                else:
                    self.target_x = 0.0
                    self.target_z = -4.0

        #print "TARGET:",self.target_x,self.target_z

        self.init_countdown -= 1

        return (self.target_x, self.target_z, x_hat, z_hat)




#hooks code for brahms module
iceaMeatBG=CIceaMeatBG()        #careful with global names here!!
def IceaMeatBG(ins):
    #print "HELLO meatBG stepfun"
    try:
        return iceaMeatBG.step(ins)
    except Exception ,detail:
	print "CAUGHT EXCEPTION:", detail,  sys.exc_info()[0]
	traceback.print_tb(sys.exc_info()[2])	









