/*
________________________________________________________________

	This file is part of BRAHMS
	Copyright (C) 2007 Ben Mitch(inson)
	URL: http://sourceforge.net/projects/abrg-brahms

	This program is free software; you can redistribute it and/or
	modify it under the terms of the GNU General Public License
	as published by the Free Software Foundation; either version 2
	of the License, or (at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program; if not, write to the Free Software
	Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
________________________________________________________________

	Subversion Repository Information (automatically updated on commit)

	$Id: python.cpp,v 1.3 2008/02/21 11:32:16 charles Exp $
	$Rev:: 965                                                 $
	$Author: charles $
	$Date: 2008/02/21 11:32:16 $
________________________________________________________________

*/

//#define PRINT_DEBUG



//	group data (template group)
#include "group.h"

#include <Python.h>


//	process information
#define COMPONENT_FLAGS FLAG_NOT_RATE_CHANGER /* zero or more of FLAG_NOT_RATE_CHANGER, FLAG_NEEDS_ALL_INPUTS */



struct DOUBLE_ARRAY
{
	DOUBLE* data;
	Dims dims;
};




class __CLASS_CPP__ : public Process
{



////////////////	'STRUCTORS

public:

	__CLASS_CPP__();
	~__CLASS_CPP__();




////////////////	SUPERVISOR INTERFACE
	
	void event(Event& event);




////////////////	MEMBERS, THE PRIVATE DATA STORE OF THE CLASS

private:

  void callPython(bool init, vector<DOUBLE_ARRAY>& inputs, vector<DOUBLE_ARRAY>& outputs);
  string str_filename;
  string str_stepfunction;
  int n_out;   //assume python always results a vector of n_out elements.
 
  PyObject *stepfunction, *global_dict, *main_module;

};





////////////////	'STRUCTORS

__CLASS_CPP__::__CLASS_CPP__()
{
	cout << "template constructor" << endl;
}

__CLASS_CPP__::~__CLASS_CPP__()
{
	cout << "template destructor" << endl;
}


//	python function name is stored in member variable "function" (std::string)
//	"init" is true for the _single_ init call, false for the _multiple_ step calls
//	"time" holds timing information, as usual, if you need it
//TODO CF this is the hook.  bool flag indicates init/step. vector is OF double arrays (so can be multiple in and out)
void __CLASS_CPP__::callPython(bool init, vector<DOUBLE_ARRAY>& inputs, vector<DOUBLE_ARRAY>& outputs)
{
  if(init) {

    Py_Initialize();


    PyRun_SimpleString("print 'hello from python'");
    PyRun_SimpleString("import os");
    PyRun_SimpleString("print os.listdir('.')");

    // printf("opening py file\n");

    FILE* file1 = fopen(this->str_filename.c_str(), "r");  

    //printf("opened py file\n");

    PyRun_SimpleFile(file1, this->str_filename.c_str());

    //printf("run py file\n");


    this->main_module = PyImport_AddModule("__main__");

    //printf("ini1\n");

    this->global_dict = PyModule_GetDict(main_module);

    //printf("ini2\n");

    this->stepfunction = PyDict_GetItemString(global_dict, this->str_stepfunction.c_str());

    //printf("python:init OK\n");

    return;
  } 
  else {      //STEP

    //cout << "a" << endl;

    int n_inputs = inputs.size();
    PyObject* myTupleOfTuples;
    myTupleOfTuples = PyTuple_New(n_inputs);  
    
    //cout << n_inputs <<endl;

    vector<DOUBLE_ARRAY>::iterator itr = inputs.begin();
    while(itr!=inputs.end())   //each input map
      {

	//cout << "b1" << endl;

	//create a tuple for this input
	//we will just pass to python as a 1D list for now.  Need to get total size though.
	int n = itr->dims.getNumberOfElements();
	PyObject* myTuple;
	myTuple = PyTuple_New(n);
	for (int i=0; i<n; i++) {
	  double datum = itr->data[i];
	  PyTuple_SetItem(myTuple, i, PyFloat_FromDouble(datum));
	}
	//add this input map's tuple to the python arg
	PyTuple_SetItem(myTupleOfTuples, itr-inputs.begin(), myTuple);
	itr++;
      }

    //cout << "b2" << endl;

    PyObject* args;                     //wrap the tuple in another args tuple and call out to Python

    //cout << "b3" << endl;

    args = PyTuple_New(1);

    //cout << "b4" << endl;

    PyTuple_SetItem(args, 0, myTupleOfTuples);

    //cout << "b5" << endl;
    //cout << this->str_stepfunction << endl;

    //cout << "b6" << endl;
    

    PyObject* result = PyObject_CallObject(this->stepfunction, args);

    //cout << "c" << endl;


    for(int i=0; i<this->n_out; i++) {        //for now , assume there is just a single 1D output tuple     

      //cout << "d" << endl;

      PyObject* myDatum = PyTuple_GetItem(result, i); 
      //cout << "e" << endl;
      double d =  PyFloat_AsDouble(myDatum);

      //cout << "f" << endl;
    

      outputs[0].data[i] = d;
    }
  }
}


////////////////	OPERATION METHODS

