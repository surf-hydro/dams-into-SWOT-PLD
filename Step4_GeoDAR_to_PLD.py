# [Description] ------------------------------
# This module associate GeoDAR IDs with PLD polygons. 

# note: For GeoDAR polygons that do not intersect with PLDv11_circa2015, I've already appended them to PLDv11_circa2015, 
# and lake_UID equals to geoDAR ID. For these dams (done in #step 3).  

# Script by: Jida Wang, Kansas State University
# Initiated: Feb. 27, 2022
# Last update: Feb. 27, 2022
# Contact: jidawang@ksu.edu; gdbruins@ucla.edu
#---------------------------------------------




# [Setup] -----------------------------------
# Inputs
# work_dir: working space
work_dir = r"D:\Research\Projects\SWOT\Dam_inventory_collection\Dam_harmonization\Auxiliary_datasets\Lakes\SWOT_PLD_v01.gdb"

GeoDAR = r"D:\Research\Projects\SWOT\Dam_inventory_collection\Dam_harmonization\Dam_datasets\All_dams.gdb\GeoDAR_v11_reservoirs_internal_simple"

# Water_original: original water polygons
PLD = "PLDv01_circa2015_GeoDARv11_subset" #this is only the subset of the latter, which spatially intersects with GeoDAR to save computation
#PLD_full = "PLDv01_circa2015_GeoDARv11_edit" #a duplicate of PLDv01_circa2015_GeoDARv11. Use table join because doing this takes way too long. 
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
 
#Make feature layer
arcpy.MakeFeatureLayer_management(PLD, "PLD_lyr")
arcpy.MakeFeatureLayer_management(GeoDAR, "GeoDAR_lyr")

#Intersect the two layers
arcpy.Intersect_analysis(["PLD_lyr", "GeoDAR_lyr"], "intermediate_1")
print('intersection completed...')

# Retrieve GoDAR IDs
all_intersected_GeoDARv11_ID = []
all_intersected_lake_UID = []
all_intersected_area = []
unique_intersected_lake_UID = []
unique_intersected_GeoDARv11_ID = []
polygon_records = arcpy.SearchCursor("intermediate_1") # By default, cursor only takes effect for selected features.
for polygon_record in polygon_records:
    all_intersected_GeoDARv11_ID.append(polygon_record.GeoDARv11_ID)
    all_intersected_lake_UID.append(polygon_record.lake_UID)
    all_intersected_area.append(polygon_record.Shape_Area)
    
    if polygon_record.lake_UID not in unique_intersected_lake_UID:
        unique_intersected_lake_UID.append(polygon_record.lake_UID)
    if polygon_record.GeoDARv11_ID not in unique_intersected_GeoDARv11_ID:
        unique_intersected_GeoDARv11_ID.append(polygon_record.GeoDARv11_ID)
del polygon_record # Release the cursor
del polygon_records
print('GeoDAR IDs retrieved...')

# Generate unique PLD information (including joint count and jointed GeoDAR IDs)
unique_intersected_lake_UID_joint_count = [] #paprallel with unique_intersected_lake_UID!
unique_intersected_lake_UID_joint_GeoDAR_ID = []
unique_intersected_lake_UID_arearatio = []
for this_unique_lake_UID in unique_intersected_lake_UID:
    here_PLD_indices = [i for i, x in enumerate(all_intersected_lake_UID) if x == this_unique_lake_UID] #search from dam arrays. 
    
    this_unique_GeoDAR_IDs = [] #unique GeoDAR IDs for this PLD lake_UID polygon
    for this_PLD_index in here_PLD_indices:
        if all_intersected_GeoDARv11_ID[this_PLD_index] not in this_unique_GeoDAR_IDs:
            this_unique_GeoDAR_IDs.append(all_intersected_GeoDARv11_ID[this_PLD_index])  
    #this can be simply done by [all_intersected_GeoDARv11_ID[i] for i in here_PLD_indices] #these values are unique here. Check so: 
    if [all_intersected_GeoDARv11_ID[i] for i in here_PLD_indices] != this_unique_GeoDAR_IDs:
        print('this should not happen........... algorithm varies')
        #break
        #This can happen. This is because: very strangely, if there are two polygons nested within each other from the same source 
        #(circa 2015 has such an error: C15_3977065 C15_8349584 for lake_UID)
        # when they intersect with another polygon from another source, there will be three intersected polygons, instead of two...
        # This has been corrected from the original PLD file (no overlap any more!!)
    
    unique_intersected_lake_UID_joint_count.append(len(this_unique_GeoDAR_IDs))
    unique_intersected_lake_UID_joint_GeoDAR_ID.append(this_unique_GeoDAR_IDs[-1]) #use the last ID
    unique_intersected_lake_UID_arearatio.append(-1.0) #initiate the array
print('unique intersected lake UID retrieved')
  
# Retrieve original areas for each unique PLD polygon (only those that intersect with GeoDAR)
original_PLD_areas = []
original_PLD_lake_UID = []
polygon_records = arcpy.SearchCursor("PLD_lyr") # By default, cursor only takes effect for selected features.
for polygon_record in polygon_records:
    if polygon_record.lake_UID in unique_intersected_lake_UID:
        original_PLD_areas.append(polygon_record.Shape_Area)
        original_PLD_lake_UID.append(polygon_record.lake_UID)
del polygon_record # Release the cursor
del polygon_records
if len(original_PLD_lake_UID) != len(unique_intersected_lake_UID):
    print('This should not happen')
