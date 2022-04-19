# [Description] ------------------------------
# This module associates dam points to their possible reservoir polygons, and
# rank the dam points associated with the same reservoir polygon based on the preferred dam source.
# Results will be flagged by QA values for manual QC. 

# Script by: Jida Wang, Kansas State University
# Initiated: Feb. 27, 2022
# Last update: Feb. 27, 2022
# Contact: jidawang@ksu.edu; gdbruins@ucla.edu
#---------------------------------------------


# [Setup] -----------------------------------
# Inputs
# work_dir: working space
work_dir = r"D:\Research\Projects\SWOT\Dam_inventory_collection\Dam_harmonization\To_Sam\R1_other_regions\R1_India_test.gdb"

# Dams: dam points
dams_original = "All_dams_India" #this is just a replicate of All_dams_India at the beginning

# This water mask has QCed GeoDAR IDs
water_mask = "PLDv01_India" #QCed (with GeoDAR intersection). 

# Search distance (in meters):
search_step = 50
max_search_distance = 300  # This may vary with the quality of the dam point data. 
max_search_distance_large = 1000 # for snapped GOODD points (about 30-arc-second, consistent with the snapping data of HydroSHEDS 30-second, see Mulligan et al GOODD paper).

# OUTPUT
dams = "All_dams_India_HM" #this is just a replicate of All_dams_India at the beginning, with expanded attributes
water_mask_dissolved = "PLDv01_India_HM"
#---------------------------------------------




# [Script] -----------------------------------
# Import built-in functions and tools.
import arcpy, numpy, os, re
import numpy as np
from arcpy import env
from numpy import ndarray
from datetime import date

print("----- Module Started -----")
print(datetime.datetime.now())

# Define environment settings.
env.workspace = work_dir
env.overwriteOutput = "TRUE"

# Copy dams_original to dams
arcpy.CopyFeatures_management(dams_original, dams)

# Make feature layer
arcpy.MakeFeatureLayer_management(water_mask, "water_mask_lyr")
# Retrieve GeoDARv11_ID_QC (with repeats) and prepare for dissolve. 
SQL_reservoirs = """{0} IS NOT NULL""".format(arcpy.AddFieldDelimiters('water_mask_lyr', "GeoDARv11_ID_QC")) #GeoDARv11_ID_QC IS NOT NULL
arcpy.SelectLayerByAttribute_management("water_mask_lyr", "NEW_SELECTION", SQL_reservoirs)
original_GeoDARv11_ID_QC = []
polygon_records = arcpy.SearchCursor("water_mask_lyr") # By default, cursor only takes effect for selected features. 
for polygon_record in polygon_records:
    original_GeoDARv11_ID_QC.append(polygon_record.GeoDARv11_ID_QC)
del polygon_record # Release the cursor
del polygon_records
arcpy.SelectLayerByAttribute_management("water_mask_lyr", "CLEAR_SELECTION") 
# Dissolve QCed PLD (with GeoDAR IDs QCed)
# Just in case clear the selection and select again
arcpy.MakeFeatureLayer_management(water_mask, "water_mask_lyr")
SQL_reservoirs = """{0} IS NOT NULL""".format(arcpy.AddFieldDelimiters('water_mask_lyr', "GeoDARv11_ID_QC")) #GeoDARv11_ID_QC IS NOT NULL
arcpy.SelectLayerByAttribute_management("water_mask_lyr", "NEW_SELECTION", SQL_reservoirs)
arcpy.Dissolve_management('water_mask_lyr', 'interm_GeoDAR_dissolved', ["GeoDARv11_ID_QC"], \
    [["lake_id","FIRST"],["basin_id","FIRST"],["names","FIRST"],["grand_id","FIRST"],["ref_area","FIRST"],["ref_wse","FIRST"],\
     ["date_t0","FIRST"],["ds_t0","FIRST"],["pass_full","FIRST"],["pass_part","FIRST"],["cycle_flag","FIRST"],\
     ["ref_area_u","FIRST"],["ref_wse_u","FIRST"],["storage","FIRST"],["ice_clim_f","FIRST"],["ice_dyn_fl","FIRST"],\
     ["lon","FIRST"],["lat","FIRST"],["reach_id_l","FIRST"],["lakeID","FIRST"],["inter_PLDv01","FIRST"],["shareseg_PLDv01","FIRST"],\
     ["lake_UID","FIRST"],["R1_partition","FIRST"],["GeoDARv11_ID","FIRST"],["lake_UID_QC","FIRST"],\
     ["intGeoDAR_count","MAX"],["intGeoDAR_arearatio","FIRST"]]) #aggregate fields based on "FIRST_". 