void __CLASS_CPP__::event(Event& event)
{
	cout << "template->event(" << coreGetEventTypeString(event.type) << ")" << endl;
	
	switch(event.type)
	{

		case EVENT_RUN_SERVICE:
		{
			//	get number of inputs
			UINT32 I = iif.getNumberOfPorts();

			//	access my inputs
			vector<DOUBLE_ARRAY> inputs;
			for (UINT32 i=0; i<I; i++)
			{
				//	access (n+1)th input
				Handle hInput = iif.getPort(i);
				Data* input = iif.getData(hInput);

				DOUBLE_ARRAY array;
				array.data = (DOUBLE*)numeric_get_content(input);
				ExtendedStructure* st = numeric_get_structure(input);
				array.dims = st->dims;
				inputs.push_back(array);
			}

			//	get number of outputs
			UINT32 numOutputs = oif.getNumberOfPorts();

			//	access outputs
			vector<DOUBLE_ARRAY> outputs;
			for (UINT32 o=0; o<numOutputs; o++)
			{
				//	access (n+1)th output
				Data* output = oif.getData(oif.getPort(o));
				DOUBLE* outputContents = (DOUBLE*)numeric_get_content(output);
				ExtendedStructure* st = numeric_get_structure(output);
				DOUBLE_ARRAY array;
				array.data = outputContents;
				array.dims = st->dims;
				outputs.push_back(array);
			}

			//	call the python code
			callPython(false, inputs, outputs);

			//	ok
			event.response = RESPONSE_OK;
			return;
		}

		case EVENT_INIT_PRECONNECT:
		{
			//	extract fields from init data
			MatMLNode nodePars(event.xmlNode);
			this->str_filename = nodePars.getField("filename").getSTRING();
			this->str_stepfunction = nodePars.getField("stepfunction").getSTRING();
			this->n_out    = nodePars.getField("n_out").getUINT32();

			//	ok
			event.response = RESPONSE_OK;
			return;
		}

		case EVENT_INIT_CONNECT:
		{
			//	on first call, create single output
			if (event.flags & FLAG_FIRST_CALL)
			{
				Handle hOutput = oif.addPort("dev/std/data/numeric", 0);
				oif.setPortName(hOutput, "out");
				Data* o = oif.getData(hOutput);
				numeric_set_structure(o, TYPE_DOUBLE | TYPE_REAL, Dims(n_out));   //one-D output, with 2 elements
			}

			//	ok
			event.response = RESPONSE_OK;
			return;
		}

		case EVENT_INIT_POSTCONNECT:
		{
			//	get number of inputs
			UINT32 I = iif.getNumberOfPorts();

			//	access my inputs
			vector<DOUBLE_ARRAY> inputs;
			for (UINT32 i=0; i<I; i++)
			{
				//	access (n+1)th input
				Handle hInput = iif.getPort(i);
				Data* input = iif.getData(hInput);

				DOUBLE_ARRAY array;
				array.data = (DOUBLE*)numeric_get_content(input);
				ExtendedStructure* st = numeric_get_structure(input);
				array.dims = st->dims;
				inputs.push_back(array);
			}

			//	get number of outputs
			UINT32 numOutputs = oif.getNumberOfPorts();

			//	access outputs
			vector<DOUBLE_ARRAY> outputs;
			for (UINT32 o=0; o<numOutputs; o++)
			{
				//	access (n+1)th output
				Data* output = oif.getData(oif.getPort(o));
				DOUBLE* outputContents = (DOUBLE*)numeric_get_content(output);
				ExtendedStructure* st = numeric_get_structure(output);
				DOUBLE_ARRAY array;
				array.data = outputContents;
				array.dims = st->dims;
				outputs.push_back(array);
			}

			//	call the python code
			callPython(true, inputs, outputs);

			//	ok
			event.response = RESPONSE_OK;
			return;
		}

		case EVENT_RUN_PLAY:
		{
			/*
				PHASE: perform any processing that must occur whilst the process is
				running in its run-phase environment, e.g. initialisation of GUIs
			*/

			//	ok
			event.response = RESPONSE_OK;
			return;
		}

		case EVENT_RUN_RESUME:
		{
			/*
				PHASE: perform processing that must occur as late as possible (wallclock
				time) before the process begins its initial step(), e.g. start hardware
				clocks this time-slice is shared, so the process should do as little
				processing as possible, performing operations in an earlier phase if possible
			*/

			//	ok
			event.response = RESPONSE_OK;
			return;
		}

		case EVENT_RUN_PAUSE:
		{
			/*
				PHASE: perform processing that must occur as soon as possible (wallclock
				time) after the process has completed its final step(), e.g. stop hardware
				clocks. this time-slice is shared, so the process should do as little
				processing as possible, deferring operations until a later phase if possible.
			*/

			//	ok
			event.response = RESPONSE_OK;
			return;
		}

		case EVENT_RUN_STOP:
		{
			/*
				PHASE: perform any further processing that must occur whilst the process is
				running in its run-phase environment, e.g. termination of GUIs. there is no time
				pressure during this or later phases.
			*/

			//	ok
			event.response = RESPONSE_OK;
			return;
		}

		case EVENT_STATE_GET:
		{
			/*
				PHASE: this is an opportunity for the process to update the SystemML State
				that it was initially passed to reflect changes in its internal state that
				occurred during run phase (not implemented at time of writing).
			*/

			//	ok
			event.response = RESPONSE_OK;
			return;
		}


#include "events.cpp"


	}

	//	raise an exception if you run into trouble during event(). the return value
	//	indicates whether you processed the event.


	
}










////////////////	CREATE COMPONENT

C_EXPORT Component* CreateComponent()
{
	return new __CLASS_CPP__;
}



