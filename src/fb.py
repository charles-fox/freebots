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

# NB need to run with v short dt to model high freq vibrations!
# (eg in slowmotion, then speed up the saved video afterwards)

import sys
import ode
from pivy.sogui import *
from pivy.coin import *
from OpenGL.GL import *    #needed only for additional drawings
from cf import *
from robot_sg import *
from SimpleController import *
from IceaController import *
#from BrahmsController import *

SEG_LENGTH = 0.1
SIM_STEP_SECS = 1.0/100.0

floorObj = []

class Universe:
    def __init__(self):

        #CACHES
        self.physicals = []  #static and moving - for collision tests
        self.movings = [] #moving only
        self.robots=[] #things with controllers
        self.rawGLObjects = []  #things that need to call special graphics

        #ODE
        self.world = ode.World()        
        self.world.setGravity((0,0,0)) #(0,-9.81,0)
        self.space = ode.Space()  #for environment object geoms
        self.segSpace = ode.Space()  #keep segs in sep space to reduce number of comparisons
        self.robotSpace = ode.Space() #for the robot body parts
        self.contactgroup = ode.JointGroup()

        #INVENTOR
        root = SoSeparator()#collide((u.world, u.contactgroup), contact_callback) #TODO replacewith custom collisions, segs vs whole world and robot vs whole world

        root.addChild(SoDirectionalLight())
        self.myCamera = SoPerspectiveCamera()
        root.addChild(self.myCamera)    
        myMaterial = SoMaterial()
        myMaterial.diffuseColor = (1.0, 0.0, 0.0)   # Red
        root.addChild(myMaterial)
        env=SoSeparator() #the environent (ie not robots)
        root.addChild(env)       

        self.root = root

        #CONTROLLER TIMER
        self.controllerTimer=0

class RawGLObject:
    def __init__(self,u):
        u.rawGLObjects.append(self)
    def drawGL(self):   #called from special inventor GL callback
        print 'abs error'


def schedulingSensorCallback(u, scheduleSensor): #main step entry for sim
    for physical in u.physicals:
        physical.updateForces()

    u.controllerTimer+=1
    if u.controllerTimer==20:
        u.controllerTimer=0
        for robot in u.robots:
            robot.controller.step()

    #COLLISIONS

    #this is equivilent to the collide2 on next line!
    #u.space.collide((u.world, u.contactgroup), contact_callback) 
    #ode.collide2(u.space, u.space,  (u.world, u.contactgroup), contact_callback)
   
    
    for robot in u.robots:
        ode.collide2(robot.geom, u.space, (u.world, u.contactgroup), oneway_contact_callback)
        for seg in robot.segs:
            ode.collide2(seg.geom, u.space, (u.world, u.contactgroup), oneway_contact_callback)
        ode.collide2(robot.wheelL.geom, u.space,  (u.world, u.contactgroup), wheel_contact_callback)
        ode.collide2(robot.wheelR.geom, u.space,  (u.world, u.contactgroup), wheel_contact_callback)
    

    u.world.step(SIM_STEP_SECS)             #ODE step
    u.contactgroup.empty()
    
    for moving in u.movings:
        moving.updateSceneGraph()

    #TODO move camera here?
    

def contact_callback(args, geom1, geom2): #GENERIC collision (like webots)
    if geom1==geom2:
        return

    #print "generic two-way contact"
    
    contacts = ode.collide(geom1, geom2)        # Check if the objects do collide
    world,contactgroup = args         
    for c in contacts:                            # Create contact joints
        c.setBounce(0.2)
        c.setMu(5000)                        #is friction?
        j = ode.ContactJoint(world, contactgroup, c)
        j.attach(geom1.getBody(), geom2.getBody())

def oneway_contact_callback(args, geom1, geom2): #ignore opposite force on environment
    if geom1==geom2:        #geom2 is the object to experience the force
        return
    #print "oneway contact"
    contacts = ode.collide(geom1, geom2)        # Check if the objects do collide
    world,contactgroup = args         
    for c in contacts:                            # Create contact joints
        c.setBounce(0.2)
        c.setMu(0)   #no friction
        j = ode.ContactJoint(world, contactgroup, c)
        j.attach(None, geom2.getBody())  #None=link to environment instead of other body (see ODE FAQ)


