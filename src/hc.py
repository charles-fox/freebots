#This is the KFKI model from deliverable D19.

from math import *
from pylab import *
from numpy import *   #this MUST come after pylab, or zeros function gets set to int version!
from random import *
from cf import *
import copy
import cPickle
import traceback

print "--LOADING HC"

def imagesc(img):
    clf()
    imshow(img, interpolation='nearest',aspect='auto' )
    colorbar()

def randomMatrix(n_rows, n_cols):
    M =  zeros((n_rows, n_cols))
    for r in range(0,n_rows):
        for c in range(0,n_cols):
            M[r,c]=random()
    return M

def sparsify(h, s):
    s=min(s,len(h))
    out = zeros(h.shape)
    h_sorted = copy.copy(h)
    h_sorted = h_sorted.transpose()
    h_sorted.sort()
    h_sorted = h_sorted.transpose()
    for i in range(len(h)-1, len(h)-s-1, -1):
        out[where(h==h_sorted[i])]=h_sorted[i]   #TODO tiny bug here, if last number is duplicated then both dups are allowed; real neurons should all be copntinuos valued.
    return out


def normalizeL1(xs):   #normalize to L2 norm
    return xs / sum(xs)         

def normalizeL2(xs):   #normalize to L2 norm
    return xs / math.sqrt(sum(xs**2))         
           
class DentateGyrus:
    def __init__(self,n_in=4,n_out=10):
        self.n_in = n_in
        self.n_out = n_out
        self.W = randomMatrix(n_out, n_in)
        self.alpha = 0.01 #learning rate (TODO can we bayesianize?)

        self.input = zeros([n_in,1])   #col vectors; cache for debugging
        self.h = zeros([n_out,1])    #activations (before pruning)
        self.out = zeros([n_out,1])    #we remember these, for learning
        self.sparsity = 8            #max number of activations to keep

    def fire_recall(self, input):
        self.input=input
        self.h=dot(self.W, self.input)
        self.out = normalizeL1(sparsify(self.h, self.sparsity))

    def fire_learn(self, input): #assumes in,out already computed and set
        self.fire_recall(input)
        for j in range(0,self.W.shape[0]): #rows, outputs
            for i in range(0,self.W.shape[1]): #cols, inputs
                dW=self.alpha*self.out[j]*(self.input[i] - self.W[j,i])  #eqn (3)
                self.W[j,i] = self.W[j,i]+dW
                
class CA3:
    def __init__(self, n_in_EC, n_in_DG, n_out):   #where in is from EC
        self.W_EC = randomMatrix(n_out, n_in_EC)
        self.W_DG = randomMatrix(n_out, n_in_DG)  #TODO think: hashing/priming again?
        self.W_RC = randomMatrix(n_out, n_out)  #recurrant connections
        self.alpha_EC = 0.05 #learning rate (can we bayesianize?)
        self.alpha_RC = 0.05 #learning rate (can we bayesianize?)
        self.beta_RC = 0.002 #forgetting rate
        self.chi = 1.0  #relative weight of RC to PP

        self.in_EC = zeros([n_in_EC,1])   #col vectors
        self.in_DG = zeros([n_in_DG,1])   #col vectorsn

        self.sparsity = 5
        self.out = zeros([n_out,1])    #we remember these, for learning

    def fire_learn(self, in_EC, in_DG):   #during learning, CA3 actvn is determined by the MFs from DG -- RCs are disabled
        self.in_DG = in_DG        #mossy fibre input from DG
        self.in_EC = in_EC        #perforant path (for leanring signal only, not activation)

        h = dot(self.W_DG, self.in_DG)    #eqn (4).   ACTIVATION is not affected by EC, but learning IS
        self.out =  normalizeL1(sparsify(h,s=5))

        #PP, EC->CA3 path
        for j in range(0,self.W_EC.shape[0]):          #rows, outputs
            for i in range(0,self.W_EC.shape[1]):      #cols, inputs
                dW=self.alpha_EC*self.out[j]*(self.in_EC[i] - self.W_EC[j,i])  #eqn (5)
                self.W_EC[j,i] = self.W_EC[j,i] + dW
        #RCs
        for j in range(0,self.W_RC.shape[0]):          #j=rows, outputs
            for i in range(0,self.W_RC.shape[1]):      #i=cols, inputs (is square)
                dW=self.alpha_RC*self.out[i]*self.out[j]*(1-self.W_RC[j,i]) - self.beta_RC*self.W_RC[j,i]   #eqn (6)
                self.W_RC[j,i] = self.W_RC[j,i] + dW

    def fire_recall(self, in_EC):
        #pdb.set_trace()
        self.in_EC = in_EC                      #Perforant Path input direct from EC
        h_EC = dot(self.W_EC, self.in_EC)       #activtn due to DG
        
        n_cycles = 5                            #KFKI are a bit vague on this
        for i in range(0,n_cycles):
            h_CA3 = dot(self.W_RC, self.out)    #recurrent activation
            h = h_EC+self.chi*h_CA3             #KFKI-D13-eqn(8)
            self.out =  normalizeL1(sparsify(h, self.sparsity))