# Just in case, reorder it based on the order of unique_intersected_lake_UID
sorted_original_PLD_areas = [] #paprallel with unique_intersected_lake_UID!
for this_unique_lake_UID in unique_intersected_lake_UID:
    here_PLD_indices = [i for i, x in enumerate(original_PLD_lake_UID) if x == this_unique_lake_UID] #search from dam arrays. 
    if len(here_PLD_indices) != 1:
        print('this should not happen ..........')
    else:
        sorted_original_PLD_areas.append(original_PLD_areas[here_PLD_indices[0]])
print('sorted original PLD areas generated')

# Loop through each unique GeoDAR IDs. follow the sequence of unique_intersected_GeoDARv11_ID (in intersected result),
# but this sequence may not always follow the GeoDAR sequence. 
for this_unique_GeoDARv11_ID in unique_intersected_GeoDARv11_ID:
    here_GeoDAR_indices = [i for i, x in enumerate(all_intersected_GeoDARv11_ID) if x == this_unique_GeoDARv11_ID]
    
    withinGeoDAR_lake_UID = [all_intersected_lake_UID[i] for i in here_GeoDAR_indices] #these values are unique here. 
    
    # Collect the sum of the intersectied area
    sum_intersected_area = sum([all_intersected_area[i] for i in here_GeoDAR_indices])
    
    #Check the count of PLD for each of these lake_UID
    withinGeoDAR_lake_UID_joint_count = []
    withinGeoDAR_lake_UID_area = []
    for this_withinGeoDAR_lake_UID in withinGeoDAR_lake_UID: #this will be double counted if the values are not unique!
        index_1 = [i for i, x in enumerate(unique_intersected_lake_UID) if x == this_withinGeoDAR_lake_UID] 
        if len(index_1) != 1:
            print('this should not happen....')
        withinGeoDAR_lake_UID_joint_count.append(unique_intersected_lake_UID_joint_count[index_1[0]]) #only to check confidence
        withinGeoDAR_lake_UID_area.append(sorted_original_PLD_areas[index_1[0]])
    sum_withinGeoDAR_lake_UID_area = sum(withinGeoDAR_lake_UID_area)
    area_ratio = 1.0*sum_intersected_area/sum_withinGeoDAR_lake_UID_area
    
    check_needed = 'yes'
    if max(withinGeoDAR_lake_UID_joint_count) == 1 and area_ratio > 0.99:
        check_needed = 'no'
    
    # Update values in unique_intersected_lake_UID series 
    for this_withinGeoDAR_lake_UID in withinGeoDAR_lake_UID:
        index_2 = [i for i, x in enumerate(unique_intersected_lake_UID) if x == this_withinGeoDAR_lake_UID] 
        if check_needed == 'no':
            unique_intersected_lake_UID_joint_count[index_2[0]] = -1 #update for all PLD polygons for this cluster (i.e., intersecting this GeoDAR reservoir). 
            # This should not interfere with the next iteration because the previous count is 1 (unique). 
        
        # update area
        unique_intersected_lake_UID_arearatio[index_2[0]] = area_ratio #applying to all PLD polygons for this cluster (intersecting this GeoDAR reservoir).
        # If this PLD polygon intersects more than one GeoDAR polygon, the ratio intersected with the last GeoDAR polygon will be used for a possible 'rewrite'. 
        # This is consistent with the GeoDAR ID written for this PLD polygon (see iteration above).
        # This is okay, because the count number of this PLD polygon will be used to indicate the need for manual check. 
print('unique intersected GeoDARv11 information generated')
        
# Assign values to the original PLD
# Must be added at the end otherwise it will cause conflicts with the attribute names in Intersection Tool.
fieldList = arcpy.ListFields(PLD)       
fieldName = [f.name for f in fieldList]
if ('GeoDARv11_ID' in fieldName) == False:
    arcpy.AddField_management(PLD, 'GeoDARv11_ID', "TEXT")
if ('lake_UID_QC' in fieldName) == False:
    arcpy.AddField_management(PLD, 'lake_UID_QC', "TEXT") # manual split or edit may be needed. 
if ('GeoDARv11_ID_QC' in fieldName) == False:
    arcpy.AddField_management(PLD, 'GeoDARv11_ID_QC', "TEXT")
if ('intGeoDAR_count' in fieldName) == False:
    arcpy.AddField_management(PLD, 'intGeoDAR_count', "LONG")
if ('intGeoDAR_arearatio' in fieldName) == False:
    arcpy.AddField_management(PLD, 'intGeoDAR_arearatio', "DOUBLE")   
    
polygon_records = arcpy.UpdateCursor(PLD) # By default, cursor only takes effect for selected features.
for polygon_record in polygon_records:
    polygon_record.lake_UID_QC = polygon_record.lake_UID
    
    index_3 = [i for i, x in enumerate(unique_intersected_lake_UID) if x == polygon_record.lake_UID] 
    if len(index_3) > 1:
        print('this should not happen...')
    if len(index_3) == 1:
        polygon_record.GeoDARv11_ID = unique_intersected_lake_UID_joint_GeoDAR_ID[index_3[0]]
        polygon_record.GeoDARv11_ID_QC = unique_intersected_lake_UID_joint_GeoDAR_ID[index_3[0]]
        polygon_record.intGeoDAR_count = unique_intersected_lake_UID_joint_count[index_3[0]]
        polygon_record.intGeoDAR_arearatio = unique_intersected_lake_UID_arearatio[index_3[0]]
    
    polygon_records.updateRow(polygon_record)
del polygon_record # Release the cursor
del polygon_records
 
print("----- Module Completed -----")
print(datetime.datetime.now())
