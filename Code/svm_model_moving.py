import numpy as np
import cPickle as pickle
from utils import *
from model_matrix import *
from getSunny import *
from holiday import *
import matplotlib.pyplot as plt
from sklearn import svm
from sklearn.svm import SVR
from sklearn import preprocessing, metrics, grid_search
from sklearn.metrics import recall_score, precision_score, mean_squared_error, r2_score
import  pytz
utc_tz  = pytz.utc
tz_used = pytz.timezone("US/Central")



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
#    if ds is not None:
#        x_sun=np.array([getSun("IL",array_times[i][-1]) for i in range(num_rows)])
#        x = np.concatenate((x,x_sun.reshape(len(x_sun),-1)),axis=1)
#        names.append("sun")
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
    return [y, x, array_times, names]
    


# grid search - method to identify the best hyperparameters out of an intelligent set
parameters = {'kernel':('linear','rbf','poly'), 'C':[40,60,80]}
            # 'degree':[1,2,3], 'gamma':[0, 0.5, 1]}
              
svr = svm.SVR()
clf = grid_search.GridSearchCV(svr, parameters)

def window(start_date, hrs_train, hrs_test):  
    """ 
    defines the train and test period 
    start_date --> the start of the training period, as a naive datetime object
    hrs_train  --> the number of hours to train on 
    hrs_test   --> the number of hours to test
    """
    subset={}
    start=start_date.replace(tzinfo = tz_used)
    i1 = np.where(data['times']==start)
    subset['naics']=data['naics']
    subset['kwhs']=(data['kwhs'][0][i1[0][0]:i1[0][0]+hrs_train],data['kwhs'][1][i1[0][0]:i1[0][0]+hrs_train])
    subset['bid']=data['bid']
    subset['times']=data['times'][i1[0][0]:i1[0][0]+hrs_train]
    subset['temps']=(data['temps'][0][i1[0][0]:i1[0][0]+hrs_train],data['temps'][1][i1[0][0]:i1[0][0]+hrs_train])
    subset['btype']=data['btype']    
    return subset

if __name__ == "__main__":
    # Load the dataset
    data, desc = qload("agentis_oneyear_22891_updated.pkl",loc="D:/DSSG/Data/")    
    s1 = datetime.datetime(2011, 1, 2, 0, 0)
    # train on 1 month of data
    num_train = 672
    # predict 1 week
    num_test = 168
    
    # nr of complete weeks in subset
    counter = int(num_train/168)
    
for i in range(counter):  
    s1 = s1 + datetime.timedelta(hours=168*i)
    print s1
    # define window of data
    subset = window(s1, num_train, num_test)       
    mdata=mat_from_building_pkl(subset,md=4,dt=3,dw=1,td=1)
    ## why is the length 668?
        
    # StandardScaler computes the mean and standard deviation on a training set 
    # so as to be able to later reapply the same transformation on the testing set
    scaler = preprocessing.StandardScaler()
    scaler_x = scaler.fit(x_train)
    scaler_y = scaler.fit(y_train)
    
    x_train_norm = scaler_x.transform(x_train)
    x_test_norm  = scaler_x.transform(x_test)
    
    y_train_norm = scaler_y.transform(y_train)
    y_test_norm  = scaler_y.transform(y_test)
    
    # fit models to train data
    model = clf.fit(x_train_norm, y_train_norm, cv=2)
    
    # predict y from test data
    y_pred_norm = clf.predict(x_test_norm)
    y_pred = scaler_y.inverse_transform(y_pred_norm)
    
    scores = [
        ('precision', precision_score),
        ('recall', recall_score),
    ]
    
    for score_name, score_func in scores:
        print "# Tuning hyper-parameters for %s" % score_name
        print
        print "Best parameters set found on development set:"
        print
        print clf.best_estimator_
        print
        print "Grid scores on development set:"
        print
        for params, mean_score, scores in clf.grid_scores_:
            print "%0.3f (+/-%0.03f) for %r" % (
                mean_score, scores.std() / 2, params)
















