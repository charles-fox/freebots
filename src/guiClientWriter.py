import sys
import Pyro.core

#to be instantiated by core process
class GuiClientWriter:
  def __init__(self):
    uri = "PYRO://127.0.1.1:7766/7f0001013e931a30a04ba6c1efeb1679"
    self.guiServer = Pyro.core.getProxyForURI(uri)

  def update(self, data):           
    self.guiServer.setData(data)
    


#w = GuiClientWriter()
#w.update([1,2,3])
