import  numpy as np
import  pytz
import  datetime as rdatetime
from    datetime import datetime
from   dateutil import tz
from utils import fill_in, qdump, qload
data_loc = 'C:/Users/Andrea/Documents/DSSG/Energy project/Codigos prueba/Temperature/'
tz_used = pytz.timezone("US/Central")

def temps_to_building_pkl(facility):
    start_date   = datetime.strptime("1/1/2011 00:00:00", "%m/%d/%Y %H:%M:%S").replace(tzinfo = tz_used)
    full_year_times = \
                [(start_date + rdatetime.timedelta(hours = n)) for n in range(8760)]
    data, desc = qload("temps_"+facility+".pkl",loc="")
    full_temps, temps_oriflag = fill_in(data,full_year_times)
    temp_times, temp_vals = zip(*full_temps)
    temps = (np.array(temp_vals), np.array(temps_oriflag))
    
    
    dataagg, descagg = qload("state_b_records_2011_with_temps.pkl",loc = "")
    #for k in range(len(toadd)-1):
    #    data[k+1]['temps'] = toadd[k]
    #    print "Changed ------", k+1
    #qdump((data,desc),"state_b_records_2011_with_temps.pkl",loc="")

            
def toadd_to_building_pkls(data,k):
    start_date   = datetime.strptime("1/1/2011 00:00:00", "%m/%d/%Y %H:%M:%S").replace(tzinfo = tz_used)
    full_year_times = \
                [(start_date + rdatetime.timedelta(hours = n)) for n in range(8760)]
    toadd, desctemp = qload("temps_"+k+".pkl",loc=data_loc + '2011/')
    ### fix it
    #times, tempe = zip(*toadd)
#    temp = {}
#    for date, number in toadd:
#        if date not in temp: # we see this key for the first time
#            temp[date] = (date, number)
#    result = temp.values()
    result = list(set(toadd)).sorted()
    
    full_temps, temps_oriflag = fill_in(result,full_year_times)
    temp_times, temp_vals = zip(*full_temps)
    temps = (np.array(temp_vals), np.array(temps_oriflag))
    return data        
    
    
        

if __name__== "__main__":
    facilities = {'1636483694' :'Danville',
                  '1988756172' :'Galesburg',
                  '2550170006' :'Vienna',
                  '5379783532' :'Pinckneyville'}
    data, desc = qload("state_b_records_2011_with_temps.pkl",loc = data_loc)
    for k in facilities:
        data = toadd_to_building_pkls(data,k)
    qdump((data,desc),"state_b_records_2011_with_temps.pkl",loc=data_loc)
                  
                  