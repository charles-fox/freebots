import pygtk
pygtk.require('2.0')
import gtk
import sys
import Pyro.core
        

class GuiClientReader:
    def __init__(self, uri):
        self.guiServer = Pyro.core.getProxyForURI(uri)
        print self.guiServer.getData()
        
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.set_border_width(10)
        self.button = gtk.Button("Hello World")
        self.button.connect("clicked", self.hello, None)
        self.button.connect_object("clicked", gtk.Widget.destroy, self.window)    
        self.window.add(self.button)        
        self.button.show()
        self.window.show()
        source_id = gtk.idle_add(self.callback)
        self.i = 1

    def hello(self, widget, data=None):
        print "Hello World"

    def delete_event(self, widget, event, data=None):  
        print "delete event occurred"
        return False

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        gtk.main_quit()

    def main(self):
        gtk.main()

    def callback(self):
        data = self.guiServer.getData()
        s=str(data)
        self.button.set_label(s)
        return True


if __name__ == "__main__":
    hello = GuiClientReader("PYRO://127.0.1.1:7766/7f00010123c30574ee4dac3f1c850d9f")
    hello.main()

