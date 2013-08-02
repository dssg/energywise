import cPickle
import datetime
import ephem # run `pip install pyephem`


#file=open('D:/DSSG/code/States.csv','r') 
file=open('/home/csimoiu/Data/States.csv','r') 
header=file.readline()      
states={}
for line in file:
    fields=line[:-1].split(',')
    name,ab,cap=fields[:3]
    zone=fields[8]
    timeZone=zone.split(' ')[0]
    if ab not in states:
        states[ab]={}
        states[ab]['capital']=cap
        states[ab]['fullName']=name.capitalize()
        states[ab]['timeZone']=timeZone
    

#file=open('D:/DSSG/Data/NationalFedCodes.txt','r')
file=open('/home/csimoiu/Data/NationalFedCodes.txt','r') 
header=file.readline().split('|')       
for line in file:
    fields=line[:-1].split('|')
    stateAB=fields[8]
    city=fields[1]
    lat=fields[-4]
    lon=fields[-3]
    try:
        states[stateAB][city]=(lat,lon)
    except:
        pass
  

cPickle.dump(states,open('stateDB.pickle','w'))
states=cPickle.load(open('stateDB.pickle','r'))    
   


    
