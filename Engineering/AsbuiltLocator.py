"""
AsbuiltLoator.py: Returns the Asbuilt sets from a corresponding feature.

This geoprocessing tools returns the Asbuilt record sets that are associated with a GIS feature by querying the Asbuilt
id of the feature and then using that id to query an Asbuilt database. This tools assumes that each digitized feature
contains the asbuilt id of the source sheet and that all asbuilts in the set share a common prefix.

For this script, the id is contained in a hyperlink in the HYPERLINK field. To use the asbuilt id, it must first be
isolated from the hyperlink using regex.

FEATURE ID
001-1 (Digitized Source)

ASBUILT DB ID (ARCHIVE)
001-1
001-2
001-3
001-n...

"""

__author__ = "Mark Buie | GIS Coordinator | City of Mesquite"
__maintainer__ = "Mark Buie"
__email__ = "mbuie@cityofmesquite.com"
__status__ = "Development"

import arcpy
import os
import zipfile
import re
import shutil


########################################################################################################################
#
#                                                  TOOL PARAMETERS
#
########################################################################################################################

input_feature = arcpy.GetParameterAsText(0).strip("'")


########################################################################################################################
#
#                                                  FUNCTIONS
#
########################################################################################################################


def zipdir(path, ziph):
    """
    Zips files in path to the ziph.zip

    :param path: The folder path to files to be zipped.
    :param ziph: The ZipFile object.
    :return: Void
    """
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):

        for file in files:
            arcpy.AddMessage(file)
            ziph.write(
                os.path.join(root, file),
                os.path.join("asbuilts", file)
            )

########################################################################################################################
#
#                                                  VARIABLES
#
########################################################################################################################

asbuilt_id_field = 'HYPERLINK'
regex_url_expression = "asbuilts/([A-z0-9./ -]*)\""
asbuilt_folder_path = r"\\fps-777-3.cityofmesquite.com\engineering\Asbuilts"
scratch_folder_path = arcpy.env.scratchFolder

########################################################################################################################
#
#                                                  SCRIPT
#
########################################################################################################################


# Let's first create some directories to organize our data. These folders will be created in the scratch directory
# of the geoprocessing job folder.
asbuilt_folder = os.path.join(scratch_folder_path, "asbuilts")

if not os.path.exists(asbuilt_folder):
    os.mkdir(os.path.join(scratch_folder_path, "asbuilts"))

# arcpy.AddMessage(input_feature)

# Create a list of the fields in the feature class so we can check if it has the correct ones.
list_fields = [str.upper(str(field.name)) for field in arcpy.ListFields(input_feature)]

# If the feature class has a HYPERLINK field, it's the fields we need.
if asbuilt_id_field in list_fields:
    with arcpy.da.SearchCursor(input_feature, asbuilt_id_field, "HYPERLINK IS NOT NULL", sql_clause=("DISTINCT", None)) as cursor:
        for row in cursor:
            regex_url_result = re.search(regex_url_expression, row[0])
            if regex_url_result:

                regex_file_expression = r"/([0-9A-z]*-[A-z0-9]*-[A-z0-9-.]*[A-z]*)"
                regex_file_result = re.search(regex_file_expression, regex_url_result.group(1))

                # arcpy.AddMessage(regex_url_result.group(1))

                asbuilt_file_path = os.path.join(asbuilt_folder_path, regex_url_result.group(1))

                if os.path.isfile(asbuilt_file_path):
                    shutil.copy2(asbuilt_file_path, os.path.join(asbuilt_folder, regex_file_result.group(1)))
                else:
                    arcpy.AddWarning("No file found for {0}".format(regex_file_result.group(1)))

# Create an empty zip file
zipf = zipfile.ZipFile(
    os.path.join(scratch_folder_path, "asbuilt_output.zip"),
    "w",
    zipfile.ZIP_DEFLATED)

# Populate zip file with asbuilts
zipdir(
    os.path.join(scratch_folder_path, "asbuilts"),
    zipf)

# Close zip.
zipf.close()

#TODO: Check if results were returned to prevent empty zip file.

# Return the results of the geoprocessing tool as a zip file.
arcpy.SetParameterAsText(1, os.path.join(scratch_folder_path, "asbuilt_output.zip"))

########################################################################################################################
#
#                                                      DONE
#                                                    Mark Buie
#                                              City of Mesquite, Texas
#
########################################################################################################################