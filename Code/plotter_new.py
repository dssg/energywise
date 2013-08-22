from    utils import *
import  report_card
import  matplotlib
#matplotlib.use('Agg')
from    matplotlib.backends.backend_pdf import PdfPages
import  ephem
import  copy
import  math
import  sys

import  numpy as np
from    datetime import datetime
import  time as itime
import  matplotlib.pyplot as plt
from    matplotlib.colors import LogNorm
import  cPickle as pickle
import  pytz
import  heapq
from    sklearn.cluster import KMeans
from    sklearn import mixture
from    holiday import yfhol
import  warnings

utc_tz  = pytz.utc
tz_used = pytz.timezone("US/Central")
#tz_used = pytz.timezone("America/Chicago")


def getSun(stateID, currentTime, city = None):
    """Get the position of the sun at a given time and location.
    
    Parameters:
    stateID  -- A string abbreviation of the state name, ie "IL","AZ",etc..
    currentTime -- Local time with tzinfo = state time zone.
    city (optional) -- The City  (defaults to state capital if missing or not found in database).
    
    Returns:
    sin(altitude) (representing how much sunlight hits an area)
    """
        #Note:  altitude,azimuth are given in radians
    o = ephem.Observer()    
    stateID.capitalize()
    dateStamp=currentTime.astimezone(pytz.utc)
    if city is None:
        city=states[stateID]['capital']        
    else:
        try:
            city=states[stateID][city].capitalize()
        except:
            city=states[stateID]['capital']             
    the_lat = states[stateID][city][0]
    the_long = states[stateID][city][1]
    #IF YOU CONVERT TO FLOAT HERE, EVERYTHING GOES BOOM (but quietly)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        o.lat    = the_lat 
        o.long   = the_long
        o.date   = dateStamp
        sun = ephem.Sun(o)
    alt=sun.alt

    return math.sin(alt)

def get_periods(di, nobs, first_pred, which = "kwhs", skip_fun = (lambda x: False), wrap_around = False):
    """Get a collection of periods (e.g., weeks) from a building record.

    Parameters:
    di -- The building record.
    nobs -- The number (int) of observations for a single period (e.g., 168 for weeks).
    first_pred -- A function which, given a datetime object, returns True if it is the start of the period.
                  For example, first_pred returns True only when the argument is Sunday at Midnight.
    which -- A string representing which time series in the building record to use (defaults to "kwhs")
    skip_fun -- A function which takes a datetime object and returns True if that time should be skipped.
                For example, skip_fun may return True on weekends, to obtain only work weeks.
    wrap_around -- If True, the beginning part of the time series is placed at the end.
                   For example, if we're starting periods on Monday, but the first day in the time series 
                   is Thursday, then the first part (from Thrusday to Monday) will be moved to the end.

    Returns (pers, new_times):
         pers -- The values (e.g., kwhs) of the periods.
         new_times -- The times (datetime objects) associated with the values.
    """
    d = copy.deepcopy(di) #used so that we don't change di at all
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
    if wrap_around:
        pers      = np.ma.concatenate([masked_series[first:], masked_series[:first]])
        new_times = np.ma.concatenate([times[first:], times[:first]])
    else:
        pers      = masked_series[first:]
        new_times = times[first:]

    residue = len(pers) % nobs
    if residue != 0:
        pers      = pers[:-residue]#trim off extra
        new_times = new_times[:-residue]

    pers      = pers.reshape(-1, nobs)
    new_times = new_times.reshape(-1, nobs)
    return pers, new_times


def make_text_fig(d, textfig):
    """Show the static information from the building record in a given axis.

    Parameters:
    d -- The building record.
    textfig -- The axis to hold the figure.
    """
    bid                  = d["bid"]
    naics                = d["naics"]
    btype                = d["btype"]
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]
    naics_map, desc = qload("NAICS.pkl")
    if naics in naics_map:
        naics_str = naics_map[naics]
        naics_str = " (" + naics_str.lstrip().rstrip() + ")"
    else:
        naics_str = ""
    if len(naics_str) > 20:
        naics_str = naics_str.replace("and ", "and\n") #TODO: Figure out better way
    toPrint =  "ID:\n   "   + str(bid)\
        + "\nNaics:\n   "     + str(naics) + "\n    " + naics_str\
        + "\nType:\n   "    + str(btype)

    toPrint += "\n"
    rep = report_card.get_report(d)
    width = 50
    for k in rep.keys():
        toPrint += k + ":\n" + ("%.2f" % rep[k]).rjust(width) + "\n"

    textfig.text(0.05, .95, toPrint, fontsize=10, ha='left', va='top')
    textfig.set_xticks([])
    textfig.set_yticks([])

def make_prison_text_fig(d, textfig):
    """Show the static information from the building record in a given axis.
    Note: This function relies on the building record corresponding to a prison in our database.

    Parameters:
    d -- The building record.
    textfig -- The axis to hold the figure.
    """
    bid                  = d["bid"]
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]
    
    feature_map, desc = qload("prison_features_map.pkl")
    if isinstance(bid, str) and "q" in bid:
        features = feature_map[int(bid[:-2])]
    else:
        features = feature_map[bid]
    toPrint =  features["name"] + " \n        (" + features["acronym"] + ")"\
        + "\nCity:\n    " + features["city"]\
        + "\nID:\n   "   + str(bid)\
        + "\nNumber of Buildings:\n    " + features["nrBuildings"]\
        + "\nX-houses:\n    " + features["X_design_housing_units"]\
        + "\nT-houses:\n    " + features["T_type_housing_units"]\
        + "\nHealthcare units:\n    " + features["health_care_units"]\
        + "\nBuilding size:\n    " + features["building_size"]
    for i in range(1, 7):
        iname = "industry_%d"%i
        industry = features[iname]
        if len(industry) > 15:
            industry = industry.replace(" and", "\nand")
        if industry != "":
            toPrint += "\nIndustry:\n    " + industry
    
    toPrint +="\nTotal land:\n    " + features["total_land"] + "acres"\
        + "\nAverage Hourly Energy Usage:\n    " + str(np.round(np.average(kwhs), 2)) + "kw"\
        + "\nMin:\n    "    + str(np.round(np.min(kwhs), 2))\
        + "\nMax:\n    "    + str(np.round(np.max(kwhs), 2))\
        + "\nTotal:\n     " + str(np.round(np.sum(kwhs)/1000.0, 2)) + "gwh"

    toPrint += "\n"    
    width = 50

    textfig.text(0.05, .95, toPrint, fontsize=10, ha='left', va='top')
    textfig.set_xticks([])
    textfig.set_yticks([])
    