def wheel_contact_callback(args, geom1, geom2): #GENERIC collision (like webots)
    if geom1==geom2:    #geom2 is the wheel!
        return

    contacts = ode.collide(geom1, geom2)        # Check if the objects do collide
    world,contactgroup = args         
    for c in contacts:                            # Create contact joints
        c.setBounce(0.2)
        c.setMu(10)                        #is friction?
        j = ode.ContactJoint(world, contactgroup, c)
        j.attach(None, geom2.getBody())


#TODO an extra thing would be to remove the joint at the follicle, and replace by joining the whisker to the environment

class Physical: 
    def __init__(self,u):

        self.ID = 'unnamed'
        self.u=u  #pointer to universe (eg for collisions)        
        u.physicals.append(self)
        
        self._mySoTransform=SoTransform()  #internals *ers
        self._mySoRotation=SoRotation()
        
        self.body = [] #the subclass is responsible for making these
        self.geom = []

        sg = SoSeparator()
        tr = self._mySoTransform
        tr.translation = (0, 0, 0) #NB these get overwritten by update fns
        tr.scaleFactor = (1, 1, 1)
        sg.addChild(tr)
        rot=self._mySoRotation
        th = SbRotation(SbVec3f(0,1,0), 0)
        rot.rotation.setValue(th)
        sg.addChild(rot)
        self.sg=sg
        u.root.addChild(self.sg)
        
    def getSceneGraph(self):
        return self.sg

    def updateForces(self):
        foo=0

    def updateSceneGraph(self): #to be consistent with my ODE position
        #print "ID:", self.ID
        x,y,z=self.body.getPosition()
        self._mySoTransform.translation = (x, y, z)

        #TODO this is wrong for true 3D -- only rotates x?
        #th_ode = self.body.getRotation()   #is a rotation matrix (like in QC unitaries)
        #x_to = SbVec3f(1,0,0)
        #x_from = SbVec3f(th_ode[0:3])    #TODO check this is right way round??
        #th_inventor = SbRotation(x_from, x_to)   #there are many ways to set this -- eg using 4*4 matrix; axis-angle; from-to vecs.
        #self._mySoRotation.rotation.setValue(th_inventor)
        

        q_ode = self.body.getQuaternion()
        #print q_ode
        th = 2*math.acos(q_ode[0])
        a = math.sin(th/2)
        rx,ry,rz=q_ode[1],q_ode[2],q_ode[3]
        
        if a==0:   #keep Inventor happy in degenerate case
            a=0.0000000001
            rx=1

        rot_inventor = SbRotation(SbVec3f(a*rx,a*ry,a*rz), th)
        self._mySoRotation.rotation.setValue(rot_inventor)
        


class Movable(Physical):  #adds to cache - for inventor graph recomputes
    def __init__(self,u):
        Physical.__init__(self,u)
        u.movings.append(self)
        
class Sensor:
    def read(self):
        print("abs error")

class DistanceSensor(Sensor):
    def read(self):
        foo=6 #TODO -- get world loc and angle, then call to each phys obj and return shortest dist

def cropServoTorque(T):
    T_max=20
    if T>T_max:
        T=T_max
    else:
        if T<-T_max:
            T=-T_max
    return T

class Robot(Movable, RawGLObject):
    def __init__(self,u,x,z):

        Movable.__init__(self,u)  #inits ode, inventor etc and register with world
        RawGLObject.__init__(self,u)   #eg may want to overlay some HC output as GL graphics onto scene to show what I'm thinking about

        mass = ode.Mass()
        density=100
        axis=0  #1x;2y;3z. But seems to be ignored? (maybe as physObject sets rotation elsewhere?)
        radius=0.5
        depth=0.1
        mass.setCylinder(density, axis, radius,depth)
             
        self.body = ode.Body(self.u.world)
        self.body.setMass(mass)
        self.body.setPosition((x,0.3,z))

        self.geom = ode.GeomCylinder(u.robotSpace, radius, depth) 
        self.geom.setBody(self.body)

        th = math.pi/2
        a = math.sin(th/2)
        self.geom.setQuaternion((math.cos(th/2), a*1,a*0,a*0))

