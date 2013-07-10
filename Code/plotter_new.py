import  sys
from    utils import *
import  numpy as np
from    datetime import datetime
import  time as itime
import  matplotlib.pyplot as plt
from    matplotlib.colors import LogNorm
import  cPickle as pickle
import  pytz
import  heapq
utc_tz  = pytz.utc
tz_used = pytz.timezone("US/Central")

def get_periods(d, nobs, first_pred, which = "kwhs", skip_fun = (lambda x: False)):
    times                  = d["times"]
    series, series_oriflag = d[which]
    
    additional_mask = np.array([skip_fun(t) for t in times])
    new_mask = np.logical_or((~series_oriflag), additional_mask)
    masked_series = np.ma.array(series, mask = new_mask)
    
    first = 0
    for ind, t in enumerate(times):
        if first_pred(t):
            first = ind
            break
    pers      = np.ma.concatenate([masked_series[first:], masked_series[:first]])
    new_times = np.ma.concatenate([times[first:], times[:first]])
    
    residue = len(pers) % nobs
    if residue != 0:
        pers      = pers[:-residue]#trim off extra
        new_times = new_times[:-residue]

    pers      = pers.reshape(-1, nobs)
    new_times = new_times.reshape(-1, nobs)
    return pers, new_times

def make_text_fig(d, textfig):
    bid                  = d["bid"]
    sic                  = d["sic"]
    btype                = d["btype"]
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]
    
    toPrint =  "ID:\n   "   + str(bid)\
        + "\nSic:\n   "     + str(sic)\
        + "\nType:\n   "    + str(btype)\
        + "\nAverage Hourly Energy Usage:\n    " + str(np.round(np.average(kwhs), 2)) + "kw"\
        + "\nMin:\n    "    + str(np.round(np.min(kwhs), 2))\
        + "\nMax:\n    "    + str(np.round(np.max(kwhs), 2))\
        + "\nTotal:\n     " + str(np.round(np.sum(kwhs)/1000.0, 2)) + "gwh"
    textfig.text(0.05, .95,toPrint , fontsize=12, ha='left', va='top')
    
    textfig.set_xticks([])
    textfig.set_yticks([])
    
def make_temp_vs_time_fig(d, tvt):
    bid                  = d["bid"]
    sic                  = d["sic"]
    btype                = d["btype"]
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]
    
    tvt.plot(   times[temps_oriflag] , temps[temps_oriflag] , c = "blue")
    tvt.scatter(times[~temps_oriflag], temps[~temps_oriflag], lw = 0,  c = "red")

    tvt.set_title("Temperature Over Time")
    tvt.set_ylabel("Temperature")
    
    labels = tvt.get_xticklabels() 
    for label in labels: 
        label.set_rotation(30) 
        

def make_kwhs_vs_time_fig(d, tvk):
    bid                  = d["bid"]
    sic                  = d["sic"]
    btype                = d["btype"]
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]

    tvk.plot(times[kwhs_oriflag], kwhs[kwhs_oriflag], c = "blue", label = "Energy Usage")
    tvk.scatter(times[~kwhs_oriflag], kwhs[~kwhs_oriflag], c = "red", lw = 0, label = "Imputed Values")
    ori_kwhs    = kwhs[kwhs_oriflag]
    per_95_kwhs = np.percentile(ori_kwhs, 95)
    per_5_kwhs  = np.percentile(ori_kwhs, 5)
    tvk.axhline(y = per_95_kwhs, c = "red", ls = "dashed", label = "95th Percentile")
    tvk.axhline(y = per_5_kwhs,  c = "black", ls = "dashed", label = "5th Percentile")
    tvk.set_title("Energy Usage Over Time")
    tvk.legend()
    tvk.set_ylabel("kwhs")
    labels = tvk.get_xticklabels() 
    for label in labels: 
        label.set_rotation(30) 

def make_freqs_fig(d, freqs):
    bid                  = d["bid"]
    sic                  = d["sic"]
    btype                = d["btype"]
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]

    start_time  = "01/01/2011 00:00:00"
    end_time    = "01/01/2012 00:00:00"
    start_ts    = int(itime.mktime(datetime.strptime(start_time, "%m/%d/%Y %H:%M:%S").timetuple()))
    end_ts      = int(itime.mktime(datetime.strptime(end_time, "%m/%d/%Y %H:%M:%S").timetuple()))
    
    all_times = range(start_ts, end_ts, 3600)
    num_times = len(all_times)
    
    a     = np.fft.fft(kwhs)
    half  = int(num_times + 1)/2
    a     = a[0:half +1]
    a[0]  = 0 #drop constant part of signal
    reals = [x.real for x in a]
    imags = [x.imag for x in a]
    freqs.set_xlabel("Period (h)")
    freqs.set_ylabel("Magnitude")
    freqs.plot(reals, label = "Real", alpha = 0.9)
    freqs.plot(imags, label = "Imaginary", alpha = 0.8)
    
    highlighted_periods =  np.array([3, 6, 12, 24, 168])
    highlighted_freqs   = float(num_times) / highlighted_periods
    highlighted_labels  = [str(x) for x in highlighted_periods]
    freqs.set_xticks(highlighted_freqs)          
    freqs.set_xticklabels(highlighted_labels)
    
    freqs.legend()
    freqs.set_title("Energy usage over time in the frequency domain")
    labels = freqs.get_xticklabels() 
    for label in labels: 
        label.set_rotation(30) 