def make_temp_vs_time_fig(d, tvt):
    """Show temperature as a function of time in a given axis.

    Parameters:
    d -- The building record.
    tvt -- The axis to hold the figure.
    """
    times                = d["times"]
    temps, temps_oriflag = d["temps"]
    
    tvt.plot(   times[temps_oriflag] , temps[temps_oriflag] , c = "blue")
    tvt.scatter(times[~temps_oriflag], temps[~temps_oriflag], edgecolors = "none",  c = "red")
    tvt.scatter(times[~temps_oriflag], [0 for x in temps[~temps_oriflag]], edgecolors = "none", c = "red", s = 1)

    tvt.set_title("Temperature Over Time")
    tvt.set_ylabel("Temperature")
    
    labels = tvt.get_xticklabels() 
    for label in labels: 
        label.set_rotation(30) 
        

def make_kwhs_vs_time_fig(d, tvk):
    """Show kwhs as a function of time in a given axis.

    Parameters:
    d -- The building record.
    tvk -- The axis to hold the figure.
    """
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]

    tvk.plot(times[kwhs_oriflag], kwhs[kwhs_oriflag], c = "blue", label = "Energy Usage")
    tvk.scatter(times[~kwhs_oriflag], kwhs[~kwhs_oriflag], c = "red", edgecolors = "none", label = "Imputed Values")
    tvk.scatter(times[~kwhs_oriflag], [0 for x in kwhs[~kwhs_oriflag]], c = "red", edgecolors = "none",  s = 1)
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
    """Show kwhs in the frequency domain (via the DFT).
       Note: This function requires data from (all of) the_year.

    Parameters:
    d -- The building record.
    freqs -- The axis to hold the figure.
    """
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]

    start_time  = "01/01/%d 00:00:00" %the_year
    end_time    = "01/01/%d 00:00:00" %(the_year + 1)
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
    freqs.set_title("Energy usage in the frequency domain")
    labels = freqs.get_xticklabels() 
    for label in labels: 
        label.set_rotation(30) 


def make_temp_vs_kwh_fig(d, tmpsvk, agg_to_day = False):
    """Show a 2d-histogram of temperatures vs kwhs in a given axis.
    
    Parameters:
    d -- The building record.
    tmpsvk -- The axis to hold the figure.
    """
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]

    both_ori = np.logical_and(temps_oriflag, kwhs_oriflag)
    if agg_to_day:
        #is_sunday_start = (lambda x: x.weekday() == 6 and x.hour == 0)
        is_midnight      = (lambda x: x.hour == 0)
        days, new_times  = get_periods(d, 24, is_midnight)
        day_avgs        = np.ma.average(days, axis = 1)
        temps, new_times = get_periods(d, 24, is_midnight, which = "temps")
        temp_avgs = np.ma.average(temps, axis = 1)
        #tmpsvk.hist2d(temp_avgs, day_totals, bins = 50, norm = LogNorm())
        tmpsvk.scatter(temp_avgs, day_avgs, alpha = .4)
        tmpsvk.set_title("Energy Usage vs Temperature (agg days)")
    else:
        tmpsvk.hist2d(temps[both_ori], kwhs[both_ori], bins = 50, norm = LogNorm())
        tmpsvk.set_title("Energy Usage vs Temperature")
        #tmpsvk.set_ylim(600, 1400)
    tmpsvk.set_xlabel("Temperature")
    tmpsvk.set_ylabel("kwh")
    tmpsvk.grid(True)

    
def make_avg_day_fig(d, avgday):
    """Show the average day in a given axis.
       Note: imputed values are ignored.

    Parameters:
    d -- The building record.
    avgday -- The axis to hold the figure.
    """

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

    avgday.errorbar([0.25 + x for x in np.arange(24)][:-1], avg_day[:-1],    yerr =std_day[:-1],    label = "Day",     alpha = .3, fmt = None,  ecolor = "blue")
    avgday.errorbar([-0.25 + x for x in np.arange(24)][1:], avg_weekend[1:], yerr =std_weekend[1:], label = "Weekend", alpha = .3, fmt = None,  ecolor = "red")
    avgday.errorbar(np.arange(24),                          avg_weekday,     yerr =std_weekday,     label = "Weekday", alpha = .3, fmt = None,  ecolor = "green")

    avgday.plot(np.arange(24), avg_day,     label = "Day",     c = "blue")
    avgday.plot(np.arange(24), avg_weekend, label = "Weekend", c = "red")
    avgday.plot(np.arange(24), avg_weekday, label = "Weekday", c = "green")


    avgday.set_title("Average Day")
    avgday.set_ylabel("Energy Usage (kwh)")
    avgday.set_xlim(-0.5, 24.5)
    avgday.set_xticks(range(0, 24, 4))
    avgday.grid(True)
    avgday.legend()

