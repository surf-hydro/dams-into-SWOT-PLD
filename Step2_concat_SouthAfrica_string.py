# [Description] ------------------------------
# Concatenating major variables in this data register into a string attribute

# Script by: Jida Wang, Kansas State University
# Initiated: Jan 18, 2022
# Last update: Jan 18, 2022
# Contact: jidawang@ksu.edu; gdbruins@ucla.edu
#---------------------------------------------

# INPUT directory
file_dir = r'D:\Research\Projects\SWOT\Dam_inventory_collection\Dam_harmonization\Dam_datasets\All_dams.gdb'
# files
GIS_file = file_dir + '/Dams_SouthAfrica_LRD2019' # input and output
this_coutry = 'South Africa' #--------------------------------------------------------------------------------

# dam_source needs to be added first
#======================================================================================


#======================================================================================
# CODE
#import urllib, csv, json, xlsxwriter, openpyxl
#import csv
#import operator
import arcpy, numpy, os
import numpy as np
from arcpy import env
from numpy import ndarray
from datetime import date

fieldList = arcpy.ListFields(GIS_file)    
fieldName = [f.name for f in fieldList]
if ('dam_UID' in fieldName) == False:
    arcpy.AddField_management(GIS_file, 'dam_UID', "TEXT")
if ('reg_string' in fieldName) == False:
    arcpy.AddField_management(GIS_file, 'reg_string', "TEXT", field_length = 500) #field_length=255 by default

#Update universal ID
all_records = arcpy.UpdateCursor(GIS_file)
for each_record in all_records:
    this_data_source = each_record.dam_source #in the format of "register_..."
    valid_data_source = this_data_source[9:]
    each_record.dam_UID = valid_data_source + '_' + str(int(each_record.dam_ID))
    all_records.updateRow(each_record)
del all_records # Release the cursor
del each_record
    
# concatenate string
all_records = arcpy.UpdateCursor(GIS_file)
for each_record in all_records:
        
    this_ID = each_record.dam_UID #string
    
    this_dam_name = each_record.Name_of_dam #string
    if this_dam_name is None:
        this_dam_name = ''
    else:
        this_dam_name = this_dam_name.strip()
    
    this_state = each_record.Province_code #string
    if this_state is None:
        this_state = ''
    else:
        this_state = this_state.strip()
        
    this_year_complete = each_record.Completion_date #double
    if this_year_complete is None:
        this_year_complete = ''
    else:
        this_year_complete = str(this_year_complete).strip()
    
    this_year_complete_alt = each_record.Completion_date_altered #double
    if this_year_complete_alt is None:
        this_year_complete_alt = ''
    else:
        this_year_complete_alt = str(this_year_complete_alt).strip()
        
    this_river = each_record.River_or_Watercourse #string
    if this_river is None:
        this_river = ''
    else:
        this_river = this_river.strip()
    
    this_town = each_record.Town_nearest #string
    if this_town is None:
        this_town = ''
    else:
        this_town = this_town.strip()
        
    this_reservoir_area = each_record.Surface_area__ha_ #double
    if this_reservoir_area is None:
        this_reservoir_area = ''
    else:
        #this_reservoir_area = this_reservoir_area.strip()
        if this_reservoir_area != '': #no negative values
            this_reservoir_area = 0.01*float(this_reservoir_area) #ha to km2 -----------------------------------------------------------------
            this_reservoir_area = str(format(this_reservoir_area, ".4f"))  #keep 4 decimal digits 

    this_reservoir_cap = each_record.Capacity__1000_cub_m_ #double 
    if this_reservoir_cap is None:
        this_reservoir_cap = ''
    else:
        #this_reservoir_cap = this_reservoir_cap.strip()
        if this_reservoir_cap != '':
            this_reservoir_cap = (10.0**(-3))*float(this_reservoir_cap) #1000 m3 to mcm -----------------------------------------------------------------
            this_reservoir_cap = str(format(this_reservoir_cap, ".4f"))               
        
    this_string = ''
    #dam, town, state, country, river, year, area, cap
    if this_dam_name != '':
        this_string = this_string + this_dam_name + " (reg dam); "
    if this_town != '':
        this_string = this_string + this_town + " (reg town); "    
    if this_state != '':
        this_string = this_string + this_state + " (reg state/province); "
    if this_coutry != '':
        this_string = this_string + this_coutry + " (reg cntry); " 
    if this_river != '':
        this_string = this_string + this_river + " (reg river); "     
    if this_year_complete != '':
        this_string = this_string + this_year_complete + " (reg year_complete); " 
    if this_year_complete_alt != '':
        this_string = this_string + this_year_complete_alt + " (reg year_complete_alt); "   
    if this_reservoir_area != '':
        this_string = this_string + this_reservoir_area + " (reg area_km2); " 
    #if this_reservoir_cap_gross != '':
    #    this_string = this_string + this_reservoir_cap_gross + " (reg cap_gross_mcm); " 
    if this_reservoir_cap != '':
        this_string = this_string + this_reservoir_cap + " (reg cap_mcm); " 
    
    this_string = this_string + this_ID + " (reg ID)"

    each_record.reg_string = this_string
    
    all_records.updateRow(each_record)
del all_records # Release the cursor
del each_record
