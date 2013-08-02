import calendar
from datetime import datetime, date

def cd(year,month,fdw,nwe):
    """ Receive the year, month, fixed day of week of holiday (0:6), number of
        weeks. 
        Returns day of the holiday for year in question."""
    #Define first day of the month & number of days in month
    fdm, ndm = calendar.monthrange(year,month)
    if nwe > 0:
        if fdm == fdw:
            day = 7 * (nwe - 1) + 1
        elif fdm >= fdw:
            day = 7 * nwe - (fdm - fdw - 1)           
        else:
            day = 7 * (nwe - 1) + (fdw - fdm + 1)
        return day
    elif nwe == -1:
        day = ndm - (date(year,month,ndm).weekday() - fdw)
        return day
    else:        
        print "Error in year ", year, " Month ", month
        
    
def yfhol(year):
    """ Recieve a year and calculates the federal holidays for it (as 
        defined by http://www.opm.gov/policy-data-oversight/snow-dismissal-procedures/federal-holidays/#url=2011
        Returns a dictionary of them"""
    # Keys either has a date when its a fixed holiday or a list with 
    # [month,fixed day,number of day in the month]=[month,fdw,nwe]
    keys = {'New Year\'s Eve':date(year,1,1), 'Birthday of Martin Luther King, Jr.' \
            :[1,0,3], 'Washington\'s Birthday':[2,0,3], 'Memorial Day':[5,0,-1], \
            'Independence Day':date(year,7,4), 'Labor Day':[9,0,1], \
            'Columbus Day':[10,0,2], 'Veterans Day':date(year,11,11), \
            'Thanksgiving Day':[11,3,4], 'Christmas Day':date(year,12,25)}
    #[cd(year,keys[k][0],keys[k][1],keys[k][2]), for k in keys if isinstance(keys[k],list)]
    for k in keys:
        if isinstance(keys[k],list):
            #print k
            day = cd(year,keys[k][0],keys[k][1],keys[k][2])
            keys[k] = date(year,keys[k][0],day)
            #print keys[k]   
    return keys
    
def is_hol(date):
    """Recieve a date.
       Returns True if holiday."""
    if isinstance(date,datetime):
        date=date.date()
    hols = yfhol(date.year)
    if date in hols.values():
        return True
    else:
        return False
    
if __name__ == "__main__":
    d=datetime.now()
    d1=date(2013,11,28)
    d2=datetime(2013,11,28,12,20,30)
    #print is_hol(d1)
    #print is_hol(d2)
    #print is_hol(d)
    print yfhol(2015)
    
    