# Remove prefix FIRST_ or MAX_
for f in arcpy.ListFields('interm_GeoDAR_dissolved'):
    if not f.required:        # not really necessary here
        arcpy.AlterField_management('interm_GeoDAR_dissolved', f.name, f.name.replace("MAX_", "").replace("FIRST_", ""))
# Update lake_UID_QC fields for those that were dissolved from more than two polygons
polygon_records = arcpy.UpdateCursor('interm_GeoDAR_dissolved')
for polygon_record in polygon_records:
    here_indices = [i for i, x in enumerate(original_GeoDARv11_ID_QC) if x == polygon_record.GeoDARv11_ID_QC]
    if len(here_indices) > 1: #meaning this polygon was dissolved from multiple polygons
        polygon_record.lake_UID_QC = polygon_record.lake_UID_QC + '_dslvd'
    polygon_records.updateRow(polygon_record)
del polygon_record
del polygon_records
arcpy.SelectLayerByAttribute_management("water_mask_lyr", "SWITCH_SELECTION") #non-GeoDAR PLD polygons. 
# Merge the two layers
arcpy.management.Merge(['water_mask_lyr', 'interm_GeoDAR_dissolved'], water_mask_dissolved)
arcpy.SelectLayerByAttribute_management("water_mask_lyr", "CLEAR_SELECTION")
print('dissolved....')

# Add fields for dam points
fieldList = arcpy.ListFields(dams)    
fieldName = [f.name for f in fieldList]
if ('R1_keep' in fieldName) == False:
    arcpy.AddField_management(dams, 'R1_keep', "SHORT")
if ('R1_lake_UID_QC' in fieldName) == False: #indicating the lake_UID has been QCed after GeoDAR intersection
    arcpy.AddField_management(dams, 'R1_lake_UID_QC', "TEXT")
if ('R1_keep_QC1' in fieldName) == False: # QC needed
    arcpy.AddField_management(dams, 'R1_keep_QC1', "SHORT")
if ('R1_lake_UID_QC1' in fieldName) == False: # QC needed
    arcpy.AddField_management(dams, 'R1_lake_UID_QC1', "TEXT")
if ('R1_move' in fieldName) == False:
    arcpy.AddField_management(dams, 'R1_move', "SHORT")
if ('R1_comment' in fieldName) == False:
    arcpy.AddField_management(dams, 'R1_comment', "TEXT") #255 characters by default
    
# Add fields for water polygons
fieldList = arcpy.ListFields(water_mask_dissolved)    
fieldName = [f.name for f in fieldList]
if ('R1_damcnt' in fieldName) == False:
    arcpy.AddField_management(water_mask_dissolved, 'R1_damcnt', "LONG")
if ('R1_srccnt' in fieldName) == False:
    arcpy.AddField_management(water_mask_dissolved, 'R1_srccnt', "LONG")
#if ('R1_duplicate' in fieldName) == False:
#    arcpy.AddField_management(water_mask_dissolved, 'R1_duplicate', "TEXT")
if ('R1_dam_UIDs' in fieldName) == False:
    arcpy.AddField_management(water_mask_dissolved, 'R1_dam_UIDs', "TEXT")
if ('R1_sel_damcnt' in fieldName) == False:
    arcpy.AddField_management(water_mask_dissolved, 'R1_sel_damcnt', "LONG")
if ('R1_sel_dam_UID' in fieldName) == False:
    arcpy.AddField_management(water_mask_dissolved, 'R1_sel_dam_UID', "TEXT")
#if ('R1_vrfdamUID' in fieldName) == False:
#    arcpy.AddField_management(water_mask_dissolved, 'R1_vrfdamUID', "TEXT")
#if ('R1_verified' in fieldName) == False:
#    arcpy.AddField_management(water_mask_dissolved, 'R1_verified', "SHORT")
if ('R1_lake_UID_QC1' in fieldName) == False: # QC needed if geometry needs to be changed.
    arcpy.AddField_management(water_mask_dissolved, 'R1_lake_UID_QC1', "TEXT")
