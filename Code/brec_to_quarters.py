from utils import *
from copy import deepcopy
import datetime
import pytz
tz_used = pytz.timezone("US/Central")


def break_into_quarters(b):
    newbs = []
    print b.keys()
 
    for i in range(len(quarter_breaks) - 1):
        newb = deepcopy(b)
        times = b["times"]
        left = np.argmax(times == quarter_breaks[i])
        right = np.argmax(times == quarter_breaks[i+1])
        newb["times"]  = b["times"][left:right]
        newb["kwhs"]   = (b["kwhs"][0][left:right],  b["kwhs"][1][left:right])
        newb["temps"]  = (b["temps"][0][left:right], b["temps"][1][left:right])
        newb["bid"]    = str(b["bid"]) + "q" + str(i+1)
        newbs.append(newb)
    return newbs

if __name__ == "__main__":
    #March 31
    q1 = datetime.datetime(the_year, 3, 31, 23, 0, tzinfo = tz_used)
    #June 30
    q2 = datetime.datetime(the_year, 6, 30, 23, 0, tzinfo = tz_used)
    #Sept 30
    q3 = datetime.datetime(the_year, 9, 30, 23, 0, tzinfo = tz_used)
    #Dec 31
    q4 = datetime.datetime(the_year, 12, 31, 23, 0, tzinfo = tz_used)
    #q4 = datetime.datetime(the_year, 12, 30, 23, 0, tzinfo = tz_used)
    
    start = datetime.datetime(the_year, 1, 1, 0, 0, tzinfo = tz_used)
    quarter_breaks = [start, q1, q2, q3, q4]#date_time_objects
    quarter_break_inds = [0] #indices, start at start of year

    finn = "state_b_records_" + str(the_year) + "_with_temps_cleaned.pkl"
    
    brecs, desc = qload(finn)
    newbs = []
    for b in brecs:
        newbs += break_into_quarters(b)
        
    qdump((newbs, desc + "(Broken into quarters.)"), "state_b_records_" + str(the_year) + "_quarters.pkl")

    
