#!/usr/bin/env python

import sys
import ode
from pivy.sogui import *
from pivy.coin import *
from OpenGL.GL import *    #needed only for additional drawings
from cf import *

import Pyro.core

class Universe:
    def __init__(self):
        uri = "PYRO://127.0.1.1:7766/7f00010123660604c807ebe70a1e65ad"
    
        self.guiServer = Pyro.core.getProxyForURI(uri)
        print self.guiServer.getData()

        
        self.root = SoSeparator()
        self.c=0.0

    def buildSceneGraph(self):
        self.root.removeAllChildren()
        #do stuff...

        data = self.guiServer.getData()
        bg = data[2]
        ptHC = data[3]

        gCx = SoSeparator()   #cortex
        tr = SoTransform()
        tr.translation.setValue(0.0,2.0,0.0)
        gCx.addChild(tr)
        gCx.addChild(makePopSceneGraph(bg.Cx.getYs()))     
        txt = makeText("Cx",0,0.8,0)
        gCx.addChild(txt)
        self.root.addChild(gCx)

        gD1 = SoSeparator()  
        tr = SoTransform()
        tr.translation.setValue(-3.0,0.0,0.0)
        gD1.addChild(tr)
        gD1.addChild(makePopSceneGraph(bg.D1.getYs()))
        txt = makeText("D1",0,0.8,0)
        gD1.addChild(txt)
        self.root.addChild(gD1)

        gD2 = SoSeparator()   #cortex
        tr = SoTransform()
        tr.translation.setValue(+3.0,0.0,0.0)
        gD2.addChild(tr)
        gD2.addChild(makePopSceneGraph(bg.D2.getYs()))
        txt = makeText("D2",0,0.8,0)
        gD2.addChild(txt)
        self.root.addChild(gD2)

        gSTN = SoSeparator()   #cortex
        tr = SoTransform()
        tr.translation.setValue(0.0,0.0,0.0)
        gSTN.addChild(tr)
        gSTN.addChild(makePopSceneGraph(bg.STN.getYs()))
        txt = makeText("STN",0,0.8,0)
        gSTN.addChild(txt)
        self.root.addChild(gSTN)

        gGPe = SoSeparator()   #cortex
        tr = SoTransform()
        tr.translation.setValue(-2.0,-2.0,0.0)
        gGPe.addChild(tr)
        gGPe.addChild(makePopSceneGraph(bg.GPe.getYs()))
        txt = makeText("GPe",0,0.8,0)
        gGPe.addChild(txt)
        self.root.addChild(gGPe)

        gGPi = SoSeparator()   #cortex
        tr = SoTransform()
        tr.translation.setValue(2.0,-2.0,0.0)
        gGPi.addChild(tr)
        gGPi.addChild(makePopSceneGraph(bg.GPi.getYs()))
        txt = makeText("GPe",0,0.8,0)
        gGPi.addChild(txt)
        self.root.addChild(gGPi)


        gEC = SoSeparator()   #cortex
        tr = SoTransform()
        tr.translation.setValue(2.0,-8.0,0.0)
        gEC.addChild(tr)
        gEC.addChild(makePopSceneGraph(ptHC.HC.EC.out))
        txt = makeText("EC",0,0.8,0)
        gEC.addChild(txt)
        self.root.addChild(gEC)

        gDG = SoSeparator()   #cortex
        tr = SoTransform()
        tr.translation.setValue(2.0,-10.0,0.0)
        gDG.addChild(tr)
        gDG.addChild(makePopSceneGraph(ptHC.HC.DG.out))
        txt = makeText("DG",0,0.8,0)
        gDG.addChild(txt)
        self.root.addChild(gDG)

        gCA3 = SoSeparator()   #cortex
        tr = SoTransform()
        tr.translation.setValue(2.0,-12.0,0.0)
        gCA3.addChild(tr)
        gCA3.addChild(makePopSceneGraph(ptHC.HC.CA3.out))
        txt = makeText("CA3",0,0.8,0)
        gCA3.addChild(txt)
        self.root.addChild(gCA3)


