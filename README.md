energywise
==========

An energy analytics tool to make commercial building more energy efficient.

energywise is a project that helped in the enhancement of a tool that profiles a building's energy consumption and gives insights as to how to become more energy efficient. 

This project is part of the 2013 [Data Science for Social Good](http://dssg.io) fellowship, in partnership with [Lawrence Berkeley National Laboratory](http://www.lbl.gov/) and with [Agentis Energy](http://agentisenergy.com/). The original tool enhanced during this project is [LBNL's fingerprint tool ](https://fingerprint.lbl.gov/) now an open source project and to which our efforts we hope can complement their work.


## The Problem
Buildings use too much energy, and nobody knows what to do about it.

Normally, the people that can take action on what goes on in a building are building managers. For that they need to know how their building behaves in its energy consumption. 

Even though they would like to spend less in their energy bills, it is too risky to decide what changes to make in their building to become more energy efficient because no one can accurately quantify savings.

In addition, they have so many tasks to do that their energy efficiency is usally pushed back in their list of priorities. 

energywise is a tool that will help them. They will run this tool inputing the data collected by their smart meter on their building's energy consumption. Our tool iluminates the connection between the usage and the electric consumption.


## The Project

### Input

The tool receives hourly interval data on a building's energy consumption. 

### Output

With the information provided by the user a report is created for the building. The analysis includes:

1. Phantom load: each building has systems that operate all the time and which provide for its basic functionality and maintenance. We estimate this baseline for the consumption of energy in a building.
2. Periodicity: buildings have cycles in their consumption of energy. Some examples include:  
	- Weekend/Weekday
	- Time of the day 
	- Holidays
	- Schedule
3. Identification of the types of days in a buildings consumption: days can be grouped according to their cycles, periodicity and variability. 
4. Identification of outliers: within each group of days and the profiles, particularly extreme days can be recognized. This identifies erratic behavior within a building.
5. Classification of a building according to its sensitivity to temperature
	- High sensitivity: energy consumption is extremely reactive to outside temperature both when it is high and low.
	- Medium sensitivity: energy consumption is very reactive but only when temperature is high. This can be due to alternative heating systems.
	- Low sensitivity: the consumption of energy is not highly correlated with outside temperature.
6. Modeling and prediction of energy consumption yields an estimate on the savings due to the elimination of peaks in consumption.

## Project Layout

* [`Code/`](Code) contains all the python scripts developed for the tool
    + [`clean_brecs.py`](clean_brecs) converts to cero temperatures that were missing values in web querying
    + 
## Installation Guide
```python
git clone https://github.com/dssg/energywise.git
cd energywise
python setup.py install
```

## Contributing to the Project
- Feel free to create an issue for any bugs you encounter.
- To get involved with this project, reach out to <dssg-energywise@googlegroups.com>

## License
MIT license, see [LICENSE.txt](LICENSE.txt)
