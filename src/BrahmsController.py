import sys
import Pyro.core

SLOT_SIM2BRAHMS=1
SLOT_BRAHMS2SIM=2
SLOT_SCHEDULE_BIT=3

#currently just doing a random walk -- HC will learn from it

class BrahmsController:
    def __init__(self, robot):
        self.robot = robot    

        self.target_x = 0
        self.target_z = 0

        self.x_hat=0   #are members/outputs so that GUIs etc can read them
        self.z_hat=0


        uri='PYRO://127.0.1.1:7766/7f0001013e6112e8250036e37fc95538'
        self.guiServer = Pyro.core.getProxyForURI(uri)

        self.guiServer.setData([0.0,0.0,0.0,0.0], SLOT_BRAHMS2SIM)  #clear out any old data  
        self.guiServer.setData([-5.0,-5.0], SLOT_SIM2BRAHMS)  

    
    def step(self):
        th = self.robot.getTheta()    
        x,y,z = self.robot.body.getPosition()

        self.guiServer.setData([x,z], SLOT_SIM2BRAHMS)                                #to brahms

        print "waiting for unblock"
        while True:                                #block until its my turn to read
            data = self.guiServer.getData(SLOT_SCHEDULE_BIT)
            if (data==0):
                break
        self.guiServer.setData(1,SLOT_SCHEDULE_BIT)             #unblock brahm's turn to read
            
        data = self.guiServer.getData(SLOT_BRAHMS2SIM)
        print data
        self.target_x, self.target_z, self.x_hat, self.z_hat = data

        print "TARGET:",self.target_x, self.target_z

        self.robot.moveDirectTo(self.target_x, self.target_z)  #motor command
        



