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
GIS_file = file_dir + '/Dams_Japan_JDF' 
this_coutry = 'Japan'

#======================================================================================


#======================================================================================
# CODE
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
    arcpy.AddField_management(GIS_file, 'reg_string', "TEXT") #field_length=255 by default, which should be good

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
    
    this_dam_name = each_record.dam_name #string
    if this_dam_name is None:
        this_dam_name = ''
    else:
        this_dam_name = this_dam_name.strip()
        
    this_year_start = each_record.yr_start #string
    if this_year_start is None:
        this_year_start = ''
    else:
        this_year_start = this_year_start.strip()
        
    this_year_complete = each_record.yr_complete #string
    if this_year_complete is None:
        this_year_complete = ''
    else:
        this_year_complete = this_year_complete.strip()
    
    this_reservoir_area = each_record.surface_area_ha #string
    if this_reservoir_area is None:
        this_reservoir_area = ''
    else:
        this_reservoir_area = this_reservoir_area.strip()
        if this_reservoir_area != '':
            this_reservoir_area = 0.01*float(this_reservoir_area) #ha to km2 -----------------------------------------------------------------
            this_reservoir_area = str(format(this_reservoir_area, ".4f"))  #keep 4 decimal digits
        
    this_reservoir_cap = each_record.res_cap_tm3 #string
    if this_reservoir_cap is None:
        this_reservoir_cap = ''
    else:
        this_reservoir_cap = this_reservoir_cap.strip()
        if this_reservoir_cap != '':
            this_reservoir_cap = 0.001*float(this_reservoir_cap) #tm3 to mcm -----------------------------------------------------------------
            this_reservoir_cap = str(format(this_reservoir_cap, ".4f"))      
        
    this_string = ''
    if this_dam_name != '':
        this_string = this_string + this_dam_name + " (reg dam); "
    if this_coutry != '':
        this_string = this_string + this_coutry + " (reg cntry); " 
    if this_year_start != '':
        this_string = this_string + this_year_start + " (reg year_start); "     
    if this_year_complete != '':
        this_string = this_string + this_year_complete + " (reg year_complete); "    
    if this_reservoir_area != '':
        this_string = this_string + this_reservoir_area + " (reg area_km2); " 
    if this_reservoir_cap != '':
        this_string = this_string + this_reservoir_cap + " (reg cap_mcm); " 
    
    this_string = this_string + this_ID + " (reg ID)"

    each_record.reg_string = this_string
    
    all_records.updateRow(each_record)
del all_records # Release the cursor
del each_record
