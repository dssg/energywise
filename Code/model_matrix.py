import numpy as np
import pytz
import time
from utils import *
from getSunny import *
from holiday import *
from datetime import datetime
from dateutil import tz

def change_mat(ts,d):
    """Recieve a time series and a markov delay period.
       Return a matix of that design."""
    n=len(ts)
    x = np.array(ts[(d-1):n-1])
    for r in range(2,d+1):
        b = np.array(ts[(d-r):(n-r)])
        x = np.concatenate([x.reshape(len(x),-1),b.reshape(len(b),-1)],axis=1)
    return x
         
def mat_from_building_pkl(b,md,dt=None,ds=None,dw=None,h=None,td=None):
    """Receive a building dictionary.
       md = number of autoregressive factors in kwhs
       dt = number of autoregressive factors in temperature
       if ds = T calculate array with position of the sun for y_i
       if dw = T calculate array with day of the week for y_i
       if h = T calculate array with dummy for holiday in y_i
       if td = T calcuate array with the hour of the day in y_i
       Return the matrices for peak prediction on this building.
       This method assumes that missing values have been inputed."""
    x = change_mat(b["kwhs"][0],md)
    names = []
    [names.append("x_t-"+str(i)) for i in range(1,md+1)]
    # optional covariates
    if dt is not None:
        if dt <= md:
            ct = change_mat(b["temps"][0][(md-dt):],dt)
        else:
            ct= change_mat(np.concatenate((np.zeros(dt-md),b["temps"][0]),axis=1),dt)
        x = np.concatenate((x,ct),axis=1)
        [names.append("t_t-"+str(i)) for i in range(1,dt+1)]
    array_times=change_mat(b['times'],md)
    num_rows=len(array_times)
    if ds is not None:
        x_sun=np.array([getSun("IL",array_times[i][-1]) for i in range(num_rows)])
        x = np.concatenate((x,x_sun.reshape(len(x_sun),-1)),axis=1)
        names.append("sun")
    if dw is not None:
        # returns an integer from 0-6
        # 0 is monday... 6 is sunday
        x_day=np.array([array_times[i][-1].weekday() for i in range(num_rows)])
        x = np.concatenate((x,x_day.reshape(len(x_day),-1)),axis=1)
        names.append("weekday")
    if h is not None:
        x_hol=np.array([is_hol(array_times[i][-1]) for i in range(num_rows)])
        x = np.concatenate((x,x_hol.reshape(len(x_hol),-1)),axis=1)
        names.append("holiday")
    if td is not None:
        x_hour=np.array([array_times[i][-1].hour for i in range(num_rows)])
        x = np.concatenate((x,x_hour.reshape(len(x_hour),-1)),axis=1)
        names.append("hour")
    if md<dt:
        x = x[(dt-md):,]
    y = b["kwhs"][0][md:]
    return [y, x, names]

if __name__ == "__main__":
    # Example 1: change_mat
    ts=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18]
    md = 4
    change_mat(ts,md)
    # Example 2: delay in temp smaller than delay in x's
    data, desc = qload("agentis_oneyear_22891_updated.pkl",loc="")
    mat_from_building_pkl(data,md=4,dt=2)
    
    #Example 3
    d = {"kwhs":[[1,2,3,4,5,6,7,8,9,10],"nada"], "temps":[[1,2,3,4,5,6,7,8,9,10],
"nada"], "times": data["times"][-10:]}
    y=mat_from_building_pkl(d,md=4,dt=3,ds=1,dw=1,h=1,td=1)
    
   