class GridCell:
    def __init__(self, sf=1, phase=0):
        self.phase=phase
        self.sf=sf
        self.out = 0
    def fire(self, x, z):
        a1 = pow(cos(self.sf*(x+z)+self.phase),2)
        a2 = pow(cos(self.sf*(x-z)+self.phase),2)
        self.out= 0.5*(a1+a2)  #weighted average
        return self.out

    def plotFields(self):
        n=100
        clf()
        res=zeros((n,n))
        for ix in range(0,n):
            for iz in range(0,n):
                x=rescale(0,n, -5, 5, ix)   #+-5 is arena min/max
                z=rescale(0,n, -5, 5, iz)
                self.fire(x,z)
                res[ix,iz] = self.out              
        imshow(res)
        colorbar()
        show()
            
class EntorhinalCortex:    #visual ins can be COMPUTED from x,z THETA
    def __init__(self):
        n_senses = 2    #non-grid cells EC outputs (eg vision, touch)
        self.gridCells = []
        for scale in frange(.5, 2.5, 0.5):
            for phase in frange(0,pi,pi/5):
                self.gridCells.append(GridCell(scale, phase))
        #pdb.set_trace()
        self.out = zeros((len(self.gridCells)+n_senses,1))  #summarized activation vector

    def fire(self,x,z,th):  #TODO needs to know position AND ROTATION TODO
        for i in range(0,len(self.gridCells)):
            self.out[i] = self.gridCells[i].fire(x,z)

        #vidual inputs (as distance sensors) #TODO at present thse just compute L along the panel's wall.
        #TODO have a whole bunch of binary none/blue/yellow sensors, at diff angles.  DG will find nice eigvectors of them.
        n=len(self.gridCells)
        #pdb.set_trace()
        #self.out[n  ]= x+(6.0-z)*math.tan(th)  #dist to south panel plane
        #self.out[n+1]= z+(6.0-x)/math.tan(th)  #dist to east panel plane

        self.out[n  ]= math.sqrt(x**2 + (6-z)**2)  #dist to south panel center
        self.out[n+1]= math.sqrt(z**2 + (6-x)**2)

        self.out = normalizeL2(self.out)
        return self.out

class Hippocampus:  
    def __init__(self):
        self.EC = EntorhinalCortex()   #has 20 grid cells by default
        self.DG = DentateGyrus(n_in=len(self.EC.out), n_out=8)
        self.CA3 = CA3(len(self.EC.out), len(self.DG.out), n_out=30)  #try 30 place cells

    def fire_recall(self, x,z,th): #input is the robot's x,z position
        self.EC.fire(x,z,th)
        self.DG.fire_recall(self.EC.out)
        self.CA3.fire_recall(self.EC.out)

    def decodeLocation(self):
        x_hat = dot(self.cx, self.CA3.out)
        z_hat = dot(self.cz, self.CA3.out)        
        return [x_hat[0], z_hat[0]]   #convert from pylab to list
        
    def fire_learn(self,x,z):        #TODO add visuals
        self.EC.fire(x,z,0)             #no visuals to grid cells
        self.DG.fire_learn(self.EC.out)
        self.CA3.fire_learn(in_EC=self.EC.out, in_DG=self.DG.out)


    def makePlaceRegression(self):      #computers linear decoding coeffs      
        n_locs = 27
        n_pcs = len(self.CA3.out)   #number of Place Cells        
            
        xs  = zeros(n_locs**2)       #locations
        zs  = zeros(n_locs**2)
        pcs = zeros((n_locs**2, n_pcs))   #place cell outs
        
        i=0
        for ix in range(0,n_locs):
            print ix
            for iz in range(0,n_locs):
                x=rescale(0,n_locs, -5, 5, ix)   #+-5 is arena min/max
                z=rescale(0,n_locs, -5, 5, iz)
                self.fire_recall(x,z,0) #TODO th            
                xs[i] = x
                zs[i] = z
                pcs[i,:]  = self.CA3.out.transpose()
                i+=1
        self.pcs=pcs
        self.cx = linalg.lstsq(pcs, xs)[0]
        self.cz = linalg.lstsq(pcs, zs)[0]

        
#class Bach:   #Basic ArCHitecture for joining modules together (like Brahms but considerably simpler)
#    def __init__(self):
#        self.HC = Hippocampus()
#        self.BG = BasalGanglia()
#        self.out = (0,0)  #will store final motor control signals
#    def fire(self, x,y):
#        self.HC.fire_learn(x,y)  #TODO think about when to switch learn/recall mode
#        self.BG.fire(TODO)
#        #TODO use the outputs of the bio structures to decide where to move to in some toy task
        

#cell =GridCell(sf=.5, phase=0*pi/5)
#cell.plotFields()


 #live, Brahmsified-style version for ICEAsim 
class PreTrainedHippocampus:  
    def __init__(self):
        print "ptHC1"
        file=open("/home/charles/dev/freebots/HC",'r')
        self.HC = cPickle.load(file)
        file.close()        
        self.HC.makePlaceRegression()
        
    def step(self, x,z,th):    #API for block sims (input not currently used, as just navigating off grid cells) TODO add theta
        self.HC.fire_recall(x,z,th)
        return self.HC.decodeLocation()
        return [1,1]

        

#train up a HC from random locations -- TODO add visual inputs
class TestHC():
    def __init__(self):
        HC = Hippocampus()
        self.HC=HC               
        n_locs = 10

        #TRAINING
        #pdb.set_trace()
        if 0:
            for epoch in range(0,5):
                for ix in range(0,n_locs):
                    print ix
                    for iz in range(0,n_locs):

                        #TODO for angles theta as well (used in vision)
                        
                        x=rescale(0,n_locs, -5, 5, ix)   #+-5 is arena min/max
                        z=rescale(0,n_locs, -5, 5, iz)
                        HC.fire_learn(x,z)               #TODO add theta
                     
            file=open("HC",'w')
            cPickle.dump(HC,file)
            print "saved HC"
            file.close()
        else:
            file=open("HC",'r')
            HC = cPickle.load(file)
            self.HC=HC
            file.close()

            #some nice plots to look at:
            self.HC.EC.gridCells[0].plotFields()
            self.makePlaceCellImages()

    def makePlaceCellImages(self):            
        #EXAMINE PLACE CELL RF'S
        n_locs = 10
        n_pcs = len(self.HC.CA3.out)   #number of place cells        
        imgs=[] 
        self.imgs=imgs
        for i in range(0,n_pcs):           #allocate space for RF images
            imgs.append(zeros((n_locs,n_locs)))
        
        res=zeros((n_locs,n_locs))
    
        for ix in range(0,n_locs):
            print ix
            for iz in range(0,n_locs):
                x=rescale(0,n_locs, -5, 5, ix)   #+-5 is arena min/max
                z=rescale(0,n_locs, -5, 5, iz)
                self.HC.fire_recall(x,z,0)
                for i in range(0,n_pcs):  #for each place cell, write this coord in its image
                    imgs[i][ix,iz] = self.HC.CA3.out[i]

    def showECResponses(self):          
        n_locs = 10
        img = zeros((n_locs*n_locs, len(self.HC.EC.gridCells)))
        r=0
        for ix in range(0,n_locs):
            print ix
            for iz in range(0,n_locs):
                x=rescale(0,n_locs, -5, 5, ix)   #+-5 is arena min/max
                z=rescale(0,n_locs, -5, 5, iz)
                self.HC.fire_recall(x,z,th)
                row = self.HC.EC.out.transpose()
                row = (row-mean(row))/std(row) #for PCA
                
                img[r,:]=row
                r+=1
        clf()
        imagesc(img)

        cov=dot(X.transpose(),X)
        
        return img

    def showDGResponses(self):          
        n_locs = 10
        img = zeros((n_locs*n_locs, len(self.HC.DG.out)))
        r=0
        for ix in range(0,n_locs):
            print ix
            for iz in range(0,n_locs):
                x=rescale(0,n_locs, -5, 5, ix)   #+-5 is arena min/max
                z=rescale(0,n_locs, -5, 5, iz)
                self.HC.fire_recall(x,z,th)
                img[r,:]=self.HC.DG.out.transpose()
                r+=1
        clf()
        imagesc(img)
        show()
 
        
        
    def showResponses(self, x,z,th):
        self.HC.fire_recall(x,z,th)
        clf()
        n=3

        subplot(n,1,1)
        out=self.HC.EC.out
        bar(range(0,len(out)),out)
        xlabel('EC')

        subplot(n,1,2)
        out=self.HC.DG.out
        bar(range(0,len(out)),out)
        xlabel('DG')

        subplot(n,1,3)
        out=self.HC.CA3.out
        bar(range(0,len(out)),out)
        xlabel('CA3')
        show()


#disable the below if Im being imported by freebots -- is for testing only
if __name__ == "__main__":
    try:
        test = TestHC()
    except:
        import pdb, sys
        e, m, tb = sys.exc_info()   #exception info
        print m
        traceback.print_tb(tb)
        pdb.post_mortem(tb)




#TODOs.  Does DG improve CA3 over direct EC inputs?