def makePopSceneGraph(ys):   #ys is vector of firing rates.
    #first, make a block background
    sg=SoSeparator()
        
    block=SoSeparator()
    tr = SoTransform()
    tr.scaleFactor = (0.5*len(ys), 0.6, 0.1)
    block.addChild(tr)
    myMaterial = SoMaterial()
    myMaterial.diffuseColor = (0.0, 0.0, 0.3)  
    block.addChild(myMaterial)
    block.addChild(SoCube())
    sg.addChild(block)

    xpos=-0.5*len(ys)+0.5
    for y in ys:
        s = SoSeparator()
        tr = SoTransform()
        tr.scaleFactor = (.5,.5,.5)
        tr.translation.setValue(xpos,0.0,0.0)

        myMaterial = SoMaterial()
        myMaterial.diffuseColor = (y,y,y)  
        s.addChild(myMaterial)

        s.addChild(tr)
        s.addChild(SoSphere())
        sg.addChild(s)
        xpos+=1

    return sg
        
def makeText(str, x,y,z):
    root = SoSeparator()
    
    # Choose a font
    myFont = SoFont()
    myFont.name = "Times-Roman"
    myFont.size = 0.7
    root.addChild(myFont)

    # We'll color the front of the text white, and the sides 
    # dark grey. So use a materialBinding of PER_PART and
    # two diffuseColor values in the material node.
    myMaterial = SoMaterial()
    myBinding = SoMaterialBinding()
    myMaterial.diffuseColor.set1Value(0, SbColor(1,1,1))
    myMaterial.diffuseColor.set1Value(1, SbColor(1,1,1))
    myBinding.value = SoMaterialBinding.PER_PART
    root.addChild(myMaterial)
    root.addChild(myBinding)

    africaSep = SoSeparator()
    africaTransform = SoTransform()
    africaText = SoText3()
    #africaTransform.rotation.setValue(SbVec3f(0,1,0), .4)
    africaTransform.translation = (x,y,z)
    africaText.parts = SoText3.ALL
    africaText.string = str
    root.addChild(africaSep)
    africaSep.addChild(africaTransform)
    africaSep.addChild(africaText)
    return root



def schedulingSensorCallback(u, scheduleSensor): #main step entry for sim
    #rebuild whole scene here, then redraw it
    u.buildSceneGraph()


# Callback routine to render extra bits in raw OpenGL
def myCallbackRoutine(void, action):
    if not action.isOfType(SoGLRenderAction.getClassTypeId()): return        # only render the floor during GLRender actions
    SoCacheElement.invalidate(action.getState()) #important--as the geometry is changing!
    global u
    #if required, call any relevant GL displays from here



  
def main():
    myWindow = SoGui.init(sys.argv[0])
    if myWindow == None: sys.exit(1)
    global u
    u=Universe() #is global, so callbacks can see it!

    u.buildSceneGraph()




    #TIMER callback
    schedulingSensor = SoTimerSensor(schedulingSensorCallback, u)
    schedulingSensor.setInterval(0.01) # once per 1 seconds   0.001 is good
    schedulingSensor.schedule()

    #Raw OpenGL drawing CALLBACK
    myCallback = SoCallback()
    myCallback.setCallback(myCallbackRoutine)
    u.root.addChild(myCallback)


    # Create a renderArea in which to see the scene
    #myRenderArea = SoGuiRenderArea(myWindow)
    myRenderArea = SoGuiExaminerViewer(myWindow)
#    u.myCamera.viewAll(u.root, myRenderArea.getViewportRegion())      # Make myCamera see everything.
    myRenderArea.setSceneGraph(u.root)       # Put our scene in myRenderArea, change the title
    myRenderArea.setTitle("ICEASim - Monitors")
    myRenderArea.show()
    SoGui.show(myWindow)  # Display main window
    SoGui.mainLoop()    # Main Inventor event loop

if __name__ == "__main__":
    main()




