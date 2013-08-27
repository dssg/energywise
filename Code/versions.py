from    holiday import *
import  utils
import  report_card

import  datetime
import  pytz
import  csv
import  cPickle as pickle
import  datetime
import  ephem # run `pip install pyephem`
import  os
import  collections
import  string
import  time
import  cPickle as pickle
import  numpy as np
import  pytz
import  datetime
import  string
import  time
import  numpy as np
import  dateutil
import  pytz
import  sys
import  matplotlib
import  heapq
import  datetime
import  math
import  calendar
import  sklearn
import  copy
import  warnings
import  collections
import  random
import  scipy

def print_versions():
    import types
    import sys
    print "Python version:\n\t", sys.version, "\n"
    unversioned = []
    print "Modules with __version__:"
    for val in globals().values():
        if isinstance(val, types.ModuleType):
            try:
                ver = val.__version__
                print "\t%s %s" %((val.__name__ + ":").ljust(15), ver.rjust(10))
            except:
                unversioned.append(val.__name__)

    print "\nModules with no __version__:"
    for mod in unversioned:
        print "\t%s" % mod

print_versions()
