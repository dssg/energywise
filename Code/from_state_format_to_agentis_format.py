from os import listdir
from    datetime import datetime
from    dateutil import tz
import  pytz
import time
tz_used = pytz.timezone("US/Central")
from utils import *
import sys

def fix_it(finn):
    print "Fixing", finn
    sys.stdout.flush()
    fin = open(data_loc + "State/" + finn)
    fin.next() #skip the first line of garbage
    fin.next() #skip the second line of garbage
    fin.next() #skip the third line of, you guessed it,  garbage

    fout = open(finn + "_new.csv", "w")
    fout.write('"","timestamp.utc","kwh","temperature","date.time"\n')
    i = 1
    for l in fin:
        line = l.split(",")
        if len(line) == 8:
            accno, meterno, date_time, date, the_time, val, kwh, newlinechar = line
        elif len(line) == 7:
            accno, meterno, date_time, date, the_time, val, kwh = line         

        else:
            print "ERROR"
        #dt = datetime.strptime(date_time, "%m/%d/%Y %H:%M").replace(tzinfo = tz_used)

        my_date_time = date.split(" ")[0] + " " + the_time
        dt = datetime.strptime(my_date_time, "%m/%d/%Y %H:%M").replace(tzinfo = tz_used)
        time_stamp = time.mktime(dt.timetuple())
        #calc new_date_time...
        new_date_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        to_write = '"' + str(i)  + '"'
        to_write += "," + str(time_stamp)
        to_write += "," + str(val)
        to_write += ",0.0"
        to_write += "," + new_date_time
        to_write += "\n"
        fout.write(to_write)
        i += 1 


if __name__ == "__main__":
    brecs, desc = qload("state_b_records_2011_updated.pkl")
    ag_rec, _ = qload("agentis_oneyear_22891_updated.pkl")
    
    temps, temps_oriflag = ag_rec["temps"]
    print "Number of elements:", len([x for x in temps if x])
    
    for brec in brecs:
        brec["temps"] = (temps, temps_oriflag)
        
    qdump((brecs, desc), "state_b_records_2011_with_temps.pkl")


    exit()
    finns = [x for x in listdir(data_loc + "State") if ".csv" in x and "new" not in x]

    for finn in finns:
        fix_it(finn)