def make_temp_vs_kwh_fig(d, tmpsvk):
    bid                  = d["bid"]
    sic                  = d["sic"]
    btype                = d["btype"]
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]

    both_ori = np.logical_and(temps_oriflag, kwhs_oriflag)
    tmpsvk.hist2d(temps[both_ori], kwhs[both_ori], bins = 50, norm = LogNorm())
    
    tmpsvk.set_title("Temperature vs Energy Usage")
    tmpsvk.set_xlabel("Temperature")
    tmpsvk.set_ylabel("kwh")
    tmpsvk.grid(True)

    
def make_avg_day_fig(d, avgday):
    is_midnight     = (lambda x: x.hour == 0)
    days, new_times = get_periods(d, 24, is_midnight, "kwhs")

    skip_weekdays   = (lambda x: x.weekday() < 5)
    weekends, _     = get_periods(d, 24, is_midnight, "kwhs", skip_weekdays)

    skip_weekend    = (lambda x: x.weekday() >= 5)
    weekdays, _     = get_periods(d, 24, is_midnight, "kwhs", skip_weekend)

    avg_weekend     = np.ma.average(weekends, axis = 0)
    avg_weekday     = np.ma.average(weekdays, axis = 0)
    avg_day         = np.ma.average(days, axis = 0)
 
    std_weekend     = np.ma.std(weekends, axis = 0)
    std_weekday     = np.ma.std(weekdays, axis = 0)
    std_day         = np.ma.std(days, axis = 0)

    avgday.errorbar(np.arange(24), avg_weekend, yerr =std_weekend, label = "Weekend")
    avgday.errorbar(np.arange(24), avg_weekday, yerr =std_weekday, label = "Weekday")
    avgday.errorbar(np.arange(24), avg_day,     yerr =std_day,     label = "Day")

    avgday.set_title("Average Day")
    avgday.set_ylabel("Temperature (F) / Energy Usage (kwh)")
    avgday.set_xlim(-0.5, 24.5)
    avgday.set_xticks(range(0, 24, 4))
    avgday.grid(True)
    avgday.legend()

def make_avg_week_fig(d, avgweek):
    is_sunday_start  = (lambda x: x.weekday() == 6 and x.hour == 0)
    weeks, new_times = get_periods(d, 168, is_sunday_start, "kwhs")

    avg_week  = np.ma.average(weeks, axis = 0)
    std_week  = np.ma.std(weeks, axis = 0)

    avgweek.errorbar(np.arange(168), avg_week, yerr =std_week, label = "Week", errorevery = 6)

    avgweek.set_title("Average Week")
    avgweek.set_ylabel("Temperature (F) / Energy Usage (kwh)")
    avgweek.set_xlim(-0.5, 24.5)
    avgweek.set_xticks(range(0, 169, 24))
    avgweek.set_xticklabels(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
    labels = avgweek.get_xticklabels() 
    for label in labels: 
        label.set_rotation(30) 

    avgweek.grid(True)
    avgweek.legend()


def plot_it(d):
    bid = d["bid"]
    fig = plt.figure(figsize = (20, 20))
    
    nrows    = 4
    ncols    = 3
    tmpsvk   = fig.add_subplot(nrows, ncols, 3)
    textfig  = fig.add_subplot(nrows, ncols, 2)
    tvt      = fig.add_subplot(nrows, 1, 4)
    tvk      = fig.add_subplot(nrows, 1, 3)
    avgday   = fig.add_subplot(nrows, 2, 3)
    avgweek  = fig.add_subplot(nrows, 2, 4)
    freqs    = fig.add_subplot(nrows, ncols, 1)
    
    make_text_fig(d, textfig)
    make_temp_vs_time_fig(d, tvt)
    make_kwhs_vs_time_fig(d, tvk)
    make_freqs_fig(d, freqs)
    make_temp_vs_kwh_fig(d, tmpsvk)
    make_avg_day_fig(d, avgday)
    make_avg_week_fig(d, avgweek)
    plt.subplots_adjust(hspace = .35)
    plt.savefig(fig_loc + "sixfig_" + str(bid) + "_2011.png")
    plt.clf()
    plt.close()
    
    
if __name__ == "__main__":
    #data, desc = qload("agentis_b_records_2011_updated_small.pkl")
    data, desc = qload("agentis_b_records_2011_updated.pkl")
    sys.stdout.flush()
    #data = [data[-1]]
    print "Data desc:", desc
    print "Number of points:", len(data)
    print "vals for point 0:", len(data[0]["times"])
    print "\n"
    for ind, d in enumerate(data):
        plot_it(d)
        bid = d["bid"]
        print str(ind), ": plotted something..."
        sys.stdout.flush()
        
        
