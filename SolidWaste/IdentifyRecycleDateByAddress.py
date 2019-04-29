
"""
IdentifyRecycleDateByAddress.py: Create a feature class to evaluate damage after a natural disaster.

"""

__author__ = "Mark Buie | GIS Coordinator | City of Mesquite"
__maintainer__ = "Mark Buie"
__email__ = "mbuie@cityofmesquite.com"
__status__ = "Development"

import arcinfo
import arcpy
import os

########################################################################################################################
#
#                                                  TOOL PARAMETERS
#
########################################################################################################################

addressLayer = arcpy.GetParameterAsText(0)
recycleLayer = arcpy.GetParameterAsText(1)
addressString = arcpy.GetParameterAsText(2)
# # outFeature = arcpy.GetParameterAsText(3)

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

output_path = arcpy.env.scratchGDB
########################################################################################################################
#
#                                                     VARIALBES
#
########################################################################################################################

address_SQL = '"MUNIS_CLAS" NOT IN(\'UTILITY_ADDRESS\', \'OUTSIDE_CITY\') ' \
              'AND "MESQ_CLASS" NOT IN (\'OUTSIDE_CITY\', \'OUTSIDE_CITY_MISD\', \'OUTSIDE_CITY_MISD_TAX\') ' \
              'AND "ADDRESS" LIKE '
input_address_SQL = '\'%' + addressString + '%\''
where_clause = address_SQL + input_address_SQL

output_fields = ['ADDRESS', 'FID_MESQ_GARB_ROTO_RECYCLE', 'FID_MESQ_ROTO_BOOM', 'DAY',
                 'ROUTE', 'FID_MESQ_GARBAGE_COLLECTION', 'GCDAREA', 'FID_MESQ_RECYCLING',
                 'RCDAREA']

########################################################################################################################
#
#                                                  SCRIPT
#
########################################################################################################################

arcpy.AddMessage("creating address_lyr")
address_lyr = arcpy.MakeFeatureLayer_management(addressLayer, "#", where_clause)

arcpy.AddMessage("creating intersect")
intersect = arcpy.Intersect_analysis([address_lyr, recycleLayer], "#")

arcpy.AddMessage("creating intersect_lyr")
intersect_lyr = arcpy.MakeFeatureLayer_management(intersect, "#")

arcpy.AddMessage("removing unwated fields")
desc = arcpy.Describe(intersect_lyr)
arcpy.AddMessage(desc.dataType)
field_info = desc.fieldInfo
for i in range(0, field_info.count):
    if field_info.getFieldName(i) not in output_fields:
        field_info.setVisible(i, "HIDDEN")

arcpy.AddMessage("creating result_lyr")
result_lyr = arcpy.MakeFeatureLayer_management(intersect_lyr, "#", "", "", field_info)
#
# arcpy.AddMessage("creating result_fc")
# arcpy.CopyFeatures_management(result_lyr, "output")

arcpy.FeatureClassToFeatureClass_conversion(result_lyr, output_path, "result_lyr")

arcpy.AddMessage("generating output")
arcpy.SetParameterAsText(3, os.path.join(output_path, "result_lyr"))



########################################################################################################################
#
#                                                      DONE
#                                                    Mark Buie
#                                              City of Mesquite, Texas
#
########################################################################################################################
