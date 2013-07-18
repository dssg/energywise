import  ephem
import  math
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
    naics                = d["naics"]
    btype                = d["btype"]
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]
    
    toPrint =  "ID:\n   "   + str(bid)\
        + "\nNaics:\n   "     + str(naics)\
        + "\nType:\n   "    + str(btype)\
        + "\nAverage Hourly Energy Usage:\n    " + str(np.round(np.average(kwhs), 2)) + "kw"\
        + "\nMin:\n    "    + str(np.round(np.min(kwhs), 2))\
        + "\nMax:\n    "    + str(np.round(np.max(kwhs), 2))\
        + "\nTotal:\n     " + str(np.round(np.sum(kwhs)/1000.0, 2)) + "gwh"
    textfig.text(0.05, .95,toPrint , fontsize=12, ha='left', va='top')
    
    textfig.set_xticks([])
    textfig.set_yticks([])
    

def make_temp_vs_time_fig(d, tvt):
    times                = d["times"]
    temps, temps_oriflag = d["temps"]
    
    tvt.plot(   times[temps_oriflag] , temps[temps_oriflag] , c = "blue")
    tvt.scatter(times[~temps_oriflag], temps[~temps_oriflag], lw = 0,  c = "red")

    tvt.set_title("Temperature Over Time")
    tvt.set_ylabel("Temperature")
    
    labels = tvt.get_xticklabels() 
    for label in labels: 
        label.set_rotation(30) 
        

def make_kwhs_vs_time_fig(d, tvk):
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]

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
    avgday.set_ylabel("Energy Usage (kwh)")
    avgday.set_xlim(-0.5, 24.5)
    avgday.set_xticks(range(0, 24, 4))
    avgday.grid(True)
    avgday.legend()


def make_avg_week_fig(d, avgweek):
    is_sunday_start  = (lambda x: x.weekday() == 6 and x.hour == 0)
    weeks, new_times = get_periods(d, 168, is_sunday_start, "kwhs")

    avg_week  = np.ma.average(weeks, axis = 0)
    std_week  = np.ma.std(weeks, axis = 0)

    avgweek.errorbar(np.arange(168), avg_week, yerr =std_week, label = "Energy Usage", errorevery = 6)

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


def make_hist_fig(d, hist):
    kwhs, kwhs_oriflag   = d["kwhs"]
    
    hist.hist(kwhs[kwhs_oriflag], bins = 50)
    hist.set_title("Histogram of Energy Usage")
    hist.set_ylabel("kwhs")


def gen_peaks(d, num_peaks = 3):
    kwhs, kwhs_oriflag   = d["kwhs"]
    
    inds = np.argsort(kwhs)[-num_peaks:]
    for ind in inds:
        yield ind


def make_peak_fig(d, ax, ind):
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
 
    highest_date = times[ind]
    highest_val  = kwhs[ind]
    leftmost  = max(0, ind-12)
    rightmost = min(len(kwhs), ind+12)
    ax.plot(kwhs[leftmost:rightmost], alpha = 0.5)


def make_kwh_vs_sun_fig(d, ax):
    states=pickle.load(open('stateDB.pickle','r'))    
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
        return math.sin(alt)

    bid                  = d["bid"]
    naics                = d["naics"]
    btype                = d["btype"]
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]

    sun_pos = np.array([max(-100, getSun("IL", t)) for t in times[kwhs_oriflag]])
    ax.hist2d(kwhs[kwhs_oriflag], sun_pos, bins = 50, norm = LogNorm())
    
    ax.set_title("Energy Usage vs sunlight")
    ax.set_xlabel("kwh")
    ax.set_ylabel("Sunlight")
    ax.grid(True)

def make_monthly_usage_fig(d, ax):
    bid                  = d["bid"]
    naics                = d["naics"]
    btype                = d["btype"]
    times                = d["times"]
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]

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

def gen_strange_pers(d, num_pers = 3, period = "day"):
    kwhs, kwhs_oriflag = d["kwhs"]

    if period == "day":
        first_pred = (lambda x: x.hour == 0)
    elif period == "week":
        first_pred = (lambda x: x.weekday() == 0 and x.hour == 0)
    else:
        print "period must be 'day' or 'week'."
        return
    num_per_period = 24 if period == "day" else 168
    pers, new_times = get_periods(d, num_per_period, first_pred, "kwhs")
    pers = pers[1:-2] #used as a hack to fix the wrap-around issue
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
        vals = pers[ind]
        times = new_times[ind]
        yield vals, times
        