if ('R1_comment' in fieldName) == False:
    arcpy.AddField_management(water_mask_dissolved, 'R1_comment', "TEXT")   

# Assign all register dam R1_keep = 1
all_records = arcpy.UpdateCursor(dams)
for this_record in all_records:
    #if this_record.dam_source == 'register_xxxx':
    if re.search('register_.+', this_record.dam_source): # The .+ symbol is used in place of * symbol
        this_record.R1_keep = 1
        this_register_name = this_record.dam_source # Retrieve the register name for later use.
        all_records.updateRow(this_record)        
del this_record # Release the cursor
del all_records

# Make feature layers
arcpy.MakeFeatureLayer_management(dams, "dams_lyr")
arcpy.MakeFeatureLayer_management(water_mask_dissolved, 'water_mask_dissolved_lyr')  

# Retrieve water mask subset (to improve computing efficiency)
arcpy.SelectLayerByLocation_management("water_mask_dissolved_lyr", "WITHIN_A_DISTANCE_GEODESIC", "dams_lyr", str(max_search_distance*1.05)+" Meters") # new selection (using 5% tolerance to ensure all polygons selected)
# Expand the selection distance for snapped GOODD dams
SQL_dam_GOODDsnp = """{0} = '{1}'""".format(arcpy.AddFieldDelimiters("dams_lyr", "dam_source"), "GOODDsnp")
arcpy.SelectLayerByAttribute_management("dams_lyr", "NEW_SELECTION", SQL_dam_GOODDsnp)
arcpy.SelectLayerByLocation_management("water_mask_dissolved_lyr", "WITHIN_A_DISTANCE_GEODESIC", "dams_lyr", str(max_search_distance_large*1.05)+" Meters", "ADD_TO_SELECTION") # add to existing selection
# Also make sure all GeoDAR reservoirs were selected (even though the reservoir may not be within the search distance).
SQL_reservoirs = """{0} IS NOT NULL""".format(arcpy.AddFieldDelimiters('water_mask_dissolved_lyr', "GeoDARv11_ID_QC")) #ADD GeoDARv11_ID_QC IS NOT NULL
arcpy.SelectLayerByAttribute_management("water_mask_dissolved_lyr", "ADD_TO_SELECTION", SQL_reservoirs)
arcpy.CopyFeatures_management("water_mask_dissolved_lyr", "interm_water_dissolved_neardams") # just edit on this layer. 
arcpy.SelectLayerByAttribute_management("water_mask_dissolved_lyr", "CLEAR_SELECTION")
arcpy.SelectLayerByAttribute_management("dams_lyr", "CLEAR_SELECTION")
arcpy.MakeFeatureLayer_management("interm_water_dissolved_neardams", "interm_water_dissolved_neardams_lyr")

# Loop through each dam to pair its reservoir polygon
dam_records = arcpy.SearchCursor("dams_lyr")
total_dam_count = float(arcpy.GetCount_management("dams_lyr").getOutput(0)) # Total number of dam points
progress_array = list(np.linspace(1, total_dam_count, 100)) # Used to track pairing progress
progress_array_rounded = []
for this_progress_array_element in progress_array:
    progress_array_rounded.append(round(this_progress_array_element))
