
"""
IdentifyRecycleDateByAddress.py: Create a feature class to evaluate damage after a natural disaster.

"""

__author__ = "Mark Buie | GIS Coordinator | City of Mesquite"
__maintainer__ = "Mark Buie"
__email__ = "mbuie@cityofmesquite.com"
__status__ = "Development"


import arcpy

########################################################################################################################
#
#                                                  TOOL PARAMETERS
#
########################################################################################################################

save_path = arcpy.GetParameterAsText(0)
in_spatialref = arcpy.GetParameterAsText(1)
in_tax_layer = arcpy.GetParameterAsText(2)
in_zone_layer = arcpy.GetParameterAsText(3)
in_zone_field = arcpy.GetParameterAsText(4)
in_grid_layer = arcpy.GetParameterAsText(5)
in_grid_field = arcpy.GetParameterAsText(6)


########################################################################################################################
#
#                                                  FUNCTIONS
#
########################################################################################################################

########################################################################################################################
#
#                                               ENVIRONMENT SETTINGS
#
########################################################################################################################

########################################################################################################################
#
#                                                     VARIALBES
#
########################################################################################################################

########################################################################################################################
#
#                                                  SCRIPT
#
########################################################################################################################

########################################################################################################################
#
#                                                      DONE
#                                                    Mark Buie
#                                              City of Mesquite, Texas
#
########################################################################################################################