def make_avg_week_fig(d, avgweek):
    """Show the average week in a given axis.
       Note: imputed values are ignored.

    Parameters:
    d -- The building record.
    avgweek -- The axis to hold the figure.
    """

    is_sunday_start  = (lambda x: x.weekday() == 6 and x.hour == 0)
    weeks, new_times = get_periods(d, 168, is_sunday_start, "kwhs")

    avg_week  = np.ma.average(weeks, axis = 0)
    std_week  = np.ma.std(weeks, axis = 0)

    avgweek.plot(np.arange(168), avg_week, label = "Energy Usage", c = "purple")
    avgweek.errorbar(np.arange(168), avg_week, yerr = std_week, label = "Energy Usage", errorevery = 6, ecolor = "purple", fmt = None, alpha = .3)

    avgweek.set_title("Average Week")
    avgweek.set_ylabel("Energy Usage (kwh)")
    avgweek.set_xlim(-0.5, 24.5)
    avgweek.set_xticks(range(0, 169, 24))
    avgweek.set_xticklabels(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
    labels = avgweek.get_xticklabels() 
    for label in labels: 
        label.set_rotation(30) 

    avgweek.grid(True)
    avgweek.legend()

def make_hist_fig(d, hist):
    """Show a histogram of hourly energy usage.
       Note: imputed values are ignored.

    Parameters:
    d -- The building record.
    hist -- The axis to hold the figure.
    """
    kwhs, kwhs_oriflag   = d["kwhs"]
    
    hist.hist(kwhs[kwhs_oriflag], bins = 50)
    hist.set_title("Histogram of Energy Usage")
    hist.set_xlabel("kwhs")
    hist.set_ylabel("Number of hours")

def gen_peaks(d, num_peaks = 3):
    """A generatore that yields the index of the highest peaks.
       
    Parameters:
    d -- The building record.
    num_peaks -- The number of peaks to be yielded.
    """
    kwhs, kwhs_oriflag   = d["kwhs"]
    
    inds = np.argsort(kwhs)[-num_peaks:]
    for ind in inds:
        yield ind


def make_peak_fig(d, ax, ind):
    """Show the 24-hour period around the time at index ind.

    Parameters:
    d -- The building record.
    ax -- The axis to hold the figure.
    ind -- The index of the time to display.
    """
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
 
    highest_date = times[ind]
    highest_val  = kwhs[ind]
    leftmost  = max(0, ind-12)
    rightmost = min(len(kwhs), ind+12)
    
    make_interval_plot(d, ax, leftmost, rightmost)

def make_kwh_vs_sun_fig(d, ax, agg_days = False):
    """Show a 2d-histogram of kwhs vs the position of the sun in a given axis.
       Note: Imputed values are ignored.

    Parameters:
    d -- The building record.
    ax -- The axis to hold the figure.
    """
    bid                  = d["bid"]
    naics                = d["naics"]
    btype                = d["btype"]
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]

    sun_pos = np.array([max(-100, getSun("IL", t)) for t in times])
    if agg_days:
        is_midnight = (lambda x: x.hour == 0)
        d["sun_pos"] = (sun_pos, np.array([True for x in sun_pos]))
        days, new_times = get_periods(d, 24, is_midnight)
        suns, new_times = get_periods(d, 24, is_midnight, which = "sun_pos")
        day_avgs = np.ma.average(days, axis = 1)
        sun_avgs = np.ma.average(suns, axis = 1)
        ax.scatter(sun_avgs, day_avgs, alpha = .4)
        ax.set_xlim(np.min(sun_avgs), np.max(sun_avgs))
        ax.set_title("Energy Usage vs Sunlight (agg days)")        
    else:
        ax.hist2d(sun_pos[kwhs_oriflag], kwhs[kwhs_oriflag], bins = 50, norm = LogNorm())
        ax.set_title("Energy Usage vs Sunlight")        
        ax.set_xlim(np.min(sun_pos[kwhs_oriflag]), np.max(sun_pos[kwhs_oriflag]))
        
    left, right = ax.get_xlim()
    ax.set_xticks([left/2., 0, right/2.])
    ax.set_xticklabels(["Below Horizon", "Sun rise/set", "Above Horizon"])
    ax.set_xlabel("Sunlight")
    ax.set_ylabel("kwh")
    ax.grid(True)


def make_monthly_usage_fig(d, ax):
    """Show a barchart with the totaly electricy usage by month.
    
    Parameters:
    d -- The building record.
    ax-- The axis to hold the figure.
    """
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]

    month_breaks = [ind for ind, t in enumerate(times) if t.day == 1 and t.hour == 0]

    zeroed_kwhs  = [k if flg else 0 for k, flg in zip(kwhs, kwhs_oriflag)] 
    month_totals = [np.sum(zeroed_kwhs[s:e]) for s, e in zip(month_breaks, month_breaks[1:] + [-1])]
    
    ax.bar([times[i] for i in month_breaks], month_totals, width = 10)
    labels = ax.get_xticklabels() 
    for label in labels: 
        label.set_rotation(30) 
    ax.set_title("Monthly Energy Usage")
    ax.set_ylabel("kwhs")
    ax.grid(True)

def make_boxplot_all_days_fig(d, ax):
    times = d['times']
    hr_start = 8
    hr_stop = 16
    kwhs, kwhs_oriflag = d["kwhs"]
    in_schedule = (lambda x: hr_start <= x.hour <= hr_stop)
    out_schedule = (lambda x: x.hour < hr_start or x.hour > hr_stop)
    
    out_flag = [out_schedule(t) for t in times]
    in_flag  = [in_schedule(t) for t in times]

    kwhs_in  = kwhs[np.logical_and(kwhs_oriflag, in_flag)]
    kwhs_out = kwhs[np.logical_and(kwhs_oriflag, out_flag)]

    ax.set_ylabel("Energy Usage (kwh)")
   
    labels = ['8am - 4pm', '4pm - 8am']
    ax.set_xticklabels(labels)
    ax.boxplot([kwhs_in, kwhs_out])
    ax.yaxis.grid(True)
    ax.set_title("All days")