progress_array = [] # Clear up the memory
dam_i = 0
dam_ID_array = []
dam_source_array = []
#intGeoDAR_array = []
lakeUID_array = [] # to write and update later
#GeoDARID_array = [] # to write GeoDAR ID only for those with GeoDAR polygons
keep_array = [] # to write and update later
for dam_record in dam_records:
    # Track and report pairing progress
    dam_i += 1
    #print(dam_i)
    this_dam_i_index = [i for i, x in enumerate(progress_array_rounded) if x == dam_i]
    if len(this_dam_i_index)>0:
        print(" In progress:  " + str(100.0*progress_array_rounded[this_dam_i_index[0]]/total_dam_count) + "% of the dams paired ......")
    
    # Read values from here
    keep_array.append(dam_record.R1_keep) #initiation
    
    # Retrieve this dam ID
    this_dam_ID = dam_record.dam_UID #string
    dam_ID_array.append(this_dam_ID)
    
    # Retrieve this dam source
    this_dam_source = dam_record.dam_source #string     
    dam_source_array.append(this_dam_source)
    
    # Select this dam
    SQL_dam = """{0} = '{1}'""".format(arcpy.AddFieldDelimiters("dams_lyr", "dam_UID"), this_dam_ID)
    arcpy.SelectLayerByAttribute_management("dams_lyr", "NEW_SELECTION", SQL_dam)
    
    # Select all water polygons within the search distance (4/6/2022: added a mechanism that uses search_step to reduce overshooting)
    # For GeoDAR dams, they will be correctly tied to the QCed GeoDAR reservoir (if any). 
    if this_dam_source == 'GeoDARv11': # Do not apply the proximity criterion here. 
        #if this_dam_ID exists in the polygon as well. 
        SQL_reservoir = """{0} = '{1}'""".format(arcpy.AddFieldDelimiters("interm_water_dissolved_neardams_lyr", "GeoDARv11_ID_QC"), this_dam_ID)
        arcpy.SelectLayerByAttribute_management("interm_water_dissolved_neardams_lyr", "NEW_SELECTION", SQL_reservoir)
        selected_polygon_count = int(arcpy.GetCount_management("interm_water_dissolved_neardams_lyr").getOutput(0))
        # If the input is a layer or table view containing a selected set of records after the action of selection (either by attribute or location),
        # only the selected records will be counted, otherwise NO features are used for counting (i.e., count = 0).
        # However, if we performed an action of "CLEAR_SELECTION" or we never performed any selection action, the count will be the total record number.
        
        if selected_polygon_count > 1:
            print('this should not happen...') #reservoirs have already been dissolved
            print(SQL_reservoir)
            print('count: ' + str(selected_polygon_count))
            
        if selected_polygon_count == 1: #select this polygon
            polygon_records = arcpy.SearchCursor("interm_water_dissolved_neardams_lyr") # By default, cursor only takes effect for selected features. 
            for polygon_record in polygon_records:
                this_lakeUID = polygon_record.lake_UID_QC
                #this_GeoDARID = polygon_record.GeoDARv11_ID_QC
                #this_intGeoDAR = polygon_record.intGeoDARres
            del polygon_record # Release the cursor
            del polygon_records
            lakeUID_array.append(this_lakeUID)
            #GeoDARID_array.append(this_GeoDARID)
            #intGeoDAR_array.append(this_intGeoDAR) 
        else: #this GeoDAR dam should not be associated with any polysons even though it has a polygon within the proximity (Do not use the proximity criterion here). 
            # Update dam_count_array
            lakeUID_array.append('-999')    
            #GeoDARID_array.append('-999')
            #intGeoDAR_array.append(-999)   
    else: # Apply proximity criterion for other dam sources. 
        # Apply the mechanism to apply search_step
        if this_dam_source != 'GOODDsnp':
            selected_polygon_count = 0 #initiate the value to be 0
            search_distance = search_step #initiate the value to be search_step
            while selected_polygon_count == 0 and search_distance <= max_search_distance: #stop if the count is no more 0 or the maximum search_distance has been reached;
                arcpy.SelectLayerByLocation_management("interm_water_dissolved_neardams_lyr", "WITHIN_A_DISTANCE_GEODESIC", "dams_lyr", str(search_distance)+" Meters")
                selected_polygon_count = int(arcpy.GetCount_management("interm_water_dissolved_neardams_lyr").getOutput(0))
                search_distance += search_step
        else:
            arcpy.SelectLayerByLocation_management("interm_water_dissolved_neardams_lyr", "WITHIN_A_DISTANCE_GEODESIC", "dams_lyr", str(max_search_distance_large)+" Meters")
            selected_polygon_count = int(arcpy.GetCount_management("interm_water_dissolved_neardams_lyr").getOutput(0))
        
        if selected_polygon_count > 0: # If at least one water polygon was found...
            # Retrieve the largest polygon, together with its polygon ID and area value. 
            polygon_records = arcpy.SearchCursor("interm_water_dissolved_neardams_lyr") # By default, cursor only takes effect for selected features. 
            Area_largest_polygon = 0.0
            for polygon_record in polygon_records:
                if polygon_record.Shape_Area > Area_largest_polygon:
                    Area_largest_polygon = polygon_record.Shape_Area
                    this_lakeUID = polygon_record.lake_UID_QC
                    #this_GeoDARID = polygon_record.GeoDARv11_ID_QC
                    #this_intGeoDAR = polygon_record.intGeoDARres
            del polygon_record # Release the cursor
            del polygon_records
            lakeUID_array.append(this_lakeUID)
            #GeoDARID_array.append(this_GeoDARID)
            #intGeoDAR_array.append(this_intGeoDAR)
        else: 
            # Update dam_count_array
            lakeUID_array.append('-999')    
            #GeoDARID_array.append('-999')
            #intGeoDAR_array.append(-999)        
        
    # Clear up selections
    arcpy.SelectLayerByAttribute_management("interm_water_dissolved_neardams_lyr", "CLEAR_SELECTION")  
    arcpy.SelectLayerByAttribute_management("dams_lyr", "CLEAR_SELECTION")
