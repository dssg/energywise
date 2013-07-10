from utils import data_loc, fig_loc, qload, qdump
from utils import fill_in, daterange
from collections import defaultdict
import string
import time
import cPickle as pickle
import numpy as np
import pytz
import datetime as rdatetime
from datetime import datetime

from dateutil import tz

alt_str = "_updated" #change this if you cange the examples csv file
only_one_year = True

utc_tz = pytz.utc
# The Agentis data is all from Illinois
tz_used = pytz.timezone("US/Central")


def timeutc_to_dow(time):
    '''Given a UTC Unix timestamp, returns the day of the week in Central time. 0 = Monday, 6 = Sunday'''
    dt = datetime.fromtimestamp(time, utc_tz)
    dt = dt.astimezone(tz_used)
    return dt.weekday()

def timeutc_to_hod(time):
    '''Given a UTC Unix timestamp, returns the hour of day in Central time. 0 = Midnight, 23 = 11PM'''
    dt = datetime.fromtimestamp(time, utc_tz)
    dt = dt.astimezone(tz_used)
    return dt.hour

def get_default_for_map():
    '''A helper function used for creating the defaultdict desc_map. in get_desc_map'''
    return (0, 0)

def get_desc_map():
    '''This function uses Examples.csv to make  desc_map.pkl -- a file containing the description map. The description map is a dictionary mapping building id (int) to a (sic, building type) pair (int, string).'''

    finn_desc = data_loc + "Agentis/Examples" + alt_str + ".csv"
    fin_desc  = open(finn_desc)
    
    desc_map = {}
    dummy    = fin_desc.readline() #skip header info
    
    for l in fin_desc:
        line    = map(string.strip, l.split(","))
        line    = [string.strip(x, '"') for x in line]
        loc_id, sic, btype = tuple(line)
        loc_id  = int(loc_id)
        if sic == "NULL":
            sic = 0
        else:
            sic = int(sic)
        desc_map[loc_id] = (sic, btype)

    desc = "This dictionary (defaultdict) maps <loc_id> to a (<sic_code>, <business_type>) pair. Values not in the dictionary are mapped to (0, 0)."

    desc_map = defaultdict(get_default_for_map, desc_map)
    qdump((desc_map, desc), "desc_map" + alt_str + ".pkl")
    
def make_data_pkl():
    desc_map, desc = qload("desc_map" + alt_str + ".pkl")
    records        = []
    #fnums         = [15007, 150]
    fnums          =  [150] + [1500 + i for i in range(10)] + [15000 + i for i in range(100)]

    
    for fnum in fnums:
        kwhs  = []
        temps = []

        finn  = data_loc + "Agentis/" + str(fnum) + ".csv"
        fin   = open(finn)
        fin.readline()#ignore header
        for l in fin:
            ind, time_stamp, kwh, v3, temp, date = (0, 0, 0, 0, 0, "0") #just to reset to be safe
            line                                 = map(string.strip, l.split(","))
            
            #if "NA" in line:
                #line = [x if x != "NA" else 0 for x in line ]
                #print "This line contains NA and will be skipped:", line
                
            if len(line) != 5 and len(line) != 6:
                print "This line, (in file", finn, ") has length", len(line), "and will be skipped:", line
                continue
            elif len(line) == 6:
                ind, time_stamp, kwh, v3, temp, date = tuple(line)
            elif len(line) == 5:
                ind, time_stamp, kwh, temp, date = tuple(line)
            
            #Strip out 2011:
            start_time = "01/01/2011 00:00:00"
            end_time   = "01/01/2012 00:00:00"

            #start_ts = int(time.mktime(datetime.strptime(start_time, "%m/%d/%Y %H:%M:%S").timetuple()))
            #end_ts = int(time.mktime(datetime.strptime(end_time, "%m/%d/%Y %H:%M:%S").timetuple()))
            start_ts   = datetime.strptime(start_time, "%m/%d/%Y %H:%M:%S")
            start_ts   = start_ts.replace(tzinfo = tz_used)
            end_ts     = datetime.strptime(end_time, "%m/%d/%Y %H:%M:%S")
            end_ts     = end_ts.replace(tzinfo = tz_used)
            ind        = int(string.strip(ind, '"'))
            #time_stamp = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            #time_stamp = float(time_stamp)
            time_stamp = datetime.fromtimestamp(float(time_stamp), utc_tz)
            
            if (not only_one_year or (time_stamp >= start_ts and time_stamp < end_ts)):
                if kwh == "NA" or float(kwh) == 0.0:
                    #print "kwh found to be NA"
                    pass
                else:

                    kwh = float(kwh)
                    kwhs.append((time_stamp, kwh))
                if temp == "NA":
                    #print "temperature found to be NA"
                    pass
                else:
                    temp = float(temp)
                    temps.append((time_stamp, temp))

        fsic, fbtype = desc_map[fnum]
        start_date   = datetime.strptime("1/1/2011 00:00:00", "%m/%d/%Y %H:%M:%S").replace(tzinfo = tz_used)
        

#        full_year_times = \
#            [(start_date + rdatetime.timedelta(hours = n)).astimezone(utc_tz) for n in range(8760)]
        full_year_times = \
            [(start_date + rdatetime.timedelta(hours = n)) for n in range(8760)]
        full_temps, temps_oriflag = fill_in(temps, full_year_times)
        full_kwhs, kwhs_oriflag   = fill_in(kwhs, full_year_times)

        temp_times, temp_vals = zip(*full_temps)
        kwh_times,  kwh_vals  = zip(*full_kwhs)
        #record = {"bid": fnum, "sic": fsic, "btype":fbtype, "temps":temps,  "kwhs": kwhs}
        record = {
            "bid"      : fnum,
            "sic"      : fsic,
            "btype"    : fbtype,
            "times"    : np.array(full_year_times),
            "kwhs"     : (np.array(kwh_vals), np.array(kwhs_oriflag)),
            "temps"    : (np.array(temp_vals), np.array(temps_oriflag))}
            
        records.append(record)
    print len(records), "records recorded."
    desc = "This is a list of Building Records."
    
    if only_one_year: foutn = "agentis_b_records_2011" + alt_str + ".pkl"
    else: foutn             = "agentis_b_records" + alt_str + ".pkl"

    qdump((records, desc), foutn)


if __name__ == "__main__":
    get_desc_map()
    make_data_pkl()
