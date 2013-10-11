energywise
==========
[<img src="http://dssg.io/img/partners/lbnl.png" width="200">](http://www.lbl.gov/)
[![Agentis](https://github.com/dssg/energywise/wiki/img/agentis.png)](http://agentisenergy.com/)

An **energy analytics tool** to make commercial building more energy efficient. Energywise profiles a building's energy consumption and gives building managers insights on how to mke their buildings more energy efficient.

This project is a rewrite and extension of Lawrence Berkeley National Laboratory's open source [fingerprint tool](https://fingerprint.lbl.gov/).
 
This project is part of the 2013 [Data Science for Social Good](http://dssg.io) fellowship, in partnership with [Lawrence Berkeley National Laboratory](http://www.lbl.gov/) and [Agentis Energy](http://agentisenergy.com/).


## The Problem: uncertain energy savings for building retrofits
Buildings use too much energy, and nobody knows what to do about it.

Normally, the people that can take action on what goes on in a building are building managers. To reduce a building's energy consumption, they need to know how their building uses energy to begin with. 

Even though they would like to spend less in their energy bills, it is too risky to decide what changes to make in their building to become more energy efficient because accurately quantify savings is hard. As a result, building energy efficiency goes unexploited.

**[Read more about the problem in the wiki](../../wiki/problem)**

## The Solution: energy analytics tool

Energywise is a tool that helps buildings managers identify ways to reduce their building's energy consumption. The tool consumes energy use data collected by a building's smart meter, analyzes the data, and generates a report that iluminates the connection between building behaviors and electric consumption.

The analysis includes:

1. *Phantom load*: each building has systems that operate all the time. We estimate the building's baseline energy consumption produced by its systems.

2. *Periodicity*: buildings have regular, predictable cycles in their energy consumption. Examples include:  
	- Weekend/Weekday
	- Time of the day 
	- Holidays
	- Schedule

3. *Anomaly detection*: Classifying days according to their energy consumption patterns. Days can be grouped according to their cycles, periodicity and variability. 
![anomalies](http://dssg.io/img/posts/anomaly_detection.png)

4. *Outlier detection*: within each group of days, particularly extreme days can be recognized. This helps identify erratic energy behavior within a building.
![outliers](http://dssg.io/img/posts/outlier.png)

5. *Temperature sensitivity classification* of a building:
	- High sensitivity: energy consumption is extremely reactive to outside temperature both when it is high and low.
	- Medium sensitivity: energy consumption is very reactive but only when temperature is high. This can be due to alternative heating systems.
	- Low sensitivity: the consumption of energy is not highly correlated with outside temperature.
    
6. *Peak prediction*: Modeling and prediction of energy consumption yields an estimate on the savings due to the elimination of peaks in consumption.
![peak](http://dssg.io/img/posts/peak_prediction.png)

**[Read more about our analysis in the wiki](../../wiki/methodology)**

# The data: building energy interval data
[Agentis energy](http://agentisenergy.com/), a company that builds software for energy utilities, supplied us with anonymized, hourly meter data - electricity usage in kWh - for roughly 7,000 buildings. A year's worth of data for one building looks like this:

![interval](http://dssg.io/img/posts/interval_data.png)

They also gave us the [NAICS code](http://en.wikipedia.org/wiki/NAICS) and business type for each building. Because the data was anonymized, and we didn't know the location of these buildings, Agentis provided us with the associated temperatures for the same time series.

**[Read more about the data in the wiki](../../wiki/data)**

## Project Layout

* [`Code/`](Code) contains all the python scripts developed for the tool.
    + [`clean_brecs.py`](Code/clean_brecs.py) Converts to cero temperatures that were missing values in web querying.
    + [`holiday.py`](Code/holiday.py) Generates a list of the federal holidays in any given year.
    + [`plotter_new.py`](Code/plotter_new.py) Core of the project, generates the full pdf report for each building.
    + [`query_temps.py`](Code/query_temps.py) For a given building record and location, looks for the temperatures in wunderground (you need to add your personal key to use it).
    + [`report_card.py`](Code/report_card.py) Generates a python dictionary from which one can extract all the statistics used in the generation of the plots in the final report.
    + [`temps_to_building_pkl.py`](Code/temps_to_building_pkl.py) Includes the temperatures into the building record.
    + [`utils.py`](Code/utils.py) All the helper functions.
    + [`versions.py`](Code/versions.py) Run this to verify versions of the required packages.

## Installation Guide
```python
git clone https://github.com/dssg/energywise.git
cd energywise
python setup.py install
```
## Team

## Contributing to the Project
- Feel free to create an issue for any bugs you encounter.
- To get involved with this project, reach out to <dssg-energywise@googlegroups.com>

## License
MIT license, see [LICENSE.txt](LICENSE.txt)
