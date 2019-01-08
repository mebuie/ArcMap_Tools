
"""
HalfPolygon.py: Splits a polygon into equal areas.

This script is for an ArcMap Python Toolbox that splits a polygon into equal areas.

The workflow in this script was dervied by the City of Richardson's 'Damage Assessment Walk Through' authored by
Heather Scroggins.

"""

__author__ = "Mark Buie | GIS Coordinator | City of Mesquite"
__credits__ = ["Lynne Buie | City of Plano"]
__maintainer__ = "Mark Buie"
__email__ = "mbuie@cityofmesquite.com"
__status__ = "Development"


import arcpy
import os

########################################################################################################################
#
#                                                  TOOL PARAMETERS
#
########################################################################################################################


in_fc = arcpy.GetParameterAsText(0)
tolerance = float(arcpy.GetParameterAsText(1))
save_location = arcpy.GetParameterAsText(2)


########################################################################################################################
#
#                                                  FUNCTIONS
#
########################################################################################################################


def getExtent(in_feature):
    describe = arcpy.Describe(in_feature)
    X_max = describe.extent.XMax
    X_min = describe.extent.XMin
    Y_max = describe.extent.YMax
    Y_min = describe.extent.YMin
    return X_max, X_min, Y_max, Y_min

def bisectExtent(line_fc, X_max, X_min, Y_max, Y_min, start_x, start_y, end_x, end_y):
    coordlist = [[1, X_max, Y_max],
                 [1, X_min, Y_max],
                 [1, X_min, Y_max],
                 [1, X_min, Y_min],
                 [1, X_min, Y_min],
                 [1, X_max, Y_min],
                 [1, X_max, Y_min],
                 [1, X_max, Y_max],
                 [2, start_x, start_y],
                 [2, end_x, end_y ]]

    cursor = arcpy.da.InsertCursor(line_fc, ["SHAPE@"])

    array = arcpy.Array()

    ID = -1
    for coord in coordlist:
        if ID == -1:
            ID = coord[0]

        if ID != coord[0]:
            cursor.insertRow([arcpy.Polyline(array)])
            array.removeAll()
        array.add(arcpy.Point(coord[1], coord[2]))
        ID = coord[0]

    cursor.insertRow([arcpy.Polyline(array)])


def getArea(in_fc):
    cursor = arcpy.da.SearchCursor(in_fc, ["SHAPE@AREA"])
    area = 0.0
    for row in cursor:
        area += row[0]
    return area


def checkEquality(in_fc):
    #TODO: Check if more than two features?

    attributes = []
    cursor = arcpy.da.SearchCursor(in_fc, ["SHAPE@AREA", "SHAPE@XY"])
    for row in cursor:
        attributes.append([row[0], row[1]])

    attributes.sort(reverse=True)

    high_area = attributes[0][0]
    low_area = attributes[1][0]

    ratio = low_area / high_area

    high_area_y = attributes[0][1][1]
    low_area_y = attributes[1][1][1]

    if high_area_y > low_area_y:
        return ratio, "up", high_area, low_area
    elif high_area_y == low_area_y:
        return ratio, "equal", high_area, low_area
    else:
        return ratio, "down", high_area, low_area


def getSpatialRefofLayer():
    return None

def XYtoLine(out_feature, template, coordinate_array):
    # http://desktop.arcgis.com/en/arcmap/10.3/analyze/python/writing-geometries.htm
    return None

def lineToPolygon():
    return None

def exportSmallestArea():
    # Select smallest area
    # feature to feature
    # clip with original feature class
    return None

########################################################################################################################
#
#                                               ENVIRONMENT SETTINGS
#
########################################################################################################################


# Set workspace to in_memory. Uses computer RAM for increased performance, but may cause issues with larger datasets.
arcpy.env.workspace = 'in_memory'


########################################################################################################################
#
#                                                     VARIALBES
#
########################################################################################################################


in_fc_copy = r"in_memory\copy"
in_fc_spatialref = arcpy.Describe(in_fc).spatialReference
# line_fc = r"in_memory\split_line"
# line_fc_filename = line_fc.split("\\")[-1]
# line_fc_path = line_fc.rsplit("\\", 1)[0]

line_fc_path = r"in_memory"
line_fc_filename = "split_line"
line_fc = os.path.join(line_fc_path, line_fc_filename)
ftop_fc = r"in_memory\feature_to_polygon"
# ftop_fc = os.path.join(arcpy.env.scratchGDB, "ftop")
clip_fc = r"in_memory\clip"
# clip_fc = os.path.join(arcpy.env.scratchGDB, "clip_fc")
result_fc = r"in_memory\result"
ratio = 0.0
if tolerance == 1:
    tolerance = 0.99999999
tolerance_divider = 4


########################################################################################################################
#
#                                                  SCRIPT
#
########################################################################################################################

# Make a copy of the input feature class so we don't mess it up.
# TODO: Make feature layer then copy to extract any user selected polygons
arcpy.CopyFeatures_management(in_fc, in_fc_copy)

# TODO: Check how many features there are and merge them into one if greater than one feature.

# Calculate the total area and target area.
total_area = getArea(in_fc_copy)

# Get the extent of the copied input feature class.
x_max, x_min, y_max, y_min = getExtent(in_fc_copy)

start_x = x_max
start_y = (y_max - y_min) / 2 + y_min
end_y = (y_max - y_min) / 2 + y_min
end_x = x_min
increment = ((y_max - y_min) / 2) / tolerance_divider

started = False
moving = "nowhere"
while ratio <= tolerance:

    # Make the polyline feature class that will have the bisecting line.
    arcpy.CreateFeatureclass_management(line_fc_path, line_fc_filename, "POLYLINE", None, None, None, in_fc_spatialref)

    # Insert lines into the line_fc that represent the perimeter of the extent with a bisecting line through the middle.
    bisectExtent(line_fc, x_max, x_min, y_max, y_min, start_x, start_y, end_x, end_y)

    # Convert the lines to polygons
    arcpy.FeatureToPolygon_management(line_fc, ftop_fc)

    # Clip the polygons with the original feature class
    arcpy.Clip_analysis(ftop_fc, in_fc_copy, clip_fc)

    # Find the ratio of area between the two polygons and the direction we need to move the bisecting line to make them
    # equal.
    ratio, direction, high, low = checkEquality(clip_fc)

    arcpy.AddMessage("the ratio is {0}, the tolerance is {1} moving line {2}".format(ratio, tolerance, direction))

    if started:
        if moving != direction:
            increment = increment / 10
            arcpy.AddMessage("INCREMENT CHANGED TO {0}".format(increment))

    if direction == "up":
        start_y += increment
        end_y += increment
    else:
        start_y -= increment
        end_y -= increment

    moving = direction

    started = True

arcpy.CopyFeatures_management(clip_fc, save_location)









########################################################################################################################
#
#                                                      DONE
#                                                    Mark Buie
#                                              City of Mesquite, Texas
#
########################################################################################################################
