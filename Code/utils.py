import numpy as np
import cPickle as pickle
#data_loc = "../Data/"
#data_loc = "/mnt/energy_data/Data/"
data_loc = "C:/Users/Scott/Data/"

fig_loc = "../Figs/"

def qload(finn, loc = ""):
    """Unpickles from file with name finn"""
    if loc == "":
        loc = data_loc
    finn= loc + finn
    print "Loading", finn +"...."
    fin = open(finn)
    toR = pickle.load(fin)
    print "\tLoaded"
    fin.close()
    return toR

def qdump(var, foutn, loc = ""):
    """ Pickles var a file with name foutn"""
    if loc == "":
        loc = data_loc
    foutn = loc + foutn
    print "Saving", foutn +"...."
    fout = open(foutn, "wb")
    pickle.dump(var, fout)
    fout.close()
    print "\tSaved"

def interp(all_times, base_val):
    old_val = base_val
    for i, v in enumerate(all_times):
        if v == 0.0:
            
            all_times[i] = old_val
        old_val = all_times[i]
    return all_times


def clean(times, vals, start_ts, num_times):
    '''Given a list of time stamps, a corresponding list of vals, a start time, and a number of times, this returns a list ordered correctly with missing values filled in'''
    toR = [0 for i in range(num_times)]
    for t, v in zip(times, vals):
        ind = (int(t) - start_ts)//3600
        if ind < num_times:
            toR[ind] = v
    return interp(toR, vals[0])

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)

#takes a time series and and a sorted list of times, and fills in via linear interpolation
def fill_in(ts, all_times):
    ori_flag = [] #True means original data is used. False means data was interpolated
    toR = []
    num_times = len(ts)

    left_ind = 0 
    right_ind  = 1
    ati = 0 #index into all_times

    def interpolate(left, target, right):
        left_time, left_val   = left
        right_time, right_val = right

        delta    = (right_time - left_time).total_seconds()
        alpha    = (target - left_time).total_seconds() / delta
        return     (alpha * right_val)  +  (1 - alpha) * left_val

    while (ati < len(all_times)):
        at = all_times[ati]
        if right_ind >= num_times:
            ati += 1
            toR.append((at, ts[-1][1]))
            ori_flag.append(False)
        else:
            left_time, left_val = ts[left_ind]
            right_time, right_val = ts[right_ind]
            
            if at == left_time:
                ati += 1
                toR.append((at, left_val))
                ori_flag.append(True)

            elif at == right_time:
                ati += 1
                toR.append((at, right_val))
                ori_flag.append(True)
                
            elif at > right_time:
                left_ind += 1
                right_ind  += 1
            
            elif at < left_time:
                ati += 1
                toR.append((at, left_val))
                ori_flag.append(False)

            elif at < right_time and at > left_time: #we're good to do the interpolation
                new_val  = interpolate((left_time, left_val), at, (right_time, right_val))
                ati     += 1
                toR.append((at, new_val))
                ori_flag.append(False)
    return toR, ori_flag
            
