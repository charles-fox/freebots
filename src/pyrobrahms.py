#This is the Brahms module.

import sys
import Pyro.core

import sys
import traceback

SLOT_SIM2BRAHMS=1
SLOT_BRAHMS2SIM=2
SLOT_SCHEDULE_BIT=3


class CPyroBrahms:
    def __init__(self):
#        print "init pyrobrahms"

        uri='PYRO://127.0.1.1:7766/7f0001013e6112e8250036e37fc95538'
        self.server = Pyro.core.getProxyForURI(uri)

    def step(self,ins):
#        print "WRAPPER STEP"
        
#        print ins
        tx,tz,x_hat,z_hat = ins[0]   #from HC (the first brahms input)
#        print ins[0]

#        print "PYROa"
#        print tx,tz,x_hat,z_hat

        self.server.setData(0, SLOT_SCHEDULE_BIT)   #let other go first (is [] at start, so no-one has the signal)
        self.server.setData([tx,tz,x_hat,z_hat], SLOT_BRAHMS2SIM) 

#        print "PYROb"
    
        while True:                                #block until its my turn to read
            data = self.server.getData(SLOT_SCHEDULE_BIT)
            if (data==1):
                break
        self.server.setData(0,SLOT_SCHEDULE_BIT)             #slot 3: scheduler bit. 0=sim's turn, 1=my turn

#       print "PYROc"

        x,z=self.server.getData(SLOT_SIM2BRAHMS)

#       print "PYROd"

        return (x,z)



#self.server.setData([x_hat, z_hat, BG, ptHC], 0)   #to GUI--move to real brain?





#hooks code for brahms module
pb=CPyroBrahms()
def pyrobrahms(ins):
#    print "HELLO Pyromyfun"
    try:
        return pb.step(ins)
    except Exception ,detail:
	print "CAUGHT EXCEPTION:", detail,  sys.exc_info()[0]
	traceback.print_tb(sys.exc_info()[2])	