#        self.sg.addChild(makeRobotSceneGraph())
#        self.sg.addChild(makeRatSceneGraph())


        #NB: ODE cylinders are in z-axis by default; Inventor are in y!
        #It MUST be Inventor that is modified, as ODE rotations are drawn anyway by Inventor
        rot=SoRotation()
        th = SbRotation(SbVec3f(1,0,0), 3.142/2)
        rot.rotation=th
        self.sg.addChild(rot)
        myCylinder = SoCylinder()    #TODO rotate zo z axis height is default
        myCylinder.radius = radius;
        myCylinder.height = depth;
        self.sg.addChild(myCylinder)

        #simple 'head' to show the front
        trans = SoTransform()    
        trans.translation.setValue(0.5, -0.2, 0.0)
        trans.scaleFactor.setValue(.2,.2,.2)
        self.sg.addChild(trans)
        self.sg.addChild(SoSphere())

#        self.controller = SimpleController(self)
        self.controller = IceaController(self)
#        self.controller = BrahmsController(self)

        self.F_controller=(0.0, 0.0, 0.0)  #Force due to controller. cache these so we dont have to run controller on every physics step
        self.T_controller=(0.0, 0.0, 0.0)  #Torque due to controller.
        self.controller_bSetoff=False

        u.robots.append(self)
        self.sensors=[] #append sensors to this list!

        self.segs=[]
        self.follicleL = Segment(u,self,1)
        self.follicleR = Segment(u,self,-1)
        self.segs.append(self.follicleL)
        self.segs.append(self.follicleR)

        par=self.follicleL
        for i in range(2,4):
            seg = Segment(u,par,i+1)
            self.segs.append(seg)
            par=seg
        par=self.follicleR
        for i in range(2,4):
            seg = Segment(u,par,-i)
            self.segs.append(seg)
            par=seg

        self.wheelL = Wheel(u,self,-0.6)
        self.wheelR = Wheel(u,self,0.6)
        


    def getBodyPositionForChildSeg(self):
        x,y,z = self.body.getPosition()

        return (x+0.5,y,z)
    

    def updateForces(self):        
   #     v = self.body.getLinearVel()
   #     gamma = 100000 #100000
   #     F_damping = map(lambda x: -1*gamma*x, v)   #linear friction
   #     self.body.addForce(F_damping)        
   #     dth = self.body.getAngularVel()
   #     gamma_th = 500
   #     T_gamma = map(lambda x: -1*gamma_th*x, dth)   #rotational friction
   #     self.body.addTorque(T_gamma)
   #print self.F_controller

        self.body.addForce((0.0, -9.81*10*0.1 ,0.0))
#        self.body.addForce(self.F_controller)
#        self.body.addTorque(self.T_controller)
        
    def isCloseTo(self,tx,tz): #true if approximately at the target (tx,tz) location
        mx,my,mz = self.body.getPosition()
        thresh=0.3
        return math.sqrt((tx-mx)**2+(tz-mz)**2) < thresh

#TODO THIS IS WRONG!
    def getTheta(self):  #gets my 2D angle in the floor plane, measured from the x axis
        matrix = self.body.getRotation()   #as 3*3 rotation matrix

        mypos = self.body.getPosition()
        rwheelpos = self.wheelR.body.getPosition()

        dx = rwheelpos[0]-mypos[0]
        dz = rwheelpos[2]-mypos[2]
        #print dx, dz
        th = fixAngle(math.atan2(dx,dz) + math.pi/2)
        print th
        return th


                
    def isFacing(self,th):  #test if approx facing theta in world coords
        mth=self.getTheta()        
        thresh=0.2
        #print mth, th
        return (abs(fixAngle(th-mth))<thresh)

    def setWheels(self, des_omegaL, des_omegaR):   #desired wheel speeds
       
        omegaL3 = self.wheelL.body.getAngularVel()  #is 3-vector
        omegaR3 = self.wheelR.body.getAngularVel()

        #print omegaL3

        omegaL3 = self.wheelL.body.vectorFromWorld(omegaL3)
        omegaR3 = self.wheelR.body.vectorFromWorld(omegaR3)

        #print omegaL3
        #print "."

        omegaL =omegaL3[2]
        omegaR =omegaR3[2]

        d_omegaL = (-des_omegaL) - omegaL   #delta angular veocity
        d_omegaR = (-des_omegaR) - omegaR

        d_T_L = d_omegaL/SIM_STEP_SECS   #delta torque left
        d_T_R = d_omegaR/SIM_STEP_SECS

        d_T_L = cropServoTorque(d_T_L)
        d_T_R = cropServoTorque(d_T_R)
        
        self.wheelL.body.addRelTorque((0.0,0.0, d_T_L))  #wheel spin goes in z!
        self.wheelR.body.addRelTorque((0.0,0.0, d_T_R))    

    def applyControllerForceForward(self, f):   #f is the force magnitude
        th=self.getTheta()
        F=(f*math.cos(th), 0, f*math.sin(th))
        self.F_controller = F


    def moveDirectTo(self,x,z):
        self.T_controller = (0.0,0.0,0.0)  #reset total force and torque
        self.F_controller = (0.0,0.0,0.0)
        
        mx,my,mz=self.body.getPosition()
        if self.isCloseTo(x,z):
            print "at goal"
            self.controller_bSetoff=False
            self.setWheels(0,0)  #brakes!
            return
        Dx = x-mx
        Dz = z-mz        
        r = math.sqrt(Dx**2 + Dz**2)
        th_target = math.atan2(Dx,Dz)  #the way we want to be pointing TODO use atan2?

        #print Dx, Dz, th_target  #these are all OK
        
        if self.isFacing(th_target):
            print "is facing"
            self.setWheels(4,4)
            self.controller_bSetoff = True
        else:
            th=self.getTheta()
            dth = fixAngle(th_target-th)            
            if dth>0:
                self.setWheels(-5,5)                
            else:
                self.setWheels(5,-5)


