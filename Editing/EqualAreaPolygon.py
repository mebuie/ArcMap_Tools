
"""
EqualAreaPolygon.py: Splits a polygon into equal north south areas.

This script is for an ArcMap Python Toolbox that splits a polygon into two north south equal areas. All features in the
feature class are merged into one feature before processing. The tool honors selections and will export only the
selected layers before merging the selected layers and processing.
"""

__author__ = "Mark Buie | GIS Coordinator | City of Mesquite"
__credits__ = ["Lynne Buie | City of Plano"]
__maintainer__ = "Mark Buie"
__email__ = "mbuie@cityofmesquite.com"
__status__ = "Production"


import arcpy
import os

########################################################################################################################
#
#                                                  TOOL PARAMETERS
#
########################################################################################################################

# in_fc: POLYGON the input polygon layer from the ArcMap tool
# tolerance: DOUBLE the tool first splits the polygon in the middle of the extent. The tolerance is calculated as the
#   polygon with the smallest area / by the polygon with the greatest area. The tool runs until this metric is above the
#   the user defined tolerance.
# save_location: POLYGON the location for the resulting split polygon

in_fc = arcpy.GetParameterAsText(0)
tolerance = float(arcpy.GetParameterAsText(1))
save_location = arcpy.GetParameterAsText(2)


########################################################################################################################
#
#                                                  FUNCTIONS
#
########################################################################################################################


def getExtent(in_feature):
    """
    Return the extent of a feature class

    :param in_feature: FEATURE CLASS the feature class to calculate the extent
    :return: the value of the top, bottom, left, and right extent
    """
    describe = arcpy.Describe(in_feature)
    X_max = describe.extent.XMax
    X_min = describe.extent.XMin
    Y_max = describe.extent.YMax
    Y_min = describe.extent.YMin
    return X_max, X_min, Y_max, Y_min


def bisectExtent(line_fc, X_max, X_min, Y_max, Y_min, start_x, start_y, end_x, end_y):
    """
    Return the middle extent of a feature class.

    Populates a feature class with polylines representing the extent of a feature class with a bisecting line.

    :param line_fc: POLYLINE The feature class to populate.
    :param X_max: DOUBLE The right extent of a feature class.
    :param X_min: DOUBLE The left extent of a feature class.
    :param Y_max: DOUBLE The top extent of a feature class.
    :param Y_min: DOUBLE The bottom extent of a feature class.
    :param start_x: DOUBLE X coordinate for start of bisecting line.
    :param start_y: DOUBLE Y coordinate for start of bisecting line.
    :param end_x: DOUBLE X coordinate for end of bisecting line.
    :param end_y: DOUBLE Y coordinate for end of bisecting line.
    :return: VOID
    """
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
    """
    Returns the total area of a all features in a feature class.

    :param in_fc: POLYGON The input feature class
    :return: DOUBLE The total area.
    """
    cursor = arcpy.da.SearchCursor(in_fc, ["SHAPE@AREA"])
    area = 0.0
    for row in cursor:
        area += row[0]
    return area


def checkEquality(in_fc):
    """
    Check which of two north south polygons have the greatest area.

    Calculates which of two polygons, that are stacked north and south, have the greatest area and determines which way
    the bisecting line should be moved to make them equal

    :param in_fc: POLYGON input polygon feature class with two features stacked on top of each other.
    :return: ratio DOUBLE the polygon with smallest area divided by the polygon with greatest area.
    :return: direction TEXT the direction the bisecting line should be moved to make the polygons equal.
    :return: high_area DOUBLE the value of the polygon with the greatest area
    :return: low_area DOUBLE the value of the polygon with the lowest area
    """

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

# in_fc_copy: POLYGON The path to a copy of the user input feature class to be split
# in_fc_copy_diss: POLYGON The path to the dissolve of in_fc_copy
# in_fc_spatialref: SPATIAL REFERENCE The spatial reference of the input feature class. Needed for the create feature
#   class parameter when creating feature class for polyline.
# line_fc_path: STRING The path for the polyline feature class.
# line_fc_filename: STRING The filename for the polyline feature class.
# line_fc: STRING The full path name for the polyline feature class.
# ftop_fc: POLYGON Path for output of feature to polygon geoprocessing tool.
# clip_fc: POLYGON Path for output of clip geoprocessing tool.
# ratio: DOUBLE The starting ratio
# tolerance_divider: INT the number to divide the tolerance by after each change of direction.

in_fc_copy = r"in_memory\copy"
in_fc_copy_diss = r'in_memory\copy_diss'
in_fc_spatialref = arcpy.Describe(in_fc).spatialReference
line_fc_path = r"in_memory"
line_fc_filename = "split_line"
line_fc = os.path.join(line_fc_path, line_fc_filename)
ftop_fc = r"in_memory\feature_to_polygon"
clip_fc = r"in_memory\clip"
ratio = 0.0
tolerance_divider = 10


########################################################################################################################
#
#                                                  SCRIPT
#
########################################################################################################################

# Make a copy of the input feature class so we don't mess it up. This also extracts and isolates any user selected
# features.
arcpy.CopyFeatures_management(in_fc, in_fc_copy)

# Dissolve all features into one feature.
arcpy.Dissolve_management(in_fc_copy, in_fc_copy_diss)

# Calculate the total area of features in the feature class.
total_area = getArea(in_fc_copy_diss)

# Get the extent of the feature class.
x_max, x_min, y_max, y_min = getExtent(in_fc_copy_diss)

# calculate the coordinates of the bisecting line.
start_x = x_max
start_y = (y_max - y_min) / 2 + y_min
end_y = (y_max - y_min) / 2 + y_min
end_x = x_min
increment = ((y_max - y_min) / 2) / tolerance_divider

# While the ratio is less than the tolerance, move the bisecting line towards the polygon with the greatest area.
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
    arcpy.Clip_analysis(ftop_fc, in_fc_copy_diss, clip_fc)

    # Find the ratio of area between the two polygons and the direction we need to move the bisecting line to make them
    # equal.
    ratio, direction, high, low = checkEquality(clip_fc)

    arcpy.AddMessage("The area ratio is {0}, adjusting bisect line {1}".format(ratio, direction))

    # Each time the line changes direction reduce the amount the line is incremented by. The precision of feature class
    # extents is 9. If the increment value drops below this the tool will get hung. Therefore, we add clause that breaks
    # the loop if the precision drops below 9.
    if started:
        if moving != direction:
            increment = increment / 10
            if 0.00000001 > increment > 0.000000001:
                increment = 0.000000001
            elif increment < 0.000000001:
                break
            arcpy.AddMessage("Reducing line increment to {0}".format(increment))

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
