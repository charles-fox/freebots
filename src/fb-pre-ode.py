#!/usr/bin/env python

#Freebots
#
#So=scene object, Sb=scene basic (vectors etc)
#
#           |
#           |
#           |sin th
#  ---------+--------> x
#           |\
#     cos th| \ 
#           |th\
#           |--->
#           v
#           z
#
#         initial view from this side

import sys
from pivy.sogui import *
from pivy.coin import *
from cf import *




class Universe:
    def __init__(self):
        self.physicals = []  #static and moving - for collision tests
        self.movings = [] #moving only
        self.robots=[] #things with controllers

def schedulingSensorCallback(u, scheduleSensor):
    for robot in u.robots:
        robot.controllerStep()        
    for moving in u.movings:
        moving.doKinematics()    
        moving.updateSceneGraph()

class Physical:
    def __init__(self,u,x=0,y=0,z=0,lx=1,ly=1,lz=1,th=0):
        self.u=u  #pointer to universe (eg for collisions)
        
        self.x=x
        self.y=y
        self.z=z
        self.lx=lx #lengths of bounding box, about center point
        self.ly=ly
        self.lz=lz
        self.th=th  #only consider 2D rotation
        
        self._mySoTransform=SoTransform()  #internals *ers
        self._mySoRotation=SoRotation()        
        self.sg = self.makeSceneGraph()
        u.physicals.append(self)
        
    def getSceneGraph(self):
        return self.sg

    def updateSceneGraph(self): #to be consistent with my physical position
        self._mySoTransform.translation = (self.x, self.y, self.z)
        #self._mySoTransform.scaleFactor = (1,1,1) #not BBox!
        th = SbRotation(SbVec3f(0,1,0), self.th)
        self._mySoRotation.rotation.setValue(th)

    def overlaps(self,other):        
        #TODO assumes no roations for now! --all squares lie in a grid
        return ((overlaps(self.x-self.lx, self.x+self.lx, other.x-other.lx, other.x+other.lx)) and (overlaps(self.y-self.ly, self.y+self.ly, other.y-other.ly, other.y+other.ly)) and(overlaps(self.z-self.lz, self.z+self.lz, other.z-other.lz, other.z+other.lz)))

class Moving(Physical):
    def __init__(self,u,x=0,y=0,z=0,lx=1,ly=1,lz=1,th=0):
        Physical.__init__(self,u,x,y,z,lx,ly,lz,th)
        u.movings.append(self)
        self.vx=0
        self.vy=0
        self.vz=0
        self.L=0 #angular momentum, 2D only!
        self.collisionFlag = False
    def doKinematics(self): #no forces here
        oldx=self.x
        oldy=self.y
        oldz=self.z
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
        self.th += self.L #TODO mass etc
        #check for collisions, bounce if so
        #pdb.set_trace()
        self.collisionFlag = False
        for physical in self.u.physicals:
            if not(self==physical):
                if physical.overlaps(self):
                    self.collisionFlag = True
                    self.x=oldx  #TODO bouncing -- just stop for now
                    self.y=oldy
                    self.z=oldz
                    self.vx=0
                    self.vy=0
                    self.vz=0
                    print("collision!")
    
class Sensor:
    def read(self):
        print("abs error")

class DistanceSensor(Sensor):
    def read(self):
        foo=6 #TODO -- get world loc and angle, then call to each phys obj and return shortest dist

