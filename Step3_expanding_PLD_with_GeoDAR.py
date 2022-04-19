# [Description] ------------------------------
# This module appends GeoDAR reservoir polygons that do not intersect with PLD_circa2015_combined into a new layer, 
# and then updates lake_UID (for appended reservoirs, lake_UID will be GeoDAR IDs). 
# This updated coded is recommended because it avoids the case where two features intersect only by shared boundary or vertices. 

# Script by: Jida Wang, Kansas State University
# Initiated: Feb. 26, 2022
# Last update: Feb. 26, 2022
# Contact: jidawang@ksu.edu; gdbruins@ucla.edu
#---------------------------------------------


#======================================================================================
# [Setup] -----------------------------------
# Inputs
# work_dir: working space
work_dir = r"D:\Research\Projects\SWOT\Dam_inventory_collection\Dam_harmonization\Auxiliary_datasets\Lakes\SWOT_PLD_v01.gdb"

# Water_original: original water polygons
PLD = "PLDv01_circa2015"
#GeoDAR = "D:\Research\Projects\SWOT\Dam_inventory_collection\Dam_harmonization\Dam_datasets\All_dams.gdb\GeoDARv11_01182022_reservoirs" #for Japan only
GeoDAR = "D:\Research\Projects\SWOT\Dam_inventory_collection\Dam_harmonization\Dam_datasets\All_dams.gdb\GeoDAR_v11_reservoirs_internal_simple" 
#for non-Japan region (here I used the final v11_ID)

#PLD_output = "PLDv01_circa2015_GeoDARv1101182022" #now used only for Japan
PLD_output = "PLDv01_circa2015_GeoDARv11" #now used only for non-Japan region
#---------------------------------------------



# [Script] -----------------------------------
# Import built-in functions and tools.
import arcpy, numpy, os
import numpy as np
from arcpy import env
from numpy import ndarray
from datetime import date

print("----- Module Started -----")
print(datetime.datetime.now())

# Define environment settings.
env.workspace = work_dir
env.overwriteOutput = "TRUE"

#Intersect GeoDAR with PLD and write non-interselcted GeoDAR into PLD. 
arcpy.MakeFeatureLayer_management(PLD, "PLD_lyr")
arcpy.MakeFeatureLayer_management(GeoDAR, "GeoDAR_lyr")
#Intersect the two layers
arcpy.Intersect_analysis(["PLD_lyr", "GeoDAR_lyr"], "intersect_1")
print('intersection completed...')

#Retrieve all "GeoDARv11_ID"
all_GeoDARv11_ID_array = []
dam_records = arcpy.SearchCursor('GeoDAR_lyr')
for dam_record in dam_records:
    all_GeoDARv11_ID_array.append(dam_record.GeoDARv11_ID)
del dam_record
del dam_records
unique_GeoDARv11_ID_array = list(set(all_GeoDARv11_ID_array))

#Retrieve intersected GeoDARv11_ID
intersected_GeoDARv11_ID_array = []
dam_records = arcpy.SearchCursor("intersect_1")
for dam_record in dam_records:
    intersected_GeoDARv11_ID_array.append(dam_record.GeoDARv11_ID)
del dam_record
del dam_records
unique_intersected_GeoDARv11_ID_array = list(set(intersected_GeoDARv11_ID_array))

#Find the remaining GeoDARv11_IDs
for this_GeoDARv11_ID in unique_GeoDARv11_ID_array:
    if this_GeoDARv11_ID not in unique_intersected_GeoDARv11_ID_array:       
        SQL_dam = """{0} = '{1}'""".format(arcpy.AddFieldDelimiters("GeoDAR_lyr", "GeoDARv11_ID"), this_GeoDARv11_ID) #identical side from GeoDAR
        arcpy.SelectLayerByAttribute_management("GeoDAR_lyr", "ADD_TO_SELECTION", SQL_dam)

#Merge into a new PLD
arcpy.Merge_management (["PLD_lyr", "GeoDAR_lyr"], PLD_output)
arcpy.SelectLayerByAttribute_management("GeoDAR_lyr", "CLEAR_SELECTION")
print('merging completed...')

#Write GeoDARv11_ID into lake_UID
arcpy.MakeFeatureLayer_management(PLD_output, "PLD_output_lyr")
SQL_dam = """{0} IS NULL""".format(arcpy.AddFieldDelimiters("PLD_output_lyr", "lake_UID"))
arcpy.SelectLayerByAttribute_management("PLD_output_lyr", "NEW_SELECTION", SQL_dam)

dam_records = arcpy.UpdateCursor('PLD_output_lyr')
for dam_record in dam_records:
    dam_record.lake_UID = dam_record.GeoDARv11_ID
    dam_records.updateRow(dam_record)
del dam_record
del dam_records

arcpy.SelectLayerByAttribute_management("PLD_output_lyr", "CLEAR_SELECTION")

##then manually delete the GeoDAR fieldsL ID_v11, plg_src, Hylak_id, and GeoDARv11_ID. previously for Japan only.
##then manually delete the GeoDAR fieldsL GeoDARv11_ID.

print("----- Module Completed -----")
print(datetime.datetime.now())
