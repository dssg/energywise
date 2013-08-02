from utils import qdump
import csv

path = '/home/csimoiu/Data/'
fName= 'correctionalFacilities_7.csv'
desc = "This dictionary contains static features of the 7 cookie cutter correctional facilities."    

if __name__=="__main__":
    staticFeatures = {}
    reader = csv.reader(open(path+fName, "rb"))
    header = reader.next()
    for rows in reader:
        name = rows[0]
        AccNo =rows[1]
        acc =rows[2]
        t = rows[3]
        opened =rows[4]
        operational_capacity =rows[5]
        current_pop =rows[6]
        av_age =rows[7]
        av_cost_per_inmate =rows[8]
        city =rows[9]
        nrBuildings =rows[10]
        building_size =rows[11]
        total_land =rows[12]
        fenced =rows[13]
        X_design_housing_units=rows[14]
        T_type_housing_units=rows[15]
        receiving_orientation_units=rows[16]
        admin_buidling=rows[17]
        segregation_units =rows[18]
        health_care_units =rows[19]
        other_buildings =rows[20]
        address =rows[21]
        industry_1 =rows[22]
        industry_2 =rows[23]
        industry_3 =rows[24]
        industry_4 =rows[25]
        industry_5 =rows[26]
        industry_6 =rows[27]
        if acc not in staticFeatures:
            staticFeatures[acc]={}
            staticFeatures[acc]['name']=name
            staticFeatures[acc]['opened']=opened
            staticFeatures[acc]['operational_capacity']=operational_capacity
            staticFeatures[acc]['current_pop']=current_pop
            staticFeatures[acc]['av_age']=av_age
            staticFeatures[acc]['av_cost_per_inmate']=av_cost_per_inmate
            staticFeatures[acc]['city']=city
            staticFeatures[acc]['nrBuildings']=nrBuildings
            staticFeatures[acc]['building_size']=building_size
            staticFeatures[acc]['total_land']=total_land
            staticFeatures[acc]['fenced']=fenced
            staticFeatures[acc]['X_design_housing_units']=X_design_housing_units
            staticFeatures[acc]['T_type_housing_units']=T_type_housing_units
            staticFeatures[acc]['receiving_orientation_units']=receiving_orientation_units
            staticFeatures[acc]['admin_buidling']=admin_buidling
            staticFeatures[acc]['segregation_units']=segregation_units
            staticFeatures[acc]['health_care_units']=health_care_units
            staticFeatures[acc]['other_buildings']=other_buildings
            staticFeatures[acc]['address']=address
            staticFeatures[acc]['industry_1']=industry_1
            staticFeatures[acc]['industry_2']=industry_2
            staticFeatures[acc]['industry_3']=industry_3
            staticFeatures[acc]['industry_4']=industry_4
            staticFeatures[acc]['industry_5']=industry_5
            staticFeatures[acc]['industry_6']=industry_6    
    
  
        qdump((staticFeatures, desc),'prisonFeatures.pkl', loc = '/mnt/energy_data/pickleFiles/')
    
    
    
    
        