sys = sml_system;

%KFKI Hippocampus
state = [];  
state.filename = '/home/charles/dev/freebots/IceaMeatHC.py';
state.stepfunction = 'IceaMeatHC';
state.n_out = 4;
sys = sys.addprocess('meatHC', 'dev/temp/python', 1, state);

%USFD Basal Ganglia
state = []; 
state.filename = '/home/charles/dev/freebots/IceaMeatBG.py';
state.stepfunction = 'IceaMeatBG';
state.n_out = 4;
sys = sys.addprocess('meatBG', 'dev/temp/python', 1, state);

%ICEASim
state = [];  
state.filename = '/home/charles/dev/freebots/pyrobrahms.py';
state.stepfunction = 'pyrobrahms';
state.n_out = 2;
sys = sys.addprocess('pyrobrahms2', 'dev/temp/python', 1, state);

sys = sys.link('pyrobrahms2>out', 'meatHC');
sys = sys.link('meatHC>out', 'meatBG');
sys = sys.link('meatBG>out', 'pyrobrahms2');

% construct the simulation
cmd = brahms_command;
cmd.executionStop = 200;           % stop the simulation after one second
cmd.all = true;                  % store all the outputs of the entire system
cmd.MultiThread = false;
%cmd.voices = 2;                 %enables concerto with 2 processes (replace threads)

% run the simulation of the system
out = brahms(sys, cmd); 

