import matplotlib
#matplotlib.use('Agg') #used to keep Amazon happy
from   os import listdir
from   utils import *
import numpy as np
import sys
import matplotlib.pyplot as plt

import plotter_new as pn


def get_report(d):
    """Given a building record d, return a Building Report.
    A Building Report is a dictionary mapping names of features to values.
    TODO: Say what each feature is.
    """
    toR = {}
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]
    times = d["times"]
    toR["naics"] = d["naics"] #Just to see what happens here...
    
    #General stats
    toR["avg"]        = np.average(kwhs[kwhs_oriflag])
    toR["max"]        = np.max(kwhs[kwhs_oriflag])
    toR["min"]        = np.min(kwhs[kwhs_oriflag])
    toR["var"]        = np.var(kwhs[kwhs_oriflag])
    toR["med"]        = np.median(kwhs[kwhs_oriflag])
    toR["total"]      = np.sum(kwhs[kwhs_oriflag]) 
    

    #Difference between weekday and weekend
    is_midnight     = (lambda x: x.hour == 0)
    skip_weekdays   = (lambda x: x.weekday() < 5)
    weekends, _     = pn.get_periods(d, 24, is_midnight, "kwhs", skip_weekdays)
    
    skip_weekend    = (lambda x: x.weekday() >= 5)
    weekdays, _     = pn.get_periods(d, 24, is_midnight, "kwhs", skip_weekend)

    weekday_peaks   = np.ma.max(weekdays, axis = 1)
    weekend_peaks   = np.ma.max(weekends, axis = 1)
    
    avg_weekday_peak = np.ma.average(weekday_peaks)
    avg_weekend_peak = np.ma.average(weekend_peaks)
    
    toR["week_day_vs_end_peaks"] = avg_weekday_peak - avg_weekend_peak

    #avg hour of daily peak:

    days, new_times     = pn.get_periods(d, 24, is_midnight)
    peak_hours          = np.ma.argmax(days, axis = 1)
    toR["avg_tod_peak"] = np.ma.average(peak_hours)
    #TODO: Separate into weekend/day

    #avg distance (in hours) to temp peak 
    temps, new_times = pn.get_periods(d, 24, is_midnight, which = "temps")
    peak_temps = np.ma.argmax(temps, axis = 1)
    dists = np.ma.abs(peak_temps - peak_hours)
    toR["avg_temp_to_kwhs_peaks"] = np.ma.average(dists)

    
    #TODO: Add avg distance (in hours) of daily peak to natural noon
    
    #Phantom load approximation
    is_midnight         = (lambda x: x.hour == 0)
    skip_weekdays       = (lambda x: x.weekday() < 5)
    weekends, new_times = pn.get_periods(d, 24, is_midnight, skip_fun = skip_weekdays)

    is_midnight         = (lambda x: x.hour == 0)
    skip_weekends       = (lambda x: x.weekday() >= 5)
    weekdays, new_times = pn.get_periods(d, 24, is_midnight, skip_fun = skip_weekends)
    toR["avg_weekday_min"] = np.ma.average(np.ma.min(weekdays, axis = 0))
    toR["avg_weekend_min"] = np.ma.average(np.ma.min(weekends, axis = 0))

    #Distance correlation between temps and kwhs (agg days)
    #Note that we use imputed temps, but only original kwhs
    is_midnight      = (lambda x: x.hour == 0)
    days, new_times  = pn.get_periods(d, 24, is_midnight)
    day_totals       = np.ma.sum(days, axis = 1)
    temps, new_times = pn.get_periods(d, 24, is_midnight, which = "temps")
    temp_avgs = np.ma.average(temps, axis = 1)
    toR["dCorr_kwhs_temps"] = dCorr(day_totals, temp_avgs)
    
    #Stats regarding first derivative
    first_deriv         = kwhs[1:] - kwhs[:-1]
    first_deriv_oriflag = np.logical_and(kwhs_oriflag[1:], kwhs_oriflag[:-1])
    oris                = first_deriv[first_deriv_oriflag]
    increases           = oris[oris > 0]
    decreases           = oris[oris < 0]

    toR["avg_increase"] = np.average(increases)
    toR["avg_decrease"] = np.average(decreases)
    toR["var_change"]   = np.var(oris)
    
    #Stats regarding DFT
    a         = np.fft.fft(kwhs)
    num_times = len(kwhs)
    half      = (num_times + 1) // 2
    a         = a[0:half +1]
    a[0]      = 0 #drop constant part of signal

    power     = a**2 #definition of power
    power     = np.absolute(power) #to make everything real
    total_power = np.sum(power)
    toR["spectral_power"] = np.real(total_power)
    
    highlighted_periods =  np.array([24, 168])
    highlighted_freqs   = float(num_times) / highlighted_periods
    for p, f in zip(highlighted_periods, highlighted_freqs):
        mykey = "prop_of_" + str(p)
        toR[mykey] = np.absolute((a[f] ** 2)) / total_power

    #Missing values:
    toR["num_missing"] = len([x for x in kwhs_oriflag if not x])

    #Relating to boxplots
    hr_start = 8
    hr_stop = 16
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

    #width of 50percent block
    weekday_working_75 = np.percentile(weekday_kwhs_in, 75)
    weekday_working_25 = np.percentile(weekday_kwhs_in, 25)
    toR["weekday_working_width"] = weekday_working_75 - weekday_working_25
    
    weekday_nonworking_75 = np.percentile(weekday_kwhs_out, 75)
    weekday_nonworking_25 = np.percentile(weekday_kwhs_out, 25)
    toR["weekday_nonworking_width"] = weekday_working_75 - weekday_working_25
    
    weekend_working_75 = np.percentile(weekend_kwhs_in, 75)
    weekend_working_25 = np.percentile(weekend_kwhs_in, 25)
    toR["weekend_working_width"] = weekend_working_75 - weekend_working_25
    
    weekend_nonworking_75 = np.percentile(weekend_kwhs_out, 75)
    weekend_nonworking_25 = np.percentile(weekend_kwhs_out, 25)
    toR["weekend_nonworking_width"] = weekend_working_75 - weekend_working_25
    
    #now comparing medians
    weekday_working_med    = np.median(weekday_kwhs_in)
    weekday_nonworking_med = np.median(weekday_kwhs_out)

    weekend_working_med    = np.median(weekend_kwhs_in)
    weekend_nonworking_med = np.median(weekend_kwhs_out)

    toR["weekday_med_dif"]       = weekday_working_med - weekday_nonworking_med
    toR["weekend_med_dif"]       = weekend_working_med - weekend_nonworking_med
    toR["day_vs_end_working"]    = weekday_working_med - weekend_working_med
    toR["day_vs_end_nonworking"] = weekday_nonworking_med - weekend_nonworking_med

    return toR