#TODO each controll should have its own
    def drawGL(self):  #called by GL render callback fn from Inventor--draw x from HC
        glPushMatrix()

        glTranslatef(0.0, 0.0, 0.0)
        glColor3f(0.5, 0.5, 0.0)
        glLineWidth(1)
        glDisable(GL_LIGHTING)  # so we don't have to set normals  

        glBegin(GL_LINES)
        glVertex3fv((self.controller.x_hat-0.5, 0.2, self.controller.z_hat))
        glVertex3fv((self.controller.x_hat+0.5, 0.2, self.controller.z_hat))
        glEnd()
        glBegin(GL_LINES)
        glVertex3fv((self.controller.x_hat, 0.2, self.controller.z_hat+0.5))
        glVertex3fv((self.controller.x_hat, 0.2, self.controller.z_hat-0.5))
        glEnd()

 #       glColor3f(0.5, 0.0, 1.0)
 #       glBegin(GL_LINES)
 #       glVertex3fv((self.controller.x_hat_smooth-0.5, 0.2, self.controller.z_hat_smooth))
 #       glVertex3fv((self.controller.x_hat_smooth+0.5, 0.2, self.controller.z_hat_smooth))
 #       glEnd()
 #       glBegin(GL_LINES)
 #       glVertex3fv((self.controller.x_hat_smooth, 0.2, self.controller.z_hat_smooth+0.5))
 #       glVertex3fv((self.controller.x_hat_smooth, 0.2, self.controller.z_hat_smooth-0.5))
 #       glEnd()

        glEnable(GL_LIGHTING)
        glPopMatrix()


