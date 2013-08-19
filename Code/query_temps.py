# Lets try with temperatured
import urllib2
import json
import  numpy as np
import  pytz
import  datetime as rdatetime
import time
from    datetime import datetime
from   dateutil import tz
from utils import fill_in, qdump, qload

tz_used = pytz.timezone("US/Central")
only_one_year = True
key = 'http://api.wunderground.com/api/'

def _add_day(parsed_json,info,locd,utcd):    
    for j in range(len(parsed_json[u'history'][u'observations'])):
        [info[k].append(parsed_json[u'history'][u'observations'][j][k]) for k in info]
        locd.append(datetime(int(parsed_json[u'history'][u'observations'][j][u'date'][u'year']),\
                    int(parsed_json[u'history'][u'observations'][j][u'date'][u'mon']), \
                    int(parsed_json[u'history'][u'observations'][j][u'date'][u'mday']), \
                    int(parsed_json[u'history'][u'observations'][j][u'date'][u'hour']), \
                    0, \
                    tzinfo=pytz.timezone(parsed_json[u'history'][u'observations'][j][u'date'][u'tzname'])))
        utcd.append(datetime(int(parsed_json[u'history'][u'observations'][j][u'utcdate'][u'year']),\
                    int(parsed_json[u'history'][u'observations'][j][u'utcdate'][u'mon']), \
                    int(parsed_json[u'history'][u'observations'][j][u'utcdate'][u'mday']), \
                    int(parsed_json[u'history'][u'observations'][j][u'utcdate'][u'hour']), \
                    int(parsed_json[u'history'][u'observations'][j][u'utcdate'][u'min']), \
                    tzinfo=pytz.timezone(parsed_json[u'history'][u'observations'][j][u'utcdate'][u'tzname'])))

def query_temps(facility,city,country,state,year,llaves,usedkey,conta):
    
    info = {u'heatindexm': [], u'windchillm': [], u'wdire': [], u'wdird': [], \
            u'windchilli': [], u'hail': [], u'heatindexi': [], u'precipi': [], \
            u'thunder': [], u'pressurei': [], u'snow': [], u'pressurem': [], \
            u'fog': [], u'icon': [], u'precipm': [], u'conds': [], u'tornado': [], \
            u'hum': [], u'tempi': [], u'tempm': [], u'dewptm': [], u'rain': [], \
            u'dewpti': [], u'visi': [], u'vism': [], u'wgusti': [], u'metar': [], \
            u'wgustm': [], u'wspdi': [], u'wspdm': []}
    locd = []
    utcd = []
    # Make a vector of all times
    start_date   = datetime.strptime("1/1/2011 00:00:00", "%m/%d/%Y %H:%M:%S").replace(tzinfo = tz_used)
    #full_year_times = \
    #            [(start_date + rdatetime.timedelta(hours = n)) for n in range(8760)]
    full_year_times = \
                [(start_date + rdatetime.timedelta(hours = n)) for n in range(8760)]
    #facility = '0579171006'
    #city = "Mount_Sterling"
    #country = "US"
    #state = "IL"
    #year = 2011
    
    i=0
    while i < len(full_year_times):
        if i%24 == 0:
            if full_year_times[i].month<10:
                mm = "0"+str(full_year_times[i].month)  
            else: 
                mm = str(full_year_times[i].month)
            if full_year_times[i].day<10:
                dd = "0"+str(full_year_times[i].day)  
            else: 
                dd = str(full_year_times[i].day)
            if conta > 500:
                conta = 1
                usedkey = llaves[llaves.index(usedkey) + 1]     
            url = key+usedkey+"history_"+str(year)+mm+dd+"/q/"+state+"/"+city+".json"
            try:
                f = urllib2.urlopen(url)
                json_string = f.read()
                parsed_json = json.loads(json_string)
                f.close()
                _add_day(parsed_json,info,locd,utcd)
                i+=1
                conta+=1
                print i
                time.sleep(2)
            except:
                time.sleep(60)
                continue
        else:
            i+=1
    temp = [float(k) for k in info[u'tempi']]
    temptemp = zip(locd,temp)    
    #full_temps, temps_oriflag = fill_in(zip(locd,temp),full_year_times)
    #temp_times, temp_vals = zip(*full_temps)
    #temps = (np.array(temp_vals), np.array(temps_oriflag))
    qdump(([info,locd,utcd],\
    "All historic info from wunderground for facility "+facility+"_"+city+"_"+state+"_"+str(year)),facility+'.pkl',loc="")
    qdump((temptemp,
    "Queried temperatures in farenheit from wunderground for facility "+facility+"_"+city+"_"+state+"_"+str(year)),"temps_"+facility+".pkl",loc="")
    return [temptemp,llaves,usedkey,conta]
    
if __name__ == "__main__":
    #facilities = {'0579171006' :'Mount_Sterling',
    llaves = ['c85a2fe3856c8df6/','a82796c0c86b97c5/','a3b0690f10aa5f74/']
    #facilities = {'0579171006' :'Mount_Sterling',
    facilities = {'1636483694' :'Danville'}
    #              '1988756172' :'Galesburg',
    #              '2550170006' :'Vienna',
    #              '5379783532' :'Pinckneyville'}
    country = "US"
    state = "IL"
    year = 2012
    usedkey = llaves[0]
    conta = 1
    toadd = []
    for k in facilities:
        facility = k
        city = facilities[k]
        country = "US"
        state = "IL"
        year = 2011
        temps,llaves,usedkey,conta=query_temps(facility,city,country,state,year,llaves,usedkey,conta)
        toadd.append(temps)
    qdump((toadd,"Temporal con las 5 prisiones"),"toadd.pkl",loc="")
    #data, desc = qload("state_b_records_2011_with_temps.pkl",loc = "")
    #print desc
    #for k in range(len(toadd)-1):
    #    data[k+1]['temps'] = toadd[k]
    #    print "Changed ------", k+1
    #qdump((data,desc),"state_b_records_2011_with_temps.pkl",loc="")
        
        
    
#print "Len full_year_times-----", len(full_year_times)
#print "len of times in json----", len(locd)
#print "len info ---------------", len(info)
#print "len tempi in info-------", len(info[u'tempi'])   
#print "temps ----------------------------"
#print info[u'tempi']
#print "times ----------------------------"
#print full_year_times
#print "utc times json--------------------"
#print locd



#hour=[]
#[hour.append(parsed_json[u'history'][u'observations'][i][u'date'][u'hour']) for i in range(len(parsed_json[u'history'][u'observations']))]

#heatindexm = []
#[heatindexm.append(parsed_json[u'history'][u'observations'][i][u'heatindexm']) \
#    for i in range(len(parsed_json[u'history'][u'observations']))]
##Stand alone script that you run from the command line and you give it a query (dates) and it gives you all of the information for those dates in an hourly format