def agg_reports(list_of_brecs):
    """Given a list of building records, return an aggregate report.
    In an aggregate report, each key in a Building Report is mapped to a list of values (one per building).
    """
    toR         = {}
    naics_codes = []
    errs        = open("errs.txt", "w")

    for d in list_of_brecs:        
        try:
            r = get_report(d)
            for k in r.keys():
                if k in toR:
                    toR[k].append(r[k])
                else:
                    toR[k] = [r[k]]
            #naics_codes.append(d["naics"])
            naics_codes.append(d["btype"])
            print d["btype"]
        except Exception as inst:
            print "Failed", d["bid"]
            print type(inst)     # the exception instance
            print inst.args      # arguments stored in .args
            print inst           # __str__ allows args to printed directly
            errs.write(str(d["bid"]) + "\n")
            sys.stdout.flush()
    return toR, naics_codes

def plot_agg_reports(agg, add_str = ""):
    for k in agg.keys():
        fig      = plt.figure(figsize = (5, 5))
        ax       = fig.add_subplot(1, 1, 1)
        num_bins = 100# int(np.log2(len(agg.keys())) + 1)
        ax.hist(agg[k], bins = num_bins)
        ax.set_title(k)
        plt.savefig(fig_loc + "agg_reports_" + k + add_str +  ".png")
        plt.close()

def process_prison_quarters():
    data, desc = qload("state_b_records_" + str(the_year) + "_quarters.pkl")
    toSave = []
    for d in data:
        print d["bid"]
        sys.stdout.flush()
        toSave.append((d["bid"], get_report(d)))
    qdump((toSave, "The Building Reports for the prison facilities, by quarter"), "prison_reps.pkl")

if __name__ == "__main__":
    process_prison_quarters(); exit()
    finns = [x for x in listdir(data_loc) if "_updated.pkl" in x and "oneyear" in x]
    ds    = []
    add_str = "_btype"
    for finn in finns:
        d, desc = qload(finn)
        ds.append(d)
        
    agg, naicss = agg_reports(ds)
    qdump((agg, "The aggregate reports"), "agg_reps.pkl")

    #naicss = [d["naics"] for d in ds]
    qdump((naicss, "The NAICS codes in the same order as the agg report"), "naics_codes" + add_str +  ".pkl") 
    #plt_agg_reports(agg)
    exit()
    for naics in naicss:
        new_ds = [d for d in ds if d["naics"] == naics]
        agg    = agg_reports(new_ds)
        plot_agg_reports(agg, add_str = "_" + str(naics) + "with_" + str(len(new_ds)))

    #agg = agg_reports(ds)
    #plot_agg_reports(agg)
 