del dam_record # Release the cursor
del dam_records

# Loop through unique lake_UIDs and select the best-ranking dam
unique_lakeUID_array = list(set(lakeUID_array)) 
unique_lakeUID_array.remove('-999') #note '-999' is also a unique value, which affects the calculation below. So this value needs to be removed. 
dam_count_array = [] # to write later
source_count_array = [] # to write later
duplicate_dam_array = [] # to write later
full_damUID_array = [] # to write later
selected_damcnt_array = [] # to write later
selected_damUID_array = [] # to write later
for this_lakeUID in unique_lakeUID_array:
         
    dam_indices = [i for i, x in enumerate(lakeUID_array) if x == this_lakeUID] #search from dam arrays. 
    
    #intGeoDAR = intGeoDAR_array[dam_indices[0]] # a single value only
    
    dam_count = len(dam_indices)
    dam_count_array.append(dam_count)
    
    ### DO NOT USE THIS ANY MORE. IT WILL SORT THE dam_indices TO BE UNIQUE and re-order it from small to large. 
    #dam_sources = [x[1] for x in enumerate(dam_source_array) if x[0] in dam_indices] 
    dam_sources = [dam_source_array[i] for i in dam_indices] 
    source_count = len(list(set(dam_sources)))
    source_count_array.append(source_count)
    
    if source_count < dam_count:
        duplicate_dam = 'same-source dam duplicate'
    elif dam_count > 1:
        duplicate_dam = 'multiple dams'
    elif  dam_count == 1:
        duplicate_dam = 'single dam'
    else:
        print('This should not happen...')
    duplicate_dam_array.append(duplicate_dam)
    
    #Retrieve all dam_UIDs
    #dam_UIDs = [x[1] for x in enumerate(dam_ID_array) if x[0] in dam_indices] ###
    dam_UIDs = [dam_ID_array[i] for i in dam_indices]
    
    #Sort dam_UIDs through ranks: 
    rank_sources = [this_register_name, 'GeoDARv11', 'GOODDunsnp', 'GOODDsnp'] #decreasing preference 
    sorted_dam_UIDs = [] ##
    for this_rank_source in rank_sources:
        here_indices = [i for i, x in enumerate(dam_sources) if x == this_rank_source]
        if len(here_indices)>0:
            for this_index in here_indices:
                sorted_dam_UIDs.append(dam_UIDs[this_index])
    this_sorted_dam_UID_list = '' #convert a list into a concatenate string for writing
    for this_sorted_dam_UIDs in sorted_dam_UIDs:
        this_sorted_dam_UID_list = this_sorted_dam_UID_list + this_sorted_dam_UIDs + ','
    full_damUID_array.append(this_sorted_dam_UID_list[:-1]) #delete the last ','
    
    #select the best damUID
    if this_register_name in dam_sources:
        here_indices = [i for i, x in enumerate(dam_sources) if x == this_register_name]
        selected_damcnt_array.append(len(here_indices)) # write the number of best-source dams to polygon       
        this_selected_damUID = '' #convert to a list of dam IDs 
        for this_index in here_indices:
            this_selected_damUID = this_selected_damUID + dam_UIDs[this_index] + ','
            keep_array[dam_indices[this_index]] = len(here_indices) # Write the number of best-source dams to dam point
            #To check if this value exceeds 1, indicating duplicate sources and thus assignment uncertainty.              
        selected_damUID_array.append(this_selected_damUID[:-1]) #delete the last ','
        
    elif 'GeoDARv11' in dam_sources:
        here_indices = [i for i, x in enumerate(dam_sources) if x == 'GeoDARv11']
        selected_damcnt_array.append(len(here_indices)) # write the number of best-source dams to polygon       
        this_selected_damUID = '' #conver to a list of dam IDs 
        for this_index in here_indices:
            this_selected_damUID = this_selected_damUID + dam_UIDs[this_index] + ','
            keep_array[dam_indices[this_index]] = len(here_indices) # Write the number of best-source dams to dam point
            #To check if this value exceeds 1, indicating duplicate sources and thus assignment uncertainty.              
        selected_damUID_array.append(this_selected_damUID[:-1]) #delete the last ','
        
    elif 'GOODDunsnp' in dam_sources:
        here_indices = [i for i, x in enumerate(dam_sources) if x == 'GOODDunsnp']
        selected_damcnt_array.append(len(here_indices)) # write the number of best-source dams to polygon       
        this_selected_damUID = '' #conver to a list of dam IDs 
        for this_index in here_indices:
            this_selected_damUID = this_selected_damUID + dam_UIDs[this_index] + ','
            keep_array[dam_indices[this_index]] = len(here_indices) # Write the number of best-source dams to dam point
            #To check if this value exceeds 1, indicating duplicate sources and thus assignment uncertainty.              
        selected_damUID_array.append(this_selected_damUID[:-1]) #delete the last ','
        
    elif 'GOODDsnp' in dam_sources:
        here_indices = [i for i, x in enumerate(dam_sources) if x == 'GOODDsnp']
        selected_damcnt_array.append(len(here_indices)) # write the number of best-source dams to polygon       
        this_selected_damUID = '' #conver to a list of dam IDs 
        for this_index in here_indices:
            this_selected_damUID = this_selected_damUID + dam_UIDs[this_index] + ','
            keep_array[dam_indices[this_index]] = len(here_indices) # Write the number of best-source dams to dam point
            #To check if this value exceeds 1, indicating duplicate sources and thus assignment uncertainty.              
        selected_damUID_array.append(this_selected_damUID[:-1]) #delete the last ','
               
    else:
        print('This should not happen....') #no other sources possible. So this should not happen. 