class Segment(Movable, RawGLObject):
    
    def __init__(self, u, par, level):       
        Movable.__init__(self,u)
        RawGLObject.__init__(self,u)
        
        mass = ode.Mass()  
        r=0.05
        density=100
        mass.setSphere(density, r)                         #NB segment is a sphere mass -- so does not need to rotate. the bending is done by joints BETWEEN the masses        
        self.body = ode.Body(self.u.world)
        self.body.setMass(mass)
        self.level=level
        x,y,z=par.getBodyPositionForChildSeg()

        seg=0.4

        if level==1:
            x+=0.15 #65
            z+=0.15
        elif level==-1:
            x+=0.15
            z-=0.15          
        elif level>1:
            x+=seg
            z+=seg
        elif level<-1:
            x+=seg
            z-=seg
        

        #x+=x_offset
        #x=x+SEG_LENGTH        #TODO fix properly
        #z=z+z_offset

        self.body.setPosition((x,y,z))
        self.geom = ode.GeomSphere(u.segSpace, r)  #SEPARATE SPACE!
        self.geom.setBody(self.body)
        self.sg.addChild(self.makeSceneGraph(r))
        self.joint = ode.HingeJoint(self.u.world)  #easier to use horiz/vertical pairs of hinges rather than balls; as have getAngle methods
        self.joint.attach(par.body, self.body)
        self.joint.setAnchor(par.body.getPosition())
        self.joint.setAxis((0,1,0))

        if abs(level)==1:   #follicle has different properties
            self.k=1.0
            self.gamma=0.5
        else:
            self.k=0.1   #TODO we really need two different classes of sim: one of rmacro navigation excersizes, and one for very fine detailed vibrtation sims.
            self.gamma=0.05
        self.par=par #needed for link graphics        
            
    def makeSceneGraph(self, r):  #return an Inventor tree ready to draw
        r=r*0.5
        sg=SoSeparator()
        tr = SoTransform()
        tr.scaleFactor = (r, r, r)
        sg.addChild(tr)
        myMaterial = SoMaterial()
        myMaterial.diffuseColor = (0.5, 0.5, 1.0)  
        sg.addChild(myMaterial)
        sg.addChild(SoSphere())
        return sg

    def updateForces(self):
        th = self.joint.getAngle()
        T_k = -self.k*th            #spring torque
        self.joint.addTorque(T_k)

        dth = self.joint.getAngleRate()
        T_gamma = -self.gamma*dth
        self.joint.addTorque(T_gamma) #damping

        #print 'th %f dth %f T_k %f T_gamma %f' % (th,dth,T_k,T_gamma)

    def getBodyPositionForChildSeg(self):
        return self.body.getPosition()

    def drawGL(self):  #called by GL render callback fn from Inventor
        if not abs(self.level)==1:
            glPushMatrix()

            glTranslatef(0.0, 0.0, 0.0)
            glColor3f(0.0, 0.7, 0.0)
            glLineWidth(2)
            glDisable(GL_LIGHTING)  # so we don't have to set normals  

            glBegin(GL_LINES)
            glVertex3fv(self.body.getPosition())
            glVertex3fv(self.par.getBodyPositionForChildSeg())
            glEnd()
    
            glEnable(GL_LIGHTING)   
            glLineWidth(1)
            glPopMatrix()

#class Follicle(Segment):
#    def __init__(self,u,par,x_offset,z_offset):
#        Segment.__init__(self,u,par,z_offset,x_offset)


class Wheel(Movable): 
    def __init__(self, u, par, z_offset):       
        Movable.__init__(self,u)
        self.par=par #needed for link graphics        

        mass = ode.Mass()
        axis=0
        radius=0.3
        depth=0.1
        mass.setCylinder(100, axis, radius,depth)  #gets rotated by any geom rots

        x,y,z = self.par.body.getPosition()
        z+=z_offset

        self.body = ode.Body(self.u.world)
        self.body.setMass(mass)
        self.body.setPosition((x,y,z))

        self.geom = ode.GeomCylinder(u.segSpace, radius, depth)  #SEPARATE SPACE!
        self.geom.setBody(self.body)

        self.sg.addChild(self.makeSceneGraph(radius,depth))
        self.joint = ode.HingeJoint(self.u.world)  #easier to use horiz/vertical pairs of hinges rather than balls; as have getAngle methods
        self.joint.attach(par.body, self.body)
        self.joint.setAnchor((x,y,z))
        self.joint.setAxis((0,0,1))

            
    def makeSceneGraph(self, r,depth):  #return an Inventor tree ready to draw
        sg=SoSeparator()
        
        myMaterial = SoMaterial()
        myMaterial.diffuseColor = (0.0, 0.0, 1.0)  
        sg.addChild(myMaterial)

        rot=SoRotation()
        th = SbRotation(SbVec3f(1,0,0), 3.142/2) #ODE/Inbventor conversion for cylinders
        rot.rotation=th
        sg.addChild(rot)        
        myCylinder = SoCylinder()
        myCylinder.radius = r
        myCylinder.height = depth;
        sg.addChild(myCylinder)
        
        return sg

    def updateForces(self):
        #th = self.joint.getAngle()
        #T_k = -self.k*th            #spring torque
        #self.joint.addTorque(T_k)

        #dth = self.joint.getAngleRate()
        #T_gamma = -self.gamma*dth
        #self.joint.addTorque(T_gamma) #damping

        ##print 'th %f dth %f T_k %f T_gamma %f' % (th,dth,T_k,T_gamma)
        foo=1



