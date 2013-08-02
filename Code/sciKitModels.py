import numpy as np
from sklearn import linear_model, metrics
from model_matrix import *
from utils import *
import matplotlib.pyplot as plt
from sklearn import svm
from sklearn.svm import SVR
from sklearn import preprocessing
from sklearn import cross_validation
from sklearn.cross_validation import KFold

# use statsmodels
# ragged array (not square/cube) in tuned_parameters 
# because for rbf take 3.. for linear, use less.

# precision = of all times you said true, what % was true
# recall = of all the ones you can say true on, how many did you say true on
# 1000 data points
# 750 actually true
# 500 estimated true
# precision= of the 500 estimated true, how many were actually true? interseection
# recall = of the 500 estimated true, how many were true = 500/750
# cv = cross validation
# cv=5 is 5 fold validation
# get 5 data sets, delete 20% of each, train a model for the remainder 
# and see how well the prediciton is for the missing 20% values
# this avoids overfitting
# clf.best_estimator_ = the spot in our grid that did the best
# grid_scores is what the whole grid did
# http://scikit-learn.org/0.13/auto_examples/grid_search_digits.html#example-grid-search-digits-py
# grid is a list of dictionaries
# weights = how to incorporate that peaks are most important?


"""fits a linear model with coefficients to minimize the residual sum of squares 
   between the observed responses in the dataset, and the responses predicted by
   the linear approximation. """
   
""" split the data set into train & test, 3 quarters trained to predict 4th quarter"""

# Load the dataset
data, desc = qload("agentis_oneyear_22891_updated.pkl",loc="")
mdata=mat_from_bld_pkl(data,md=4,dt=3,ds=1,dw=1,h=1,td=1)

num_train=4000
num_test=168

train_X = mdata[1][:num_train]
train_Y = mdata[0][:num_train]

test_X = mdata[1][num_train:num_train+num_test]
test_Y = mdata[0][num_train:num_train+num_test]

clf = linear_model.LinearRegression()
clf.fit(train_X,train_Y)
clf.score(test_X, test_Y)
preds = clf.predict(test_X)


clf = svm.SVC(kernel='linear', C=1).fit(train_X, train_Y)
clf.score(test_X, test_Y)
scores = cross_validation.cross_val_score(clf, train_X, train_Y, cv=5)


# 1 plot
plt.figure(figsize = (10,10))
plt.plot(range(num_test), preds, label = "preds")
plt.plot(range(num_test), test_Y, label = "actual")
plt.legend()
plt.show()


# 3 figures
# subplot(x=nrRows,y=nrColumns,z=nrOrder) 
fig = plt.figure(figsize = (10,10))
ax2 = fig.add_subplot(3, 1, 1)
# plot 1/3
ax1.plot(range(num_test), preds, label = "preds")
ax1.plot(range(num_test), test_Y, label = "actual")
ax1.scatter(range(len(mdata[2])), clf.coef_)
ax1.legend()

# plot 2/3
ax2 = fig.add_subplot(3, 1, 2)
ax2.scatter(range(len(mdata[2])), clf.coef_)
ax2.set_xticks(range(len(mdata[2])))
ax2.set_xticklabels(mdata[2])

labels = ax.get_xticklabels()
for label in labels:
        label.set_rotation(30)
        
# plot 3/3
ax3 = fig.add_subplot(3, 1, 3)
ax3.scatter(test_Y, preds - test_Y)
plt.show()


print metrics.mean_absolute_error(test_Y, preds), "MAD"
print metrics.mean_square_error(test_Y, preds), "MSE"
print metrics.explained_variance_score(test_Y, preds), "EVR"
print metrics.r2_score(test_Y, preds), "normal R2"



""" k-fold cross validation
    The training set is split into k smaller sets
    A model is trained using of the folds as training data
    The resulting model is validated on the remaining part of the data
    The performance measure reported by k-fold cross-validation 
    is then the average of the values computed in the loop. """




    