def make_strange_per_fig(d, ax, per):
    vals, new_times = per
    ax.plot(new_times, vals)
    ax.set_title("Beginning " + new_times[0].strftime("%m/%d/%Y"))
    ax.set_ylabel("kwhs")
    labels = ax.get_xticklabels() 
    for label in labels: 
        label.set_rotation(30) 
    

def make_extreme_days_figs(d, axhigh, axlow):
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
    ind = np.argmax(totals)
    highest_day = new_times[ind][0]
    axhigh.plot(new_times[ind], days[ind])
    axhigh.set_title("Highest Day\n" + highest_day.strftime("%m/%d/%Y"))
    labels = axhigh.get_xticklabels() 
    for label in labels: 
        label.set_rotation(30) 

    ind = np.argmin(totals)
    lowest_day = new_times[ind][0]
    axlow.plot(new_times[ind], days[ind])
    axlow.set_title("Lowest Day\n" + lowest_day.strftime("%m/%d/%Y"))
    labels = axlow.get_xticklabels() 
    for label in labels: 
        label.set_rotation(30) 
  
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
    #freqs    = fig.add_subplot(nrows, ncols, 1)
    hist    = fig.add_subplot(nrows, ncols, 1)
    
    make_text_fig(d, textfig)
    make_temp_vs_time_fig(d, tvt)
    make_kwhs_vs_time_fig(d, tvk)
    #make_freqs_fig(d, freqs)
    make_hist_fig(d, hist)
    make_temp_vs_kwh_fig(d, tmpsvk)
    make_avg_day_fig(d, avgday)
    make_avg_week_fig(d, avgweek)
    plt.subplots_adjust(hspace = .35)
    plt.savefig(fig_loc + "fig_" + str(bid) + "_2011.png")
    plt.clf()
    plt.close()
    

def test_things(d):
    bid = d["bid"]
    '''
    fig = plt.figure(figsize = (10, 10))
    ax1 = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(1, 2, 2)

    make_extreme_days_figs(d, ax1, ax2)
    plt.show()
    exit()

    '''    

    fig2 = plt.figure(figsize = (20, 20))
    weeks = gen_strange_pers(d, 6, period = "week")
    weeks.next()
    for i, p in enumerate(weeks):
        week_fig = fig2.add_subplot(3, 3, i + 1)
        make_strange_per_fig(d, week_fig, p)

    avg_week = fig2.add_subplot(4, 1, 4)
    make_avg_week_fig(d, avg_week)
    plt.show()
    exit()

    fig2 = plt.figure(figsize = (20, 20))
    days = gen_strange_pers(d, 6, period = "day")


    for i, p in enumerate(days):
        day_fig = fig2.add_subplot(3, 3, i + 1)
        make_strange_per_fig(d, day_fig, p)

    avg_day = fig2.add_subplot(4, 1, 4)
    make_avg_day_fig(d, avg_day)
    plt.show()
    exit()


    fig2  = plt.figure(figsize = (10, 10))
    peaks = fig2.add_subplot(1, 1, 1)
    peaksgen = gen_peaks(d, 3)
    for p in peaksgen:
        print p
        make_peak_fig(d, peaks, p)
    plt.show()
    exit()
    
    fig    = plt.figure(figsize = (20, 20))
    totals = fig.add_subplot(1, 1, 1)
    make_monthly_usage_fig(d, totals)
    plt.show()
    exit()

if __name__ == "__main__":
    #data, desc = qload("agentis_b_records_2011_updated_small.pkl")
    #data, desc = qload("agentis_b_records_2011_updated.pkl")
    #data, desc = qload("agentis_allyears_19870_updated.pkl")
    #data, desc = qload("agentis_allyears_18400_updated.pkl")
    #data, desc = qload("agentis_allyears_21143_updated.pkl")
    data, desc = qload("agentis_allyears_22891_updated.pkl")
    data = [data]
    sys.stdout.flush()
    #data = [data[-1]]
    print "Data desc:", desc
    print "Number of points:", len(data)
    print "vals for point 0:", len(data[0]["times"])
    print "\n"
    for ind, d in enumerate(data):
        test_things(d)
        exit()
        plot_it(d)
        bid = d["bid"]
        print str(ind), ": plotted something..."
        sys.stdout.flush()
        
        
