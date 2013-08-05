
## IL buildings dictionary
desc = "This dictionary includes static information about the 7,076 IL buildings."
buildings={}
fName="D:/DSSG/Data/ILdata/ILbuildings.csv"

file=open(fName,'r')
header = file.readline().split('|,')
for line in file:  
    fields = line[:-1].split('|,')
    bld_nr, bld_name, agency, facility = fields[:4]
    FCI, FCI_cost, RI, RI_cost = map(float,fields[4:8])
    sqft, yrConstructed, floors = fields[8:11]
    print fields
    bld_type, city, state, zipCode, construction_type, use, assessment=map(str,fields[11:])

    if bld_nr not in buildings:
        buildings[bld_nr]={
            "bld_name":         bld_name,
            "agency":           agency,
            "facility" :        facility,
            "FCI" :             FCI,
            "FCI_cost":         FCI_cost,
            "RI":               RI,
            "RI_cost":          RI_cost,
            "sqft":             sqft,
            "yrConstructed":    yrConstructed,
            "floors":           floors,
            "bld_type":         bld_type,/
            "city":             city,
            "state":            state,
            "zipCode":          zipCode,
            "construction_type":construction_type,
            "use":              use,
            "assessment":       assessment
            }         
file.close()
