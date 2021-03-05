# FlowControl

## Introduction

FlowControl provides different strategies and models to control pedestrian flow.  
The basic idea is to reroute agents to adjust the pedestrian flow in distinct areas.

The flow control model consists of four sub-models that define
1. how agents move (autonoumous system) (mobility model)
2. how the autonomous system needs to be intervened to achieve a certain goal (controller)
3. how inform agents get informed about the rerouting measure (information dissemination model)
4. how agents react to the rerouting measure (reaction model)

### Mobility model 
To model the pedestrian flow, we use existing locomotion models of the pedestrian dynamics simulator [Vadere](https://gitlab.lrz.de/vadere/vadere).

### Controller (controller model)

The rerouting strategy is modelled by the so-called controller. 
The controller is a set of rules that define how to intervene the autonomous system.
If the state of the system is continously measured and considered in these rules, the controller is a feedback-controller.
Otherwise it is an open-loop controller.
The FlowControl package provides both types of controller models.

### Information dissemination model

Agents need to get informed when they should change their navigation behavior.
The FlowControl package provides different types of information dissemination strategies.

* Signs (space-bound): dynamic signs reroute agents at certain locations
* Individual text messages: agents get a text message disseminated through mobile networks

In case 1, the user needs to define a sign model.
In case 2, the user needs to define a model of the information dissemination.

Inform agents using signs
Characteristic for the sign model is that agents can only be controlled at specific positions in the topography.
* Define the position of the sings in the sign model.
In the control loop:
* Control action: if agents recognize the sign, change their target.


Inform agents using text messages
Characteristic for the text message model is that it takes some time until agents recieve the text message.

* Simplified model: we define a random variable for the time delay from which we draw randomly.
* Realistic model: simulate the information dissemination with a mobile networks simulator.
For case 2, the coupled simulator crownet can be used.

### Reaction model
It depends on the perception and the mooed whether agents react to rerouting measure.
Even if the information about the rerouting is transmitted succesfully, some agents might not react.

We model this with a simplified model:
* time-delay: we define a random variable for the reaction time from which we draw randomly.
* reacitvity: we define a random variable for the reactivity from which we draw randomly.

## System requirements
Python >= 3.7 required. 


## Dependencies

## Other repositories

| Mobility model | Information dissemination |
| ------ | ------ |
| Vadere  | CrowNet²  |

²ncessray if the information dissemination needs to be modelled realistically.

If the simplified information dissemination model is used, it is possible to include the Vadere repository only.

However, we strongly recommend to include the crownet repository. 
CrowNet couples already contains simulators and simulation models necessary to use functionalities of FlowControl.

Please clone the crowNet repository as described [here](https://sam-dev.cs.hm.edu/rover/crownet)

Make sure that the environmental variable CROWNET_HOME points to the crownet repository:
```
echo $CROWNET_HOME
```
Create a config file to make CROWNET_HOME available to FlowControl:
```
echo $CROWNET_HOME > ~/.flowcontrolconfig
```

## Python dependencies

See requirements.txt

We strongly recommend to work with a virtual environment.



