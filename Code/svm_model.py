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
from sklearn.metrics import classification_report, recall_score, precision_score, mean_squared_error, r2_score


# Load the dataset
data, desc = qload("agentis_oneyear_22891_updated.pkl",loc="D:/DSSG/Data/")
mdata=mat_from_building_pkl(data,md=4,dt=3,dw=1,td=1)

# split data into train & test groups
# train on 3 months of hourly data
# test on 1 week
hrs_wk = 168
nr_wks = 3*4
num_train = hrs_wk * nr_wks
num_test = hrs_wk
    
# grid search - method to identify the best hyperparameters out of an intelligent set
parameters = {'kernel':('linear','rbf','poly'), 'C':[0.5,1,2,3,4,5,6,7,8,9,10],
              'degree':[1,2,3]} #'gamma':[0, 0.5, 1]}
svr = svm.SVR()
clf = grid_search.GridSearchCV(svr, parameters)


# cross validation - method to measure performance
x_train = mdata[1][:num_train]
y_train = mdata[0][:num_train]

x_test = mdata[1][num_train:num_train+num_test]
y_test = mdata[0][num_train:num_train+num_test]

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
model = clf.fit(x_train_norm, y_train_norm, cv=5)

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



plt.figure(figsize = (10,10))
plt.plot(range(num_test), y_pred, label = "preds")
plt.plot(range(num_test), y_test, label = "actual")
plt.legend()
plt.show()


#if __name__ == "__main__":
    


    