def make_boxplot_weekday_vs_end_fig(d, ax):
    times = d['times']
    hr_start = 6
    hr_stop = 17
    kwhs, kwhs_oriflag = d["kwhs"]
    in_schedule = (lambda x: hr_start <= x.hour <= hr_stop)
    out_schedule = (lambda x: x.hour < hr_start or x.hour > hr_stop)
    is_weekday = (lambda x: x.weekday() < 5)
    is_weekend = (lambda x: x.weekday() >= 5)

    out_flag = [out_schedule(t) for t in times]
    in_flag  = [in_schedule(t) for t in times]
    weekday_flag = [is_weekday(t) for t in times]
    weekend_flag = [is_weekend(t) for t in times]
    
    weekday_kwhs_in  = kwhs[np.logical_and(kwhs_oriflag, np.logical_and(in_flag, weekday_flag))]
    weekday_kwhs_out = kwhs[np.logical_and(kwhs_oriflag, np.logical_and(out_flag, weekday_flag))]

    weekend_kwhs_in  = kwhs[np.logical_and(kwhs_oriflag, np.logical_and(in_flag, weekend_flag))]
    weekend_kwhs_out = kwhs[np.logical_and(kwhs_oriflag, np.logical_and(out_flag, weekend_flag))]

    ax.set_ylabel("Energy Usage (kwh)")
    ax.yaxis.grid(True)
    labels = ['Weekday 8am - 4pm', 'Weekend 8am - 4pm', 'Weekday 4pm - 8am', 'Weekend 4pm - 8am']
    ax.set_xticklabels(labels)
    ax.boxplot([weekday_kwhs_in, weekend_kwhs_in, weekday_kwhs_out, weekend_kwhs_out], positions = [1, 2, 4, 5])
    ax.set_title("Weekday vs Weekend")

def gen_holidays(d):
    """A generator that yields federal holidays in the timeframe of the building record d (in chronological order)."""
    times = d["times"]
    holidays = yfhol(the_year)
    holidays = holidays.items()
    holinames, holidates = zip(*holidays)
    mymap = dict(zip(holidates, holinames))

    is_midnight     = (lambda x: x.hour == 0)
    days, new_times = get_periods(d, 24, is_midnight, "kwhs")
    for t in new_times:
        date = t[0].date()
        if date in holidates:
            left_side  = np.argmax(times == t[0])
            right_side = np.argmax(times == t[-1])
            
            yield (left_side, right_side), mymap[date]

def gen_strange_pers(d, num_pers = 3, period = "day"):
    """A generator which yields the strangest period (day or week).

    Parameters:
    d -- The building record.
    num_pers -- The number of periods to be yieled (one at a time).
    period -- A string, either "day" or "week".
    """
    kwhs, kwhs_oriflag = d["kwhs"]
    times = d["times"]
    if period == "day":
        first_pred = (lambda x: x.hour == 0)
    elif period == "week":
        first_pred = (lambda x: x.weekday() == 0 and x.hour == 0)
    else:
        print "period must be 'day' or 'week'."
        return
    num_per_period = 24 if period == "day" else 168
    pers, new_times = get_periods(d, num_per_period, first_pred, "kwhs")
    temp_pers, _ = get_periods(d, num_per_period, first_pred, which = "temps")

    avg_per         = np.average(pers, axis=0)
    weirdness       = []
    totals          = []
    
    standardize = True
    if standardize:
        avg_per = avg_per - np.min(avg_per)
        avg_per = avg_per / np.max(avg_per)

    for per in pers:
        if standardize:
            per = per - np.min(per)
            per = per / np.max(per)

        dist = np.average(np.abs(per - avg_per))        
        weirdness.append(dist)
    inds = np.argsort(weirdness)[-num_pers:][::-1]
    for ind in inds:
        left_side  = np.argmax(times == new_times[ind][0])#hackish, but oh well
        right_side = np.argmax(times == new_times[ind][-1])#hackish, but oh well
 
        yield left_side, right_side

def make_strange_per_fig(d, ax, per, c = 'blue'):
    """Creates a plot of the period yieled from get_strange_pers.

    Parameters:
    d -- The building record.
    ax -- The axis to hold the figure.
    per -- The period yieled from get_strange_pers.
    """
    start, end = per
    make_interval_plot(d, ax, start, end, c = c)
    ax.set_title(d["times"][start].strftime("%m/%d/%Y %H:%M:%S") + "--" + d["times"][end].strftime("%m/%d/%Y %H:%M:%S"))

def make_extreme_days_figs(d, axhigh, axlow):
    """Show the extreme high and extreme low days (in terms of electricity usage).
    
    Parameters:
    d -- The building recorod.
    axhigh -- The axis to hold the extreme-high figure.
    axlow -- The axis to hold the extreme-low figure.
    """
    is_midnight     = (lambda x: x.hour == 0)
    days, new_times = get_periods(d, 24, is_midnight, "kwhs")
    avg_day         = np.average(days, axis=0)
    weirdness       = []
    totals          = []
    times           = d["times"]

    for day in days:
        total = np.sum(day)
        totals.append(total)
        dist = np.average(np.abs(day - avg_day))
        weirdness.append(dist)
    ind = np.argmax(totals)
    highest_day = new_times[ind][0]
   
    left_side  = np.argmax(times == new_times[ind][0])#hackish, but oh well
    right_side = np.argmax(times == new_times[ind][-1])#hackish, but oh well
    make_interval_plot(d, axhigh, left_side, right_side)
    axhigh.set_title("Highest Day\n" + highest_day.strftime("%m/%d/%Y"))
   
    ind = np.argmin(totals)
    lowest_day = new_times[ind][0]
    left_side  = np.argmax(times == new_times[ind][0])#hackish, but oh well
    right_side = np.argmax(times == new_times[ind][-1])#hackish, but oh well
    make_interval_plot(d, axlow, left_side, right_side)

    axlow.set_title("Lowest Day\n" + lowest_day.strftime("%m/%d/%Y"))


