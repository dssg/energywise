#We're going to look only at 2010, get 111 points, do some dimensionality reduction and plot.

from utils import data_loc, fig_loc, qload, qdump
import numpy as np
from datetime import datetime
import time
import matplotlib.pyplot as plt

import pickle
import pytz

utc_tz = pytz.utc
tz_used = pytz.timezone("US/Central")

def plot_b_rec(b):
     ''' Given a building record, this creats a six-figure plot and saves it as a jpg.'''
     bid = d["bid"]
     sic = d["sic"]
     btype = d["btype"]
     times = d["times"]
     kwhs = d["kwhs"]
     temps = d["temps"]

     fig = plt.figure(figsize = (9, 12))

     tmpsvk = fig.add_subplot(3, 2, 1)
     textfig = fig.add_subplot(3, 2, 2)
     tvt = fig.add_subplot(3, 2, 3)
     tvk = fig.add_subplot(3, 2, 4)
     avgday = fig.add_subplot(3, 2, 5)
     avgweek = fig.add_subplot(3, 2, 6)

     textfig.text(0.05, .95, "ID:\n   " + str(bid) + "\nSic:\n   " + str(sic) + "\n" + "Type:\n   " + str(btype), fontsize=14, ha='left', va='top')
     
     textfig.set_xticks([])
     textfig.set_yticks([])
     
     tvt.plot(times, temps)
     tvt.set_title("Temperature Over Time")
     tvt.set_xlabel("Time")
     tvt.set_ylabel("Temperature")
     
     tvk.plot(times, kwhs)
     tvk.set_title("Energy Usage Over Time")
     tvk.set_xlabel("Time")
     tvk.set_ylabel("kwhs")
     
     tmpsvk.scatter(temps, kwhs, alpha = 0.1)
     tmpsvk.set_title("Temperature vs Energy Usage")
     tmpsvk.set_xlabel("Temperature")
     tmpsvk.set_ylabel("kwh")
 

     avgday_temps = [[] for x in range(24)]
     avgday_kwhs = [[] for x in range(24)]

     avgweek_temps = [[] for x in range(7)]
     avgweek_kwhs = [[] for x in range(7)]
     
     for time, kwh, temp  in zip(times, kwhs, temps):
          hod = datetime.fromtimestamp(time, utc_tz).astimezone(tz_used).hour
          dow = datetime.fromtimestamp(time, utc_tz).astimezone(tz_used).weekday()
          if temp > 0: 
               avgday_temps[hod].append(temp)
               avgweek_temps[dow].append(temp)
          if kwh > 0: 
               avgday_kwhs[hod].append(kwh)
               avgweek_kwhs[dow].append(kwh)

     stdday_temps = [np.std(x) for x in avgday_temps]
     stdday_kwhs = [np.std(x) for x in avgday_kwhs]
     
     avgday_temps = [np.average(x) for x in avgday_temps]
     avgday_kwhs = [np.average(x) for x in avgday_kwhs]
     
     if False:
          avgday_temps -= np.min(avgday_temps)
          avgday_temps /= np.max(avgday_temps)
          avgday_kwhs -= np.min(avgday_kwhs)
          avgday_kwhs /= np.max(avgday_kwhs)
          
     stdweek_temps = [np.std(x) for x in avgweek_temps]
     stdweek_kwhs = [np.std(x) for x in avgweek_kwhs]

     avgweek_temps = [np.average(x) for x in avgweek_temps]
     avgweek_kwhs = [np.average(x) for x in avgweek_kwhs]
     
     if False:
          avgweek_temps -= np.min(avgweek_temps)
          avgweek_temps /= np.max(avgweek_temps)
          avgweek_kwhs -= np.min(avgweek_kwhs)
          avgweek_kwhs /= np.max(avgweek_kwhs)
     
     
     avgday.errorbar(range(24), avgday_temps, yerr = stdday_temps, label = "T")
     avgday.errorbar([0.25 + i for i in range(24)], avgday_kwhs, yerr=stdday_kwhs, label = "E")
     
     avgday.set_title("Average Day")
     avgday.set_yticks([])
     avgday.legend()
           

     avgweek.errorbar(range(7), avgweek_temps, yerr = stdweek_temps, label = "T")
     avgweek.errorbar([0.05 + x for x in range(7)], avgweek_kwhs, yerr=stdweek_kwhs, label = "E")
     avgweek.set_title("Average Week")
     avgweek.set_yticks([])
     avgweek.legend()
           
     plt.tight_layout()
     #plt.show()
     
     plt.savefig(fig_loc + "sixfig_" + str(bid) + "_2011.png")
     plt.clf()
     


if __name__ == "__main__":
     data, desc = qload("agentis_b_records_2011.pkl")
     print "Data desc:", desc
     print "Number of points:", len(data)
     print "vals for point 0:", len(data[0]["times"])
     for d in data:
          plot_b_rec(d)