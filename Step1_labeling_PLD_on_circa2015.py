# [Description] ------------------------------
# Labeling SWOT PLD lakes (a subset of circa-2015 lakes) on circa-2015 lakes

# Script by: Jida Wang, Kansas State University
# Initiated: Jan 13, 2022
# Last update: Jan 13, 2022
# Contact: jidawang@ksu.edu; gdbruins@ucla.edu
#---------------------------------------------

# [Setup] -----------------------------------
work_dir = r"E:\SWOT_PLD_20211103\SWOT_PLD_full_dataset"
#circa2015 = r"D:\Research\Projects\SWOT\Dam_inventory_collection\Dam_harmonization\Auxiliary_datasets\Lakes\SWOT_Lakes_AllUCLA2015.gdb\circa2015_UCLA_lakes". relocated to below:
circa2015 = r"E:\SWOT_PLD_20211103\SWOT_PLD_v01.gdb\circa2015_UCLA_lakes"
selection_relation = "SHARE_A_LINE_SEGMENT_WITH" #"INTERSECT" # "SHARE_A_LINE_SEGMENT_WITH"
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

for layer_i in ["01","02","03","04","05","06","07","08","09"]:
    PLD = "SWOT_PLD_pfaf_" + layer_i + ".shp"  
    print('processing ' + PLD + '... using ' + selection_relation)
    
    arcpy.MakeFeatureLayer_management(PLD, "PLD_lyr")
    PLD_count = int(arcpy.GetCount_management("PLD_lyr").getOutput(0))
    
    arcpy.MakeFeatureLayer_management(circa2015, "circa2015_lyr")
    arcpy.SelectLayerByLocation_management("circa2015_lyr", selection_relation, "PLD_lyr")
    selected_count = int(arcpy.GetCount_management("circa2015_lyr").getOutput(0))
    
    print('PLD count : selected count ... ' + str(PLD_count) + ' : ' + str(selected_count))

    if selected_count > 0:
        selected_records = arcpy.UpdateCursor("circa2015_lyr")
        for selected_record in selected_records:
            if selection_relation == "INTERSECT":
                selected_record.inter_PLDv01 = 1
            else:
                selected_record.shareseg_PLDv01 = 1
            selected_records.updateRow(selected_record)
        del selected_record # Release the cursor
        del selected_records

    arcpy.SelectLayerByAttribute_management("circa2015_lyr", "CLEAR_SELECTION")
    print('')
    
print("----- Module Completed -----")
print(datetime.datetime.now())