def gen_over_thresh(d, thresh):
    """A generatore that yields the times where the energy usage was above some threshold.
    
    Parameters:
    d -- The building record.
    thresh -- The threshold.

    Yields a pair of indices -- the times on either side of the point which crosses the threshold. 
    (12 hours on either side).
    """
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]

    #Right now, just assume you start and end below thresh
    left_sides   = [ind for ind in range(len(kwhs)-1) if kwhs[ind] <= thresh and kwhs[ind+1] > thresh]
    right_sides  = [ind for ind in range(len(kwhs)-1) if kwhs[ind] > thresh and kwhs[ind+1] <= thresh]
    #Now account for the fact that you may start/end above thresh
    if kwhs[0] >= thresh:
        left_sides = [0] + left_sides
    if kwhs[-1] >= thresh:
        right_sides += [len(kwhs)-1]

    periods = zip(left_sides, right_sides)

    for ls, rs in periods:
        new_left_side  = max(0, ls - 12)
        new_right_side = min(len(kwhs)-1, rs + 12)

        kvals  =  kwhs[new_left_side:new_right_side]
        ptimes = times[new_left_side:new_right_side]
        tvals  = temps[new_left_side:new_right_side]

        yield new_left_side, new_right_side

def get_times_of_highest_change(d, num_times, direction = "increase"):
    """Returns the indices where the highest increase in electricity usage occured.
    Note the indices returned are for just before the spikes occured (as opposed to just after).

    Parameters:
    d -- The building record.
    num_times -- The number of times to be returned.
    direction -- Either "increase" (default) or "decrease"
    """
    kwhs, kwhs_oriflag = d["kwhs"]
    times = d["times"]
    first_deriv = kwhs[1:] - kwhs[:-1]

    inds = np.argsort(first_deriv)

    if direction == "increase":
        inds = inds[-num_times:][::-1]
    else:
        inds = inds[:num_times]

    return inds


def make_interval_plot(d, ax, start, end, show_temps = True, show_sun = True, c = 'blue'):
    """
    Given a building record, an axis, and a start/end, plot the interval between the start and end.

    Parameters:
    d -- The building record.
    ax -- The axis.
    start -- Index of start time.
    end -- Index of end time.

    show_temps [True] -- If True, temperatures are shown in red.
    show_sun [True] -- If True, sunlight is shown in dashed grey.
    c ['blue'] -- The color of the kwhs line. 
    """
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]    

    kwhs          = kwhs[start:end]
    kwhs_oriflag  = kwhs_oriflag[start:end]
    temps         = temps[start:end]
    temps_oriflag = temps_oriflag[start:end]
    times         = times[start:end]

    lns1 = ax.plot(times, kwhs, label = "kwhs", c = c)
    ax.set_ylabel("kwh")

    suns = np.array([max(0, getSun("IL", x.replace(tzinfo = tz_used))) for x in times])
    
    sun_ax = ax.twinx()
    lns2 = sun_ax.plot(times, suns, label = "Sunlight", c = "purple", alpha = 0.3, ls = "dashed")

    sun_ax.set_ylim((-.5, 1))
    sun_ax.set_yticks([])

    weather_ax = sun_ax.twinx()
    weather_ax.set_ylabel("Temperature")
    lns3 = weather_ax.plot(times, temps, label = "Temperature", c = "red", alpha = 0.4)
        
    lns = lns1+lns2+lns3
    labs = [l.get_label() for l in lns]
    weather_ax.legend(lns, labs, loc=0)
    
    ax.grid(True)

    labels = ax.get_xticklabels() 
    for label in labels: 
        label.set_rotation(30)     

        
def make_cami_fig(d, ax):
    """
    Given a building record and an axis, add Cami's favorite plot to the axis.
    Cami's favorite plot provides a detailed illustration of how much money can be saved.
    This figure shows a variety of retrofitting options, and the predicted savings induced by each (as well as confidence intervals).
    """
    num_hours = 24
    kwhs, kwhs_oriflag = d["kwhs"]
    times              = d["times"]
    is_sunday_start    = (lambda x: x.weekday() == 6 and x.hour == 0)
    weeks, new_times   = get_periods(d, num_hours, is_sunday_start)

    thresh   = np.percentile(weeks, 95, axis = 0)
    avg_week = np.average(weeks, axis = 0)

    high_avgs = []
    for col in range(num_hours):
        inds = weeks[:, col] >thresh[col]
        high_avgs.append(np.average(weeks[:, col][inds]))

    high_avgs = np.array(high_avgs)
    sum_avg = np.sum(avg_week)
    sum_high = np.sum(high_avgs)
    ax.set_title("Cami could have saved you:\n%.2f dollars" % ((sum_high - sum_avg) *.05))

    ax.stackplot(range(num_hours), avg_week, high_avgs-avg_week, colors = ["white", "red"])
    ax.plot(range(num_hours), thresh, ls = "dotted", color = "black")
  
def make_cluster_fig(d, types_ax, times_ax):
    """
    Given a building record and two axes, this function populates the axes.
    The first axis (types_ax) is pouplated with the means of the clusters found via clustering the individual days based on behavior.
    The second axis (times_ax) is populated with the original signal over the full year, where each day is colored based on its found cluster.
    """
    kwhs, kwhs_oriflag = d["kwhs"]
    times              = d["times"]

    is_midnight     = (lambda x: x.hour == 0)
    days, new_times = get_periods(d, 24, is_midnight)
    oridays = copy.copy(days)

    times_ax.plot(times, kwhs, lw=0.5, c="black")
    for day in days:
        day -= np.average(day)#center each day

    num_clusters = 3
    clusterer = KMeans(init='k-means++', n_clusters=num_clusters, n_init=10)
    #clusterer = mixture.GMM(n_components=3, covariance_type='full')
    #clusterer = mixture.DPGMM(n_components=3, covariance_type='full')
    clusterer.fit(days)
    preds = clusterer.predict(days)
    #centers = clusterer.means_    
    centers = clusterer.cluster_centers_
    num_in_each = []
    for c in range(len(centers)):
        num_in_each.append(len(preds[preds == c]))

    sorted_inds = [x[1] for x in sorted(zip(num_in_each, range(len(num_in_each))), reverse = True)]

    colors = ["green", "blue", "red", "purple", "pink", "black", "grey"]
    colors = colors[:len(centers)]
    cmap = dict(zip(sorted_inds, colors))

    for c, center in enumerate(centers):
        types_ax.plot(center, label = "# days: " + str(len(preds[preds == c])), c = cmap[c])        

    types_ax.legend()
    types_ax.set_yticks([])
    types_ax.set_ylabel("Relative energy usage")
    for i, d in enumerate(oridays):
        times_ax.plot(new_times[i], d, c = cmap[preds[i]])
    times_ax.set_ylabel("kwhs")

