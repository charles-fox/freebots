
class SimpleController:
    def __init__(self, robot):
        self.robot = robot    
        self.x_hat=0
        self.z_hat=0

        self.counter=0

    def step(self):
        tx = 0.0
        tz = 0.0   #target location        #TODO: problems getting to x=-ve z=0

        self.robot.moveDirectTo(tx,tz)
