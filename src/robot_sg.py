from pivy.sogui import *
from pivy.coin import *

def makeRobotSceneGraph():
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
        
      

    #internal scaling -- not related to physics etc
    tri = SoTransform()
    tri.translation = (0, .2, 0)
    tri.scaleFactor = (.1, .1, .1)

    rot = SoRotation()
    rot.rotation.setValue(SbRotation(   SbVec3f(0,-1,0),-1.57 ))

    robot = SoSeparator()
    robot.addChild(tri)
    robot.addChild(rot)
    robot.addChild(body)               
    robot.addChild(head)
        
    return robot