def make_deriv_day_fig(d, ax):
    is_midnight        = (lambda x: x.hour == 0)
    times              = d["times"]
    kwhs, kwhs_oriflag = d["kwhs"]
    deriv = kwhs[1:] - kwhs[:-1]
    hods = np.array([t.hour for t in times[:-1]])
    trim = True
    if trim:
        #remove 1% of data (extreme values)
        upper = np.percentile(deriv, 99.5)
        lower = np.percentile(deriv, 0.5)

        flag = np.array([lower < x and x < upper for x in deriv])
        deriv = deriv[flag]
        hods = hods[flag]
    ax.hist2d(hods, deriv, bins = (23*3, 100), norm = LogNorm())
    ax.set_xticks(range(23))
    ax.axhline(0, 0, 1, ls = "dotted", c = "black")
    ax.set_xlabel("Hours after midnight")
    ax.set_ylabel("Change in kwh")
    
def multi_plot(d, foutn = None):
    fontsize = 24
    if foutn == None:
        foutn = fig_loc + 'fin_' + str(d["bid"]) + '_' + str(the_year) + '.pdf'
    pdf = PdfPages(foutn)
    size = (8.5, 11)
    #size = (13.6, 7.7)

    
    all_figs = ["general",
                "avg behavior",
                "clustering",
                "box plots",
                "behavior",
                "spikes",
                "deriv day",
                "outliers2", 
                "holidays",
                "overthresh",
                "extreme days", 
                "raw"]
                
    bmax = len(all_figs)
    for i, f in enumerate(all_figs):
        add_fig(pdf, d, f, size = size, fontsize = fontsize)
        progress_bar(i+1, bmax)
    print "\n",
    pdf.close()

def _add_fig_box_plots(pdf, d, size, fontsize):
    #Box-plot figures
    b_fig = plt.figure(figsize = size)
    ax_alldays = b_fig.add_subplot(211)
    ax_split = b_fig.add_subplot(212)
    make_boxplot_all_days_fig(d, ax_alldays)
    make_boxplot_weekday_vs_end_fig(d, ax_split)
    b_fig.suptitle("Effect of Schedule", fontsize = fontsize)
    plt.savefig(pdf, format = 'pdf')

def _add_fig_general(pdf, d, size, fontsize):
    #General/global figure
    g_fig = plt.figure(figsize = size)
    g_text    = g_fig.add_subplot(1, 2, 1)
    g_hist    = g_fig.add_subplot(2, 2, 2)
    g_totals  = g_fig.add_subplot(2, 2, 4)
    
    #  make_text_fig(d, g_text)
    make_hist_fig(d, g_hist)
    make_monthly_usage_fig(d, g_totals)

    bid = d["bid"]
    try:
        feature_map, desc = qload("prison_features_map.pkl")
        if isinstance(bid, str) and "q" in bid:
            features = feature_map[int(bid[:-2])]
        else:
            features = feature_map[bid]
        g_fig.suptitle(features["name"], fontsize = fontsize)
        make_prison_text_fig(d, g_text)
    except:
        g_fig.suptitle(str(bid), fontsize = fontsize)
        make_text_fig(d, g_text)
    plt.savefig(pdf, format = 'pdf')

def _add_fig_avg_behavior(pdf, d, size, fontsize):
    #Avg behavior figure    
    n_fig = plt.figure(figsize = size)
    n_avgday  = n_fig.add_subplot(2, 1, 1)
    n_avgweek = n_fig.add_subplot(2, 1, 2)
    
    make_avg_day_fig(d, n_avgday)
    make_avg_week_fig(d, n_avgweek)
    
    n_fig.suptitle("Average Behavior", fontsize = fontsize)
    extract_legend(n_fig)
    plt.savefig(pdf, format = 'pdf')

def _add_fig_behavior(pdf, d, size, fontsize):
    #Behavior fig
    b_fig      = plt.figure(figsize = size)
    b_vstemp   = b_fig.add_subplot(2, 2, 1)
    b_vssun    = b_fig.add_subplot(2, 2, 3)
    b_vstempad = b_fig.add_subplot(2, 2, 2)
    b_vssunad  = b_fig.add_subplot(2, 2, 4)
    
    make_temp_vs_kwh_fig(d, b_vstemp, False)
    make_kwh_vs_sun_fig(d, b_vssun)
    make_temp_vs_kwh_fig(d, b_vstempad, True)
    make_kwh_vs_sun_fig(d, b_vssunad, True)
    
    b_fig.suptitle("Average Behavior", fontsize = fontsize)
    extract_legend(b_fig)
    plt.savefig(pdf, format = 'pdf')

def _add_fig_raw(pdf, d, size, fontsize):
    #Raw data figure
    a_fig = plt.figure(figsize = size)
    a_temps    = a_fig.add_subplot(3, 1, 1)
    a_kwhs     = a_fig.add_subplot(3, 1, 2)
    a_freqs    = a_fig.add_subplot(3, 1, 3)
    
    make_temp_vs_time_fig(d, a_temps)
    make_kwhs_vs_time_fig(d, a_kwhs)
    make_freqs_fig(d, a_freqs)
    a_fig.suptitle("Raw Data", fontsize = fontsize)
    extract_legend(a_fig)
    plt.savefig(pdf, format = 'pdf')

