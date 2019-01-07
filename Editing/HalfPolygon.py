
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


in_fc = arcpy.GetParameterAsText(0)

arcpy.AddMessage(in_fc.Extent)


def extentToArray():
    return None

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


# Extent of feature. X will never change when splitting North South.
start_X = 0.0
start_Y = 0.0
end_X = 0.0
end_Y = 0.0
# Area of polygons that were the highest area
total_area = 0.0


# for each polygon, get the minimum bounding area

# Create a line at the halfway point



########################################################################################################################
#
#                                                      DONE
#                                                    Mark Buie
#                                              City of Mesquite, Texas
#
########################################################################################################################
