import matplotlib
matplotlib.use('Agg')
from   os import listdir
from   utils import *
import numpy as np
import sys
import matplotlib.pyplot as plt


def get_report(d):
    kwhs, kwhs_oriflag = d["kwhs"]
    toR = {}
    toR["avg"]        = np.average(kwhs[kwhs_oriflag])
    toR["max"]        = np.max(kwhs[kwhs_oriflag])
    toR["min"]        = np.min(kwhs[kwhs_oriflag])
    toR["var"]        = np.var(kwhs[kwhs_oriflag])
    toR["med"]        = np.median(kwhs[kwhs_oriflag])
    toR["total"]      = np.sum(kwhs[kwhs_oriflag]) 
    
    return toR


def agg_reports(list_of_brecs):
    toR = {}
    for d in list_of_brecs:
        try:
            r = get_report(d)
            for k in r.keys():
                if k in toR:
                    toR[k].append(r[k])
                else:
                    toR[k] = [r[k]]
        except:
            print "Failed ", d["bid"]
            
    return toR

def plot_agg_reports(agg):
    for k in agg.keys():
        fig = plt.figure(figsize = (5, 5))
        ax  = fig.add_subplot(1, 1, 1)
        num_bins = int(np.log2(len(agg.keys())) + 1)
        ax.hist(agg[k], bins = num_bins)
        ax.set_title(k)
        plt.savefig("agg_reports_" + k + ".png")

if __name__ == "__main__":
    finns = [x for x in listdir(data_loc) if "_updated.pkl" in x and "oneyear" in x]
    ds = []
    for finn in finns:
        d, desc = qload(finn)
        ds.append(d)
    agg = agg_reports(ds)
    plot_agg_reports(agg)
