from utils import qdump
import csv

fName='2012_NAICS_Structure.csv'
desc = "This dictionary maps 2012 NAIC codes to a description."    

if __name__=="__main__":
    NAICS = {}
    reader = csv.reader(open(fName, "rb"))
    header = reader.next()
    for rows in reader:
        k = rows[0][:-1]
        v = rows[1]
        NAICS[int(k)] = v

    qdump((NAICS, desc),'NAICS.pkl', loc = '/home/csimoiu/')




    