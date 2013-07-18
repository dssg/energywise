import sys
from utils import data_loc, fig_loc, qload, qdump, interp, clean
import numpy as np
from datetime import datetime
import time as itime
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import pickle
import pytz
import heapq
utc_tz  = pytz.utc
tz_used = pytz.timezone("US/Central")
from plotter_new import get_periods


def get_stats(d):
     bid                  = d["bid"]
     sic                  = d["sic"]
     btype                = d["btype"]
     times                = d["times"]
     kwhs, kwhs_oriflag   = d["kwhs"]
     temps, temps_oriflag = d["temps"]

     ori_kwhs              = kwhs[kwhs_oriflag]
     min_kwhs, min_time    = np.min(ori_kwhs), times[kwhs_oriflag][np.argmin(ori_kwhs)]
     max_kwhs, max_time    = np.max(ori_kwhs), times[kwhs_oriflag][np.argmax(ori_kwhs)]
     avg_kwhs    = np.average(ori_kwhs)
     total_kwhs  = np.sum(ori_kwhs)

     per_75_kwhs = np.percentile(ori_kwhs, 75)
     per_25_kwhs = np.percentile(ori_kwhs, 25)
     per_95_kwhs = np.percentile(ori_kwhs, 95)
     per_5_kwhs  = np.percentile(ori_kwhs, 5)
     
     month_starts = ["01/01/2011 00:00:00",\
                          "02/01/2011 00:00:00",\
                          "03/01/2011 00:00:00",\
                          "04/01/2011 00:00:00",\
                          "05/01/2011 00:00:00",\
                          "06/01/2011 00:00:00",\
                          "07/01/2011 00:00:00",\
                          "08/01/2011 00:00:00",\
                          "09/01/2011 00:00:00",\
                          "10/01/2011 00:00:00",\
                          "11/01/2011 00:00:00",\
                          "12/01/2011 00:00:00"]
          
     month_starts = [datetime.strptime(st, "%m/%d/%Y %H:%M:%S").replace(tzinfo = tz_used) for st in month_starts]
     month_breaks = [np.argmax(times == ms) for ms in month_starts]#indices
     zeroed_kwhs  = [k if flg else 0 for k, flg in zip(kwhs, kwhs_oriflag)]
     
     month_totals = [np.sum(zeroed_kwhs[s:e]) for s, e in zip(month_breaks, month_breaks[1:] + [-1])]
   
     report  = "-"*10 + "Building Report:" + "-"*10 \
         + "\nID:\n"        + "\t"*2       + str(bid).ljust(20)\
         + "\nSIC:\n"       + "\t"*2       + str(sic)\
         + "\nType:\n"      + "\t"*2       + str(btype)\
         + "\nEnergy Usage:" \
         + "\n\tAverage Hourly:\n"  + "\t"*2 +  str(np.round(avg_kwhs, 2)) + "kwh"\
         + ("\n\tMin:\n"            + "\t"*2      + str(np.round(min_kwhs, 2))).ljust(15)\
         + ("(" + min_time.strftime("%m/%d/%Y %H:%M")   + ")").rjust(20)\
         + ("\n\tMax:\n"            + "\t"*2      + str(np.round(max_kwhs, 2))).ljust(15)\
         + ("(" + max_time.strftime("%m/%d/%Y %H:%M")   + ")").rjust(20)\
         + "\n\tTotal:\n"           + "\t"*2      + str(np.round(total_kwhs/1000.0, 2)) + "gwhs"\
         + "\n\t75th percentile:\n" + "\t"*4      + str(np.round(per_75_kwhs, 2))\
         + "\n\t25th percentile:\n" + "\t"*4      + str(np.round(per_25_kwhs, 2))\
         + "\n\t95th percentile:\n" + "\t"*4      + str(np.round(per_95_kwhs, 2))\
         + "\n\t5th percentile:\n"  + "\t"*4      + str(np.round(per_5_kwhs,  2))

     report +="\nMonthly Totals:\n"
     for i, v in enumerate(month_totals):
          report += "\t"*2 + "Month " + str(i+1) + ": " + str(np.round(v/1000.0, 2)) + " gwhs\n"

     is_midnight     = (lambda x: x.hour == 0)
     days, new_times = get_periods(d, 24, is_midnight, "kwhs")
     avg_day         = np.average(days, axis=0)
     weirdness       = []
     totals          = []

     for day in days:
          total = np.sum(day)
          totals.append(total)
          dist = np.average(np.abs(day - avg_day))
          weirdness.append(dist)
     ind           = np.argmax(weirdness)
     weirdest_date = new_times[ind][0]
     weirdest_vals = days[ind]

     ind = np.argmax(totals)
     highest_day = new_times[ind][0]
     
     ind = np.argmin(totals)
     lowest_day = new_times[ind][0]

     report += "\nHighest day: " + highest_day.strftime("%m/%d/%Y")
     report += "\nLowest day: " + lowest_day.strftime("%m/%d/%Y")
     report += "\nStrangest day: " + weirdest_date.strftime("%m/%d/%Y")
     #plt.plot(weirdest_vals, label = weirdest_date.strftime("%m/%d/%Y"))
     #plt.plot(avg_day,       label = "Average day")
     #plt.legend()
     #plt.show()

     is_sunday_start  = (lambda x: x.weekday() == 6 and x.hour == 0)
     weeks, new_times = get_periods(d, 168, is_sunday_start, "kwhs")
     avg_week         = np.average(weeks, axis=0)
     weirdness        = []
     for week in weeks:
          dist = np.average(np.abs(week - avg_week))
          weirdness.append(dist)
     inds  = np.argsort(weirdness)[-5:][::-1]

     report += "\nStrangest weeks:\n"
     for ind in inds:
          weirdest_date_start = new_times[ind][0]
          weirdest_date_end   = new_times[ind][-1]
          weirdest_vals       = weeks[ind]
          week_as_string      = weirdest_date_start.strftime("%m/%d/%Y") + "--" +  weirdest_date_end.strftime("%m/%d/%Y")
          report             += "\t" + week_as_string + "\n"

     report += "\nPeaks:\n"
     inds  = np.argsort(ori_kwhs)[-5:][::-1]
     for ind in inds:
          highest_date = (times[kwhs_oriflag])[ind]
          highest_val = ori_kwhs[ind]
          report += "\t" + highest_date.strftime("%m/%d/%Y %H:%M:%S") + " -> " + str(highest_val) + "kwh\n"
     return report


if __name__ == "__main__":
    data, desc = qload("agentis_b_records_2011_updated_small.pkl")
    #data, desc = qload("agentis_b_records_2011_updated.pkl")
    sys.stdout.flush()
    #data = [data[-1]]
    print "Data desc:", desc
    print "Number of points:", len(data)
    print "vals for point 0:", len(data[0]["times"])
    print "\n"
    for ind, d in enumerate(data):
        print get_stats(d)
        sys.stdout.flush()
