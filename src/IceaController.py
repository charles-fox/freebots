#!/usr/bin/env python

from bg import *
from hc import *
import random
from guiClientWriter import *




#currently just doing a random walk -- HC will learn from it

def isCloseTo(tx,tz, mx,mz):  #target and estiMated locations; true if close.
    thresh=1.8
    return ((abs(tx-mx)<thresh) and (abs(tz-mz)<thresh))


class IceaController:
    def __init__(self, robot):
        self.robot = robot    

        self.target_x = 0
        self.target_z = 0

        self.x_hat=0   #are members/outputs so that GUIs etc can read them
        self.z_hat=0

        self.x_hat_smooth = -5.0
        self.z_hat_smooth = 0

        self.hunger = 0.0
        self.thirst = 0.5

        self.BG = BasalGanglia(n=2)
        self.ptHC = PreTrainedHippocampus()

        self.gui = GuiClientWriter()

    
    def step(self):
        th = self.robot.getTheta()    
        x,y,z = self.robot.body.getPosition()

        self.hunger += 0.02
        self.thirst += 0.03
        if self.hunger > 1.0:  #cap at 1.0 (full strength)
            self.hunger=1.0
        if self.thirst>1.0:
            self.thirst=1.0

        ###################################Calls to modules
        #put them into the BG, and update it to get decision
        bg_input = [self.hunger, self.thirst]

        bg_out = self.BG.step(bg_input)
        self.x_hat, self.z_hat = self.ptHC.step(x,z,th)   #pretrained hippocampus step
        ####################################


        alpha=0.7
        self.x_hat_smooth = alpha*self.x_hat_smooth + (1-alpha)*self.x_hat
        self.z_hat_smooth = alpha*self.z_hat_smooth + (1-alpha)*self.z_hat


        if isCloseTo(self.x_hat_smooth, self.z_hat_smooth, 0, 0):  #TODO should be HC estimates
            #we are at the center of the maze. Look at BG to decide where to go.
            if (bg_out[0] > bg_out[1]):
                self.target_x = 0
                self.target_z = 4
            else:
                self.target_x = 0
                self.target_z = -4                

        #select rand new target at each goal
        #if self.robot.isCloseTo(self.target_x, self.target_z):  #pick new target one last one reached
        #    self.target_x = random.randint(-4,4)
        #    self.target_z = random.randint(-4,4)
        #    print "new target x=",self.target_x," z=",self.target_z

        #print th        
        self.robot.moveDirectTo(self.target_x, self.target_z)

        self.gui.update([self.x_hat, self.z_hat, self.BG, self.ptHC])   #write data for external gui monitors to use