class Block(Movable):  #an immobile block in the world, for collisions, a wall.
    def __init__(self, u, x, y, z, lx, ly, lz, cr=1.0,cg=0.0,cb=0.0):  #the center, and lengths, and rgb colors
        Movable.__init__(self,u)  #NB CHANGE THIS BACK TO PHYSICAL AS WELL AS CLASS!
        
        mass = ode.Mass()
        mass.setSphere(500, 1)                
        self.body = ode.Body(self.u.world)
        self.body.setMass(mass)
        self.body.setPosition((x,y,z)) 
        self.sg.addChild(self.makeSceneGraph(lx, ly, lz, cr,cg,cb))

        self.geom = ode.GeomBox(u.space, lengths=(2*lx,2*ly,2*lz))
        self.geom.setBody(self.body)
            
    def makeSceneGraph(self, lx, ly, lz,cr,cg,cb):  #return an Inventor tree ready to draw
        block=SoSeparator()
        tr = SoTransform()
        tr.scaleFactor = (lx, ly, lz)
        block.addChild(tr)
        myMaterial = SoMaterial()
        myMaterial.diffuseColor = (cr,cg,cb)  
        block.addChild(myMaterial)
        block.addChild(SoCube())
        return block




    
# Callback routine to render the floor using OpenGL
def myCallbackRoutine(void, action):
    if not action.isOfType(SoGLRenderAction.getClassTypeId()): return        # only render the floor during GLRender actions
    SoCacheElement.invalidate(action.getState()) #important--as the geometry is changing!

    global u
    for rawGLObject in u.rawGLObjects:
        rawGLObject.drawGL()


  
def main():

    #pdb.set_trace()
    myWindow = SoGui.init(sys.argv[0])
    if myWindow == None: sys.exit(1)

    global u
    u=Universe() #is global, so callbacks can see it!

    h=0.8


    floor = Block(u, 0,0,0,  8,0.1,8, cr=0.0,cg=0.4,cb=0.0)

    if 0:  #arena
        wall1 = Block(u, 0,1,5, 5,1,0.1)
        wall2 = Block(u, 0,1,-5, 5,1,0.1)
        wall3 = Block(u, 5,1,0, .1,1,5)
        wall4 = Block(u, -5,1,0, .1,1,5)
        robot = Robot(u, 0.0, 0.0)  #x,z
    else:    #plus-maze
        wallN = Block(u, 0,h,-5,   1,h,0.1)
        wallE = Block(u, 5,h,0,    0.1,h,1)
        wallS = Block(u, 0,h,5,    1,h,0.1)
        #wallW = Block(u, -5,h,0,   0.1,h,1)
        wallNw = Block(u, -1,h,-3,   0.1,h,2)
        wallNe = Block(u,  1,h,-3,   0.1,h,2)
        wallSw = Block(u, -1,h, 3,   0.1,h,2)
        wallSe = Block(u,  1,h, 3,   0.1,h,2)        
        wallWn = Block(u, -3,h,-1,   2,h,0.1)
        wallWs = Block(u, -3,h, 1,   2,h,0.1)
        wallEn = Block(u,  3,h,-1,   2,h,0.1)
        wallEs = Block(u,  3,h, 1,   2,h,0.1)

        wallNw = Block(u, -5,h,-3,   0.1,h,2)
        wallSw = Block(u, -5,h, 3,   0.1,h,2)


        posterS = Block(u,  0,2*h, 6,   2, 2*h,0.1,   0.0,0.0,0.1)
        posterE = Block(u,  6,2*h, 0,   0.1, 2*h,2,  0.5,0.5,0.0)
   
        robot = Robot(u, -6.0, 0.0)  #x,z        
   
    #TIMER   
    schedulingSensor = SoTimerSensor(schedulingSensorCallback, u)
    schedulingSensor.setInterval(0.01) # once per 1 seconds   0.001 is good
    schedulingSensor.schedule()

    #GL CALLBACK
    myCallback = SoCallback()
    myCallback.setCallback(myCallbackRoutine)
    u.root.addChild(myCallback)


    # Create a renderArea in which to see the scene
    #myRenderArea = SoGuiRenderArea(myWindow)
    myRenderArea = SoGuiExaminerViewer(myWindow)
    u.myCamera.viewAll(u.root, myRenderArea.getViewportRegion())      # Make myCamera see everything.
    myRenderArea.setSceneGraph(u.root)       # Put our scene in myRenderArea, change the title
    myRenderArea.setTitle("ICEASim - Freebots")
    myRenderArea.show()
    SoGui.show(myWindow)  # Display main window
    SoGui.mainLoop()    # Main Inventor event loop

if __name__ == "__main__":
    main()




