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
        self.window.set_title("ICEASim monitor")
        self.window.set_default_size(600,300)
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.set_border_width(10)
        
        self.button = gtk.Button("Hello World")
        self.button.connect("clicked", self.hello, None)
        self.button.connect_object("clicked", gtk.Widget.destroy, self.window)    
        #self.window.add(self.button)        
       

        self.button2 = gtk.Button("Hello World")
        #self.window.add(self.button2)        
       

        self.area = gtk.DrawingArea()
        self.area.set_size_request(400, 300)
        self.area.set_events(gtk.gdk.POINTER_MOTION_MASK |
                             gtk.gdk.POINTER_MOTION_HINT_MASK )
        self.area.connect("expose-event", self.area_expose_cb)
        self.sw = gtk.ScrolledWindow()
        self.sw.add_with_viewport(self.area)

        
        self.table = gtk.Table(2,2)

        self.table.attach(self.button, 0,1,0,1)
        self.table.attach(self.button2, 1,2,0,1)
        self.table.attach(self.sw, 0, 2, 1, 2)
        
        self.window.add(self.table)

        self.table.show()
        self.sw.show()
        self.area.show()
        self.button.show()
        self.button2.show()
        self.window.show()
        source_id = gtk.idle_add(self.callback)
        self.i = 1

    def area_expose_cb(self, area, event):
        self.style = self.area.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]

        self.draw_line(210, 10)
        self.draw_lines(310, 10)
    
        return True

    def draw_line(self, x, y):
        self.area.window.draw_line(self.gc, x+10, y+10, x+20, y+30)
        return

    def draw_lines(self, x, y):
        points = [(x+10,y+10), (x+10,y), (x+40,y+30),
                  (x+30,y+10), (x+50,y+10)]
        self.area.window.draw_lines(self.gc, points)
        return


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

