import  numpy as np
import  sys
import  cPickle as pickle
from    scipy.spatial import distance
data_loc = "../Data/"
fig_loc  = "../Figs/"
the_year = 2012

def extract_legend(fig, loc = 'upper left'):
    """
    Given a figure, this function goes over each subplot and removes the legends.
    It then adds a figure legend, which aggregates all subplot legends.

    Note: Each label appears only once in the figure legend, no matter how many subplots have it.
    So, for example, if each subplot has "temperature", the figure legend will only show one entry for "temperature".
    """
    axes = fig.get_axes()
    handles = []
    labels  = []

    for ax in axes:
        hs, ls = ax.get_legend_handles_labels()
        if len(hs) >= 1:
            leg = ax.legend()
            if leg is not None:
                leg.set_visible(False)
            for h, l in zip(hs, ls):
                if l not in labels:
                    labels.append(l)
                    handles.append(h)
    if len(handles) >= 1:
        fig.legend(handles, labels, loc)

def progress_bar(done, bmax = 100):    
    """A terminal-based progress bar"""
    sys.stdout.write ("\r")
    sys.stdout.write ("[")
    perc = int((done/float(bmax))*100)
    sys.stdout.write('\033[94m')
    red = '\033[91m'
    end = '\033[0m'
    spin = "-\|/-\|/-\*"
    how_far = perc // 10
    inbar = "*" * how_far + red + spin[how_far] +  end + " " * (10 - how_far) 
    sys.stdout.write(inbar)
    sys.stdout.write(end)
    sys.stdout.write("]")
    sys.stdout.write(" "+str(perc))
    sys.stdout.write("%")
    if done >= bmax:         
        sys.stdout.write("\r[-FINISHED!-] 100%")
        sys.stdout.write("\n")
    sys.stdout.flush()

def dCorr(x, y):
    """Returns the distance-correlation between x and y"""
    n = len(x)
    assert n == len(y), "Vectors must be of the same length"
    def dCov2(xM, yM):
        """Returns the distance-covariance squared of x and y, given the pairwise
        distance matrices xM and yM."""
        return (1.0 / n**2) * np.sum(xM * yM) #sum of all entries in component-wise product
        

    A = distance.squareform(distance.pdist(np.array(x).reshape(n, -1)))
    B = distance.squareform(distance.pdist(np.array(y).reshape(n, -1)))

    #Center along both axes:
    A -= A.mean(axis = 0)
    B -= B.mean(axis = 0)

    A -= A.mean(axis = 1)
    B -= B.mean(axis = 1)

    #Calculate distance covariances
    dcov  = np.sqrt(dCov2(A, B))
    dvarx = np.sqrt(dCov2(A, A))
    dvary = np.sqrt(dCov2(B, B))
    toR = dcov / np.sqrt(dvarx * dvary)
    if np.isnan(toR):
        return 0.0
    else:
        return toR
    
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
    sys.stdout.flush()
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
    sys.stdout.flush()
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

