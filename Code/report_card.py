import matplotlib
matplotlib.use('Agg') #used to keep Amazon happy
from   os import listdir
from   utils import *
import numpy as np
import sys
import matplotlib.pyplot as plt
from   plotter_new import get_periods

def get_report(d):
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]
    toR = {}
    toR["avg"]        = np.average(kwhs[kwhs_oriflag])
    toR["max"]        = np.max(kwhs[kwhs_oriflag])
    toR["min"]        = np.min(kwhs[kwhs_oriflag])
    toR["var"]        = np.var(kwhs[kwhs_oriflag])
    toR["med"]        = np.median(kwhs[kwhs_oriflag])
    toR["total"]      = np.sum(kwhs[kwhs_oriflag]) 
    
    #avg hour of daily peak:
    is_midnight         = (lambda x: x.hour == 0)
    days, new_times     = get_periods(d, 24, is_midnight)
    peak_hours          = np.ma.argmax(days, axis = 1)
    toR["avg_tod_peak"] = np.ma.average(peak_hours)
    #TODO: Separate into weekend/day

    #avg distance (in hours) between temp peak 
    temps, new_times = get_periods(d, 24, is_midnight, which = "temps")
    peak_temps = np.ma.argmax(temps, axis = 1)
    dists = np.ma.abs(peak_temps - peak_hours)
    toR["avg_temp_to_kwhs_peaks"] = np.ma.average(dists)


    #TODO: Add avg distance (in hours) of daily peak to natural noon
    
    
    #Phantom load approximation
    is_midnight         = (lambda x: x.hour == 0)
    skip_weekdays       = (lambda x: x.weekday() < 5)
    weekends, new_times = get_periods(d, 24, is_midnight, skip_fun = skip_weekdays)

    is_midnight         = (lambda x: x.hour == 0)
    skip_weekends       = (lambda x: x.weekday() >= 5)
    weekdays, new_times = get_periods(d, 24, is_midnight, skip_fun = skip_weekends)
    toR["avg_weekday_min"] = np.ma.average(np.ma.min(weekdays, axis = 0))
    toR["avg_weekend_min"] = np.ma.average(np.ma.min(weekends, axis = 0))

    #Distance correlation between temps and kwhs (agg days)
    #Note that we use imputed temps, but only original kwhs
    is_midnight      = (lambda x: x.hour == 0)
    days, new_times  = get_periods(d, 24, is_midnight)
    day_totals       = np.ma.sum(days, axis = 1)
    temps, new_times = get_periods(d, 24, is_midnight, which = "temps")
    temp_avgs = np.ma.average(temps, axis = 1)
    toR["dCorr_kwhs_temps"] = dCorr(day_totals, temp_avgs)
    

    return toR

def agg_reports(list_of_brecs):
    toR = {}
    naics_codes = []
    for d in list_of_brecs:        
        try:
            r = get_report(d)
            for k in r.keys():
                if k in toR:
                    toR[k].append(r[k])
                else:
                    toR[k] = [r[k]]
            naics_codes.append(d["naics"])

        except Exception as inst:
            print "Failed", d["bid"]
            print type(inst)     # the exception instance
            print inst.args      # arguments stored in .args
            print inst           # __str__ allows args to printed directly
            
    return toR, naics_codes

def plot_agg_reports(agg, add_str = ""):
    for k in agg.keys():
        fig = plt.figure(figsize = (5, 5))
        ax  = fig.add_subplot(1, 1, 1)
        num_bins = 100# int(np.log2(len(agg.keys())) + 1)
        ax.hist(agg[k], bins = num_bins)
        ax.set_title(k)
        plt.savefig(fig_loc + "agg_reports_" + k + add_str +  ".png")
        plt.close()

if __name__ == "__main__":
    finns = [x for x in listdir(data_loc) if "_updated.pkl" in x and "oneyear" in x]
    ds = []
 
    for finn in finns:
        d, desc = qload(finn)
        ds.append(d)
        
    agg, naicss = agg_reports(ds)
    qdump((agg, "The aggregate reports"), "agg_reps.pkl")

    #naicss = [d["naics"] for d in ds]
    qdump((naicss, "The NAICS codes in the same order as the agg report"), "naics_codes.pkl") 
    #plt_agg_reports(agg)
    exit()
    for naics in naicss:
        new_ds = [d for d in ds if d["naics"] == naics]
        agg = agg_reports(new_ds)
        plot_agg_reports(agg, add_str = "_" + str(naics) + "with_" + str(len(new_ds)))

    #agg = agg_reports(ds)
    #plot_agg_reports(agg)
 