class Robot(Moving):
    def __init__(self,u):
        Moving.__init__(self,u)
        u.robots.append(self)
        self.sensors=[] #append sensors to this list!
    def controllerStep(self): #TODO refactor
        speed=0.1
        if self.collisionFlag:
            self.vx=0
            self.vy=0
            self.vz=0
            self.L=1  #rotate
        else: #set velocity in the direction I am facing
            
            self.vx=speed*math.sin(self.th)
            self.vy=0
            self.vz=speed*math.cos(self.th)
            self.L=0 #no rotation  
    
    def makeSceneGraph(self):
        # Construct parts for legs (thigh, calf and foot)
        thigh = SoCube()
        thigh.width = 1.2
        thigh.height = 2.2
        thigh.depth = 1.1
        
        calfTransform = SoTransform()
        calfTransform.translation.setValue(0, -2.25, 0.0)
        
        calf = SoCube()
        calf.width, calf.height, calf.depth = 1, 2.2, 1
        
        footTransform = SoTransform()
        footTransform.translation = (0, -1.5, .5)
        
        foot = SoCube()
        foot.width, foot.height, foot.depth = 0.8, 0.8, 2
        
        # Put leg parts together
        leg = SoGroup()
        leg.addChild(thigh)
        leg.addChild(calfTransform)
        leg.addChild(calf)
        leg.addChild(footTransform)
        leg.addChild(foot)
        
        leftTransform = SoTransform()
        leftTransform.translation = (1, -4.25, 0)
        
        # Left leg
        leftLeg = SoSeparator()
        leftLeg.addChild(leftTransform)
        leftLeg.addChild(leg)
        
        rightTransform = SoTransform()
        rightTransform.translation = (-1, -4.25, 0)
        
        
        # Right leg
        rightLeg = SoSeparator()
        rightLeg.addChild(rightTransform)
        rightLeg.addChild(leg)
        
        # Parts for body
        bodyTransform = SoTransform()
        bodyTransform.translation = (0.0, 3.0, 0.0)
        
        bronze = SoMaterial()
        
        bronze.ambientColor = (.33, .22, .27)
        bronze.diffuseColor = (.78, .57, .11)
        bronze.specularColor = (.99, .94, .81)
        bronze.shininess = .28
        
        bodyCylinder = SoCylinder()
        bodyCylinder.radius = 2.5
        bodyCylinder.height = 6
        
        # Construct body out of parts 
        body = SoSeparator()
        body.addChild(bodyTransform)      
        body.addChild(bronze)
        body.addChild(bodyCylinder)
        body.addChild(leftLeg)
        body.addChild(rightLeg)
        
        # Head parts
        headTransform = SoTransform()
        headTransform.translation = (0, 7.5, 0)
        headTransform.scaleFactor = (1.5, 1.5, 1.5)
        
        silver = SoMaterial()
        silver.ambientColor = (.2, .2, .2)
        silver.diffuseColor = (.6, .6, .6)
        silver.specularColor = (.5, .5, .5)
        silver.shininess = .5
        
        headSphere = SoSphere()
    
        # Construct head
        head = SoSeparator()
        head.addChild(headTransform)
        head.addChild(silver)
        head.addChild(headSphere)
        
        # Robot is just head and body (transformed to stand on y=0 ground)
        robot = SoSeparator()

        #initialize my values (they are overwritten in getSG)
        tr = self._mySoTransform
        tr.translation = (0, 0, 0)
        tr.scaleFactor = (1, 1, 1)
        robot.addChild(tr)

        rot=self._mySoRotation
        th = SbRotation(SbVec3f(0,1,0), 0)
        rot.rotation.setValue(th)
        robot.addChild(rot)

        #internal scaling -- not related to physics etc
        tri = SoTransform()
        tri.translation = (0, .6, 0)
        tri.scaleFactor = (.1, .1, .1)
        robot.addChild(tri)

        robot.addChild(body)               
        robot.addChild(head)

        self.updateSceneGraph() #overwrites rotation and transform vals
        
        return robot


class Block(Physical):  #an immobile block in the world, for collisions, a wall.
    def __init__(self, u, x, y, z, lx, ly, lz):  #the center, and lengths
        Physical.__init__(self,u,x,y,z,lx,ly,lz)        

    def getSceneGraph(self):
        return self.sg
    def makeSceneGraph(self):  #return an Inventor tree ready to draw
        block=SoSeparator()
        tr = SoTransform()
        tr.translation = (self.x, self.y, self.z)
        tr.scaleFactor = (self.lx, self.ly, self.lz)
        block.addChild(tr)
        myMaterial = SoMaterial()
        myMaterial.diffuseColor = (1.0, 0.0, 0.0)  
        block.addChild(myMaterial)
        block.addChild(SoCube())
        return block

def main():
    myWindow = SoGui.init(sys.argv[0])
    if myWindow == None: sys.exit(1)
    root = SoSeparator()

    root.addChild(SoDirectionalLight())
    myCamera = SoPerspectiveCamera()
    root.addChild(myCamera)
    
    myMaterial = SoMaterial()
    myMaterial.diffuseColor = (1.0, 0.0, 0.0)   # Red
    root.addChild(myMaterial)

    u=Universe() #is global, so callbacks can see it!

    #WORLD

    world=SoSeparator()
    root.addChild(world)


    ground=SoSeparator()
    tr = SoTransform()
    tr.translation.setValue(0.0,0.0,0.0)
    tr.scaleFactor.setValue(5, 0.1 , 5)
    ground.addChild(tr)
    mat = SoMaterial()
    mat.diffuseColor = (0.0, 1.0, 0.0)  
    ground.addChild(mat)    
    ground.addChild(SoCube())
    world.addChild(ground)

    wall1 = Block(u, 0,1,5, 5,1,0.1)
    wall2 = Block(u, 0,1,-5, 5,1,0.1)
    wall3 = Block(u, 5,1,0, .1,1,5)
    wall4 = Block(u, -5,1,0, .1,1,5)

    world.addChild(wall1.getSceneGraph())
    world.addChild(wall2.getSceneGraph())
    world.addChild(wall3.getSceneGraph())
    world.addChild(wall4.getSceneGraph())


    #ROBOT
    robot = Robot(u)
    robot.x=0    
    root.addChild(robot.getSceneGraph())

    robot2 = Robot(u)
    robot2.z=3
    root.addChild(robot2.getSceneGraph())


    #TIMER   
    schedulingSensor = SoTimerSensor(schedulingSensorCallback, u)
    schedulingSensor.setInterval(0.1) # once per 1 seconds
    schedulingSensor.schedule()


    # Create a renderArea in which to see our scene graph.
    # The render area will appear within the main window.
    #myRenderArea = SoGuiRenderArea(myWindow)
    myRenderArea = SoGuiExaminerViewer(myWindow)


    # Make myCamera see everything.
    myCamera.viewAll(root, myRenderArea.getViewportRegion())

    # Put our scene in myRenderArea, change the title
    myRenderArea.setSceneGraph(root)
    myRenderArea.setTitle("Freebots")
    myRenderArea.show()

    SoGui.show(myWindow)  # Display main window
    SoGui.mainLoop()    # Main Inventor event loop

if __name__ == "__main__":
    main()




