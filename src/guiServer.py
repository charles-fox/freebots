import Pyro.core

#need to import classes

class GuiServer(Pyro.core.ObjBase):
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
        self.data=[]
        for i in range(0,100): #TODO grow as needed?
            self.data.append([])
            
    def hello(self, name):
        return "Hello "+name+" hows tricks?"
    def setData(self, data, idx=0):   #called by the main ThomCat process
        self.data[idx] = data
    def getData(self,idx=0):       #called by reader processes
        return self.data[idx]

Pyro.core.initServer()
daemon=Pyro.core.Daemon()
uri=daemon.connect(GuiServer(), "guiServer")

print "running on port " , daemon.port

print "uri is " , uri

daemon.requestLoop()


