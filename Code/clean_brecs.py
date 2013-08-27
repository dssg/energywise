from utils import *
import sys

def clean_rec(d):
    kwhs, kwhs_oriflag   = d["kwhs"]
    temps, temps_oriflag = d["temps"]
    for i in range(len(temps_oriflag)):
        t = temps[i]
        if t < -60:
            temps_oriflag[i] = False #Ain't no way that reading's real
            temps[i] = 0
    for i in range(len(kwhs_oriflag)):
        k = kwhs[i]
        if k < -5:
            kwhs_oriflag[i] = False #Ain't no way that reading's real
            kwhs[i] = 0
    d["temps"] = (temps, temps_oriflag)
    d["kwhs"] = (kwhs, kwhs_oriflag)
      
if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1:
        the_year = int(args[1])
    
    brecs, desc = qload("state_b_records_" + str(the_year) + "_updated_with_temps.pkl")
    for d in brecs:
        clean_rec(d)
    qdump((brecs, desc + "(Plus we cleaned out curiously low values (noise))"),
          "state_b_records_" + str(the_year) + "_with_temps_cleaned.pkl")
