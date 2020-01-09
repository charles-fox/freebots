from cf import *
from pylab import *


class Dendrite:
    def __init__(self, par, w=0):
        self.par=par
        self.w0=w     #raw synaptic weight (to learn etc)
        self.w=w      #effective weight after modification, eg by DA actions 

class Neuron:
    def __init__(self, m=1, epsilon=1,dopamineAction=0):
        self.dendrites = []
        self.dopamineDendrites=[]
        self.dopamineAction = dopamineAction   #0=no action; -1=division; +1=multiplication of weights
        self.u=0           #latest impulse input
        self.k = 0.25        #time step parameter
        self.a=0           #activation
        self.y=0           #firing rate
        self.m=m           #transfer scaling
        self.epsilon = epsilon   #firing threshold

    def addParent(self, par,w=0):
        self.dendrites.append(Dendrite(par,w))

    def addDopamineParent(self, par):
        self.dopamineDendrites.append(Dendrite(par,None)) #no weights for dopamine?

    def applyDopamineWeightModifications(self):
        lam=0  #DA input level
        if not(self.dopamineAction==0):            
            for dopamineDendrite in self.dopamineDendrites:
                lam+=dopamineDendrite.par.y
                DA_factor = 1
                if self.dopamineAction == 1:
                    DA_factor = (1+lam)
                if self.dopamineAction == -1:
                    DA_factor = (1-lam)
                for dendrite in self.dendrites:
                    dendrite.w = dendrite.w0 * DA_factor

    def fire(self):
        self.applyDopamineWeightModifications()        
        self.u=0                          #impulse from this point in time
        for dendrite in self.dendrites:
            self.u+= dendrite.w * dendrite.par.y
        da = -self.k * (self.a - self.u)
        self.a += da
        self.y = self.transferFunction(self.a, self.m, self.epsilon)

    def transferFunction(self, a, m, epsilon):
        if (a-epsilon)<0:
            y=0
        else:
            y= m*(a-epsilon)
        if y>1:
            y=1
        return y
        
class Population():
    def __init__(self, nNeurons, m=1, epsilon=0,dopamineAction=0):
        self.neurons = []
        for i in range(0,nNeurons):
            self.neurons.append(Neuron(m, epsilon,dopamineAction))

    def fire(self):
        for neuron in self.neurons:
            neuron.fire()

    def getLogState(self):
        s=[]
        for neuron in self.neurons:
            s.append(neuron.y)
        return s

    def addParPopOneToOne(self, parPop, w):  #gives same weight to each 1-1 link
        for i in range(0, len(self.neurons)):
            self.neurons[i].addParent(parPop.neurons[i], w)

    def addParPopDiffuse(self, parPop, w): #same w for ALL links
        for i in range(0, len(self.neurons)):
            for j in range(0, len(self.neurons)):
                self.neurons[i].addParent(parPop.neurons[j], w)

    def addParDopamine(self, dopamineNeuron): #assume only one DA neuron
        for neuron in self.neurons:
            neuron.addDopamineParent(dopamineNeuron)

    def clampFiringRates(self, ys):   #used for input pops
        for i in range(0, len(self.neurons)):
            self.neurons[i].y = ys[i]

    def getYs(self):   #returns vector of firing rates
        ys=[]
        for neuron in self.neurons:
            ys.append(neuron.y)
        return ys

class Logger:
    def __init__(self):
        self.loggables=[]  #list of objects to be logged
        self.logs=[]  #there will be one temporal log per object here
        self.logNames=[]  #will be list of strings
    def add(self, obj, strName):
        self.loggables.append(obj)
        self.logs.append([]) #one time list per object
        self.logNames.append(strName)
    def update(self):        
        for i in range(0,len(self.loggables)):
            loggable=self.loggables[i]
            log=self.logs[i]
            s=loggable.getLogState()
            log.append(s)
                
class BasalGanglia:
    def __init__(self, n=4):          #n=number of channels = number of neurons in each pop

        w_Cx_D1 = 1.0
        w_Cx_D2 = 1.0
        w_Cx_STN = 1.0       
        w_STN_GPe = 0.9
        w_STN_GPi = 0.9
        w_D1_GPi = -1.0
        w_D2_GPe = -1.0
        w_GPe_STN = -1.0 
        w_GPe_GPi = 0.3 
        
        y_DA = 0.2
        
        Cx = Population(n)       #we will clamp stuff here over time
        
        
        SNc = Neuron()           #single channel level
        SNc.y = y_DA             #fix DA level for whole sim

        
        D1 = Population(n,dopamineAction=1, epsilon=0.2)
        D1.addParDopamine(SNc)
        D1.addParPopOneToOne(Cx, w_Cx_D1)

        D2 = Population(n,dopamineAction=-1, epsilon=0.2)
        D2.addParDopamine(SNc)
        D2.addParPopOneToOne(Cx, w_Cx_D2)
        
        STN = Population(n, epsilon=-0.25)
        STN.addParPopOneToOne(Cx, w_Cx_STN)  #TODO motor Cx also

        GPe = Population(n,epsilon=-0.2)
        GPe.addParPopOneToOne(D2, w_D2_GPe)
        GPe.addParPopDiffuse(STN, w_STN_GPe)
        STN.addParPopOneToOne(GPe, w_GPe_STN)   #the loop closure

        GPi = Population(n,epsilon=-0.2)
        GPi.addParPopOneToOne(D1, w_D1_GPi)
        GPi.addParPopDiffuse(STN, w_STN_GPi)
        GPi.addParPopOneToOne(GPe, w_GPe_GPi)

        self.Cx=Cx   #store pointers 
        self.SNc=SNc
        self.D1=D1
        self.D2=D2
        self.STN=STN
        self.GPe=GPe
        self.GPi=GPi
        
    def fire(self):
        self.D1.fire()
        self.D2.fire()
        self.STN.fire()
        self.GPe.fire()
        self.GPi.fire()

    def updateInput(self, input):
        self.Cx.clampFiringRates(input)

    #Interface for block simulators (e.g. Brahms, Scicos, etc)
    def step(self, input):
        self.updateInput(input)   #inputs from Cx
        self.fire()
        return self.GPi.getYs()   #the action decisions (from GPi)




#test harness

class InputReader:
    def __init__(self):
        self.t=-1  #time step
    def read(self):
        self.t+=1
        t=self.t
        if t<20:
            return [1,0]
        if t<40:
            return [0,1]
        if t<80:
            return [.5,.4]
        if t<1000:
            return [0,.3]
        return [0,0]        

class TestBG:
    def __init__(self):
        bg = BasalGanglia(n=2)

        logger=Logger()  #set up what data to log
        logger.add(bg.Cx,'Cx')
        logger.add(bg.D1,'D1')
        logger.add(bg.D2,'D2')
        logger.add(bg.STN,'STN')
        logger.add(bg.GPe,'GPe')
        logger.add(bg.GPi,'GPi')
        
        inputReader = InputReader()
        ins=[]
        outs=[]
        for i in range(0,200):
            input = inputReader.read()

            bg.step(input)
            
            logger.update()

            ins.append(input)
            outs.append(bg.GPi.getYs())

        #pdb.set_trace()

        clf()
        for i in range(0,6):  #plot results logs
            subplot(6,1,i+1)
            imshow(array(logger.logs[i]).transpose(), interpolation='nearest',aspect='auto' )
            ylabel(logger.logNames[i])
            colorbar()
        show()

        #pdb.set_trace()


#testBG = TestBG()   #active this line to run a self-contained test