def _add_fig_outliers(pdf, d, size, fontsize):    
    #outliers 
    o_fig = plt.figure(figsize = size)
    avg_day = o_fig.add_subplot(5, 2, 1)
    make_avg_day_fig(d, avg_day)
    times = d["times"]
    
    days = gen_strange_pers(d, 3, period = "day")
    for i, p in enumerate(days):
        day_fig = o_fig.add_subplot(4, 2, 2*(i + 2)-1)
        make_strange_per_fig(d, day_fig, p)
        day_fig.set_title(times[p[0]].strftime("%m/%d/%y"))

    avg_week = o_fig.add_subplot(5, 2, 2)
    make_avg_week_fig(d, avg_week)

    weeks = gen_strange_pers(d, 3, period = "week")
    for i, p in enumerate(weeks):
        week_fig = o_fig.add_subplot(4, 2, 2*(i + 2))
        make_strange_per_fig(d, week_fig, p)
        week_fig.set_title(times[p[0]].strftime("%m/%d/%y") + " - " + 
                           times[p[1]].strftime("%m/%d/%y"))
    o_fig.suptitle("Outliers", fontsize = fontsize)
    extract_legend(o_fig)
    plt.subplots_adjust(hspace = .55)
    plt.savefig(pdf, format = 'pdf')

def _add_fig_outliers2(pdf, d, size, fontsize):
    #outliers, 2 page
    times = d["times"]

    days = gen_strange_pers(d, 6, period = "day")        
    weeks = gen_strange_pers(d, 6, period = "week")

    for page in range(2):
        o_fig = plt.figure(figsize = size)
        avg_day = o_fig.add_subplot(5, 2, 1)
        make_avg_day_fig(d, avg_day)
        for i in range(3):
            try:
                p = days.next()
            except StopIteration:
                break

            day_fig = o_fig.add_subplot(4, 2, 2*(i + 2)-1)
            make_strange_per_fig(d, day_fig, p)
            day_fig.set_title(times[p[0]].strftime("%m/%d/%y"))

        #now the weeks:
        avg_week = o_fig.add_subplot(5, 2, 2)
        make_avg_week_fig(d, avg_week)
        for i in range(3):
            try:
                w = weeks.next()
            except StopIteration:
                break
            week_fig = o_fig.add_subplot(4, 2, 2*(i + 2))
            make_strange_per_fig(d, week_fig, w, c = "purple")
            week_fig.set_title(times[p[0]].strftime("%m/%d/%y") + " - " + 
                               times[p[1]].strftime("%m/%d/%y"))
                
        o_fig.suptitle("Outliers", fontsize = fontsize)
        plt.subplots_adjust(wspace = .35)
        plt.subplots_adjust(hspace = .55)
        extract_legend(o_fig)
        plt.savefig(pdf, format = 'pdf')

def _add_fig_overthresh(pdf, d, size, fontsize):
    #overthresh
    kwhs, kwhs_oriflag = d["kwhs"]
    thresh             = np.percentile(kwhs[kwhs_oriflag], 99)
    overtimes          = gen_over_thresh(d, thresh)
    ot_fig = plt.figure(figsize = size)
    
    for i, p in enumerate(overtimes):
        if i >= 9: break
        over_fig = ot_fig.add_subplot(3, 3, i + 1)
        make_strange_per_fig(d, over_fig, p)

    ot_fig.suptitle("Times in the top 1%%\n (>%.2fkwhs)" % thresh, fontsize = 24)
    extract_legend(ot_fig)
    plt.subplots_adjust(hspace = .35, wspace = .5)
    plt.savefig(pdf, format = 'pdf')

