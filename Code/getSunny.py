import cPickle
import matplotlib.pyplot as plt
import datetime
import ephem # run "pip install pyephem"
import math
import pytz

# TO RUN ON AMAZON
# import matplotlib
# matplotlib.use('Agg')

states=cPickle.load(open('stateDB.pickle','r'))    
 
#####################################################################
    

o = ephem.Observer()


def getSun(stateID,currentTime,city=None):
    # stateID is a string abbreviation of the state name, ie "IL","AZ",etc.
    # currentTime is local time with tzinfo = state time zone
    # city is optional (defaults to state capital if missing or not found in database)
    # returns sin(altitude) 
    # altitude,azimuth are given in radians

    stateID.capitalize()
    dateStamp=currentTime.astimezone(pytz.utc)

    if city is None:
        city=states[stateID]['capital']        
    else:
        try:
            city=states[stateID][city].capitalize()
        except:
            city=states[stateID]['capital'] 

    o.lat    = states[stateID][city][0]
    o.long   = states[stateID][city][1]
    o.date   = dateStamp
    sun = ephem.Sun(o)
    alt=sun.alt
#    azimuth=sun.az
    return math.sin(alt)


### TEST
tz_state = pytz.timezone("America/Chicago")     
dayTimes=[datetime.datetime(2013, 8, 1, x, 00, 00, 00).replace(tzinfo=tz_state) for x in range(24)]
results=[getSun("IL",d) for d in dayTimes]


t=[]
y=[]

for d in dayTimes:
	t.append(d)
	y.append(getSun('IL',d))

k=[u'America/New_York',
 u'America/Detroit',
 u'America/Kentucky/Louisville',
 u'America/Kentucky/Monticello',
 u'America/Indiana/Indianapolis',
 u'America/Indiana/Vincennes',
 u'America/Indiana/Winamac',
 u'America/Indiana/Marengo',
 u'America/Indiana/Petersburg',
 u'America/Indiana/Vevay',
 u'America/Chicago',
 u'America/Indiana/Tell_City',
 u'America/Indiana/Knox',
 u'America/Menominee',
 u'America/North_Dakota/Center',
 u'America/North_Dakota/New_Salem',
 u'America/North_Dakota/Beulah',
 u'America/Denver',
 u'America/Boise',
 u'America/Shiprock',
 u'America/Phoenix',
 u'America/Los_Angeles',
 u'America/Anchorage',
 u'America/Juneau',
 u'America/Sitka',
 u'America/Yakutat',
 u'America/Nome',
 u'America/Adak',
 u'America/Metlakatla',
 u'Pacific/Honolulu']

