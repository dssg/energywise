import cPickle


file=open('D:/DSSG/Data/SICdescription.csv','r') 
#file=open('/home/csimoiu/Data/States.csv','r') 
header=file.readline()      
SIC={}
for line in file:
    fields=line[:-1].split(',')
    code=fields[0]
    descrip=fields[1:][0]
    print code, descrip
    if code not in SIC:
        SIC[code]=descrip


# format: SIC['code']
cPickle.dump(SIC,open('D:/DSSG/Data/SICdescrip.pickle','w'))
SIC=cPickle.load(open('SICdescrip.pickle','r'))    
   


    