def _add_fig_spikes(pdf, d, size, fontsize):
    #spikes
    times     = d["times"]
    num_times = 6 
    inds      = get_times_of_highest_change(d, num_times, direction = "increase")
    s_fig     = plt.figure(figsize = size)
    
    for i, ind in enumerate(inds):
        left_side  = max(0,          ind-12)
        right_side = min(len(times), ind+12)
        ax = s_fig.add_subplot(num_times//2, 2, i+1)
        make_interval_plot(d, ax, left_side, right_side)
        ax.set_title("Spike at " + times[ind].strftime("%m/%d/%y %H:%M:%S"))
        ax.axvspan(times[ind], times[ind+1], color = "black", alpha = 0.2)
        
    s_fig.suptitle("Spikes", fontsize = fontsize)
    s_fig.subplots_adjust(wspace = .35)
    s_fig.subplots_adjust(hspace = .25)
    extract_legend(s_fig)
    plt.savefig(pdf, format = 'pdf')

def _add_fig_extreme_days(pdf, d, size, fontsize):
    #extreme days
    ex_fig      = plt.figure(figsize = size)
    axavg       = ex_fig.add_subplot(3, 1, 1)
    axhigh      = ex_fig.add_subplot(3, 1, 2)
    axlow       = ex_fig.add_subplot(3, 1, 3)
    make_avg_day_fig(d, axavg)
    make_extreme_days_figs(d, axhigh, axlow)
    
    ex_fig.suptitle("Extreme days", fontsize = fontsize)
    extract_legend(ex_fig)
    plt.savefig(pdf, format = 'pdf')

def _add_fig_clustering(pdf, d, size, fontsize):
    #clustering fig
    c_fig      = plt.figure(figsize = size)
    types_ax   = c_fig.add_subplot(2, 1, 1)
    times_ax   = c_fig.add_subplot(2, 1, 2)
    make_cluster_fig(d, types_ax, times_ax)
    c_fig.suptitle("Types of days", fontsize = fontsize)
    plt.savefig(pdf, format = 'pdf')

def _add_fig_cami(pdf, d, size, fontsize):
    #Cami fig
    cami_fig = plt.figure(figsize = size)
    ax = cami_fig.add_subplot(1, 1, 1)
    make_cami_fig(d, ax)
    cami_fig.suptitle("SAVE ALL THE MONIES", fontsize = fontsize)
    plt.savefig(pdf, format = 'pdf')

def _add_fig_holidays(pdf, d, size, fontsize):
    #Holiday figures
    holidays    = gen_holidays(d)
    times = d["times"]
    for page in range(4):
        fig = plt.figure(figsize = size)
        fig.suptitle("Holidays", fontsize = fontsize)
        avg_day_ax = fig.add_subplot(221)
        make_avg_day_fig(d, avg_day_ax)
        for i in range(3):
            try:
                hol, holiname = holidays.next()
            except StopIteration:
                break
            ax = fig.add_subplot(2, 2, 2+i)
            ax.set_title(holiname)

            #We plot one day on either side of the holiday as well
            left_side  = max(0, hol[0] - 24)
            right_side = min(len(times), hol[1] + 24)
            make_interval_plot(d, ax, left_side, right_side)
            ax.axvspan(times[hol[0]], times[hol[1]], color = "black", alpha = .2)
            
        extract_legend(fig)
        plt.subplots_adjust(wspace = .35)
        plt.subplots_adjust(hspace = .25)
        plt.savefig(pdf, format = 'pdf')

def _add_fig_deriv_day(pdf, d, size, fontsize):
    #Delta analysis
    d_fig      = plt.figure(figsize = size)
    ax         = d_fig.add_subplot(1, 1, 1)
    make_deriv_day_fig(d, ax)
    d_fig.suptitle("Distributions of Load Fluctuations", fontsize = fontsize)
    plt.savefig(pdf, format = 'pdf')

def add_fig(pdf, d, which, size, fontsize = 36):
    #Switch statement:
    {"general"     : _add_fig_general,
     "avg behavior": _add_fig_avg_behavior,
     "behavior"    : _add_fig_behavior,
     "raw"         : _add_fig_raw,
     "outliers"    : _add_fig_outliers,
     "outliers2"   : _add_fig_outliers2,
     "overthresh"  : _add_fig_overthresh,
     "spikes"      : _add_fig_spikes,
     "extreme days": _add_fig_extreme_days,
     "clustering"  : _add_fig_clustering,
     "cami"        : _add_fig_cami,
     "holidays"    : _add_fig_holidays,
     "box plots"   : _add_fig_box_plots,
     "deriv day"   : _add_fig_deriv_day,}[which](pdf, d, size, fontsize)


def test_things():
    '''Used for generating figures for our specific data'''
    global the_year
    font = {'size'   : 6}
    matplotlib.rc('font', **font)
    from adjust_for_dlst import adjustbrec
    
    arg1 = sys.argv[1]
    if arg1 == "states":
        data, desc = qload("state_b_records_" + str(the_year) + "_with_temps_cleaned.pkl")
    elif arg1 == "state":
        num = int(sys.argv[2])
        if len(sys.argv) > 3:            
            the_year = int(sys.argv[3])
            
        data, desc = qload("state_b_records_" + str(the_year) + "_with_temps_cleaned.pkl")
        data = [data[num]]
    else:
        data, desc = qload("agentis_oneyear_" + arg1 + "_updated.pkl")
        data = [data]
                      
    sys.stdout.flush()
    #data = [data[-1]]
    print "Data desc:", desc
    print "Number of points:", len(data)
    print "vals for point 0:", len(data[0]["times"])
    print "\n"
    
    #make_comparison_doc(data);exit()
    
    for ind, d in enumerate(data):
        #d = adjustbrec(d, the_year)
        print d["bid"]
        print d["times"][:4]
        print d["kwhs"][0][:4]
       
        multi_plot(d)
        print "*"*10, "Finished report for", d["bid"], "*"*10
        sys.stdout.flush()

def make_comparison_doc(ds, foutn = None):
    '''This take s a list of builing records (of length at most six), and makes a pdf comparing them'''

    assert len(ds) <= 6, "List has too many building records" 
    fontsize = 24
    if foutn == None:
        foutn = fig_loc + 'comparison.pdf'
    pdf = PdfPages(foutn)
    size = (8.5, 11)

    feature_map, desc = qload("prison_features_map.pkl")
    funs = [(make_temp_vs_time_fig, "Temperature over time"),
            (make_kwhs_vs_time_fig, "Energy usage over time"),
            (make_freqs_fig, "In the frequency domain"),
            (make_temp_vs_kwh_fig, "Energy usage vs temperature"),
            (make_avg_day_fig, "Average day"),
            (make_avg_week_fig, "Average week"),
            (make_hist_fig, "Histogram of energy usage"),
            (make_kwh_vs_sun_fig, "Energy usage vs sunlight"),
            (make_monthly_usage_fig, "Monthly usage"),
            (make_deriv_day_fig, "Distribution of load fluctuation"),
            (make_boxplot_all_days_fig, "Effect of schedule\n(all days)"),
            (make_boxplot_weekday_vs_end_fig, "Effect of schedule\n(weekday vs weekend)")]
    for fun, title in funs:
        fig = plt.figure(figsize = size)
        fig.suptitle(title, fontsize = fontsize)
        for i, d in enumerate(ds):
            loc  = (3, 2, i+1)
            ax = fig.add_subplot(*loc)
            
            fun(d, ax)
            ax.set_title(feature_map[d["bid"]]["acronym"])
        extract_legend(fig)
        plt.savefig(pdf, format = 'pdf')
   
    pdf.close() 

if __name__ == "__main__":
    

    states = qload("stateDB.pickle")

    #test_things()
    #exit()
    args = sys.argv
    if len(args) < 3:
        print "Usage:"
        print "\tpython make_report.py <infile> <outfile>"
        print "\tWhere infile is a pickled building record, and outfile is a pdf"
        exit()
    
    infile  = args[1]
    outfile = args[2]
        
    states = qload("stateDB.pickle")
    font = {'size'   : 6}
    matplotlib.rc('font', **font)
    try:
        data, desc = qload(infile)
    except:
        print "Exiting, file '%s' not found" %infile
        exit(-1)
  
    
        
    print len(args)