#Assign values back to dams   
dam_records = arcpy.UpdateCursor('dams_lyr')
ii = 0
for dam_record in dam_records:
    dam_record.R1_keep = keep_array[ii]
    dam_record.R1_keep_QC1 = keep_array[ii] # TO QC
    if lakeUID_array[ii] != '-999':
        dam_record.R1_lake_UID_QC = lakeUID_array[ii] 
        dam_record.R1_lake_UID_QC1 = lakeUID_array[ii] # TO QC
    dam_records.updateRow(dam_record)
    ii = ii + 1
del dam_record
del dam_records
  
#Assign values back to water mask    
lake_records = arcpy.UpdateCursor('water_mask_dissolved_lyr')
for lake_record in lake_records:
    lake_record.R1_lake_UID_QC1 = lake_record.lake_UID_QC # in case the geometry of this polygon needs to be changed. TO QC
    this_index = [i for i, x in enumerate(unique_lakeUID_array) if x == lake_record.lake_UID_QC]
    if len(this_index) > 0:
        lake_record.R1_damcnt = dam_count_array[this_index[0]]
        lake_record.R1_srccnt = source_count_array[this_index[0]]
        #lake_record.R1_duplicate = duplicate_dam_array[this_index[0]]
        lake_record.R1_dam_UIDs = full_damUID_array[this_index[0]]
        lake_record.R1_sel_dam_UID = selected_damUID_array[this_index[0]]
        lake_record.R1_sel_damcnt  = selected_damcnt_array[this_index[0]]
    lake_records.updateRow(lake_record)
del lake_record
del lake_records  

print("----- Module Completed -----")
print(datetime.datetime.now())