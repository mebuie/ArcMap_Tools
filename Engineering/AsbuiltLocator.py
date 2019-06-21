"""
AsbuiltLoator.py: Returns the Asbuilt sets that overlap an input polygon.

This geoprocessing tools returns the Asbuilt record sets from features that overlap a user defined polygon.
The tool relies on a unique asbuilt archive schema where the asbuilt that was used to digitize the feature is referenced
as a field in the feature, and the asbuilt sets share a common id (see example 1).

For this script, the id is contained in a hyperlink in the HYPERLINK field. To use the asbuilt id, it must first be
isolated from the hyperlink using regex.

Example 1:

FEATURE ID
001-1 (Digitized Source)

ASBUILT ID (ARCHIVE)
001-1
001-2
001-3
001-n...

"""

__author__ = "Mark Buie | GIS Coordinator | City of Mesquite"
__maintainer__ = "Mark Buie"
__email__ = "mbuie@cityofmesquite.com"
__status__ = "Production"

import arcpy
import os
import zipfile
import re
import shutil
import glob

# TODO: TEST, Large file sizes could potentially bog down the server.
# TODO: To save space on the server, the asbuilt directory should be deleted after the tool is finished.


########################################################################################################################
#
#                                                  TOOL PARAMETERS
#
########################################################################################################################

target_area = arcpy.GetParameterAsText(0)
input_feature = arcpy.GetParameterAsText(1).split(";")


########################################################################################################################
#
#                                                  VARIABLES
#
########################################################################################################################

scratch_folder_path = arcpy.env.scratchFolder


########################################################################################################################
#
#                                                  FUNCTIONS
#
########################################################################################################################

def clipFeatures(in_layers, focus_area):
    output_features = []
    count = 0
    for layer in in_layers:
        count += 1
        layer = layer.strip("'")
        # There is a bug with the clip tool where it will fail if the output name is too long...
        result_name = os.path.join(arcpy.env.scratchGDB, "lyr" + str(count))
        output_features.append(result_name)
        arcpy.Clip_analysis(layer, focus_area, result_name)

    return output_features


def asbuiltHyperlinkToUNC(in_layer, unc_path):
    # The HYPERLINK field can be mixed case depending on the layer. Let's find the correct case.
    # TODO: I have not tested if SearchCursor inputs are case sensitive, so this may not be necessary.
    hyperlink_field = ""
    fields = arcpy.ListFields(in_layer)
    for field in fields:
        if field.name.upper() == "HYPERLINK":
            hyperlink_field = field.name

    # Let's get all the unique asbuilt unc paths.
    regex_url_expression = "asbuilts/([A-z0-9./ -]*)\""
    asbuilt_unc_paths = []
    with arcpy.da.SearchCursor(in_layer, hyperlink_field, hyperlink_field + " IS NOT NULL", sql_clause=("DISTINCT", None)) as cursor:

        for row in cursor:
            # Remove the suffix of the html link.
            regex_url_result = re.search(regex_url_expression, row[0])
            # Replace with UNC path.
            if regex_url_result:
                asbuilt_file_path = os.path.join(unc_path, regex_url_result.group(1))
                asbuilt_unc_paths.append(asbuilt_file_path)

    return asbuilt_unc_paths


def getAsbuiltSetPaths(full_asbuilt_paths):
    asbuilt_set_paths = []
    # Remove the asbuilt file suffix -001, 002, etc.
    for path in full_asbuilt_paths:
        set_path = path.rsplit("-", 1)[0]
        asbuilt_set_paths.append(set_path)

    return asbuilt_set_paths

def getAsbuilts(asbuilt_paths, save_path):
    for asbuilt_path in asbuilt_paths:
        set_name = asbuilt_path.rsplit("/", 1)[-1]

        arcpy.AddMessage("Preparing asbuilts for {0}".format(set_name))

        set_folder = os.path.join(save_path, set_name)
        if not os.path.exists(set_folder):
            os.mkdir(os.path.join(set_folder))

        asbuilt_images = glob.glob(asbuilt_path + '*.TIF*')
        for image in asbuilt_images:
            if os.path.isfile(image):
                shutil.copy2(image, os.path.join(set_folder))
            else:
                arcpy.AddWarning("No file found for {0}".format(image))


def zip_folder(folder_path, output_path):
    """Zip the contents of an entire folder (with that folder included
    in the archive). Empty subfolders will be included in the archive
    as well.
    
    Modified from:
    https://www.calazan.com/how-to-zip-an-entire-directory-with-python/
    """
    parent_folder = os.path.dirname(folder_path)
    # Retrieve the paths of the folder contents.
    contents = os.walk(folder_path)

    zip_file = zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED)
    for root, folders, files in contents:
        # Include all subfolders, including empty ones.
        for folder_name in folders:
            absolute_path = os.path.join(root, folder_name)
            relative_path = absolute_path.replace(parent_folder + '\\', '')
            zip_file.write(absolute_path, relative_path)
        for file_name in files:
            absolute_path = os.path.join(root, file_name)
            relative_path = absolute_path.replace(parent_folder + '\\', '')
            zip_file.write(absolute_path, relative_path)

    zip_file.close()

########################################################################################################################
#
#                                                  SCRIPT
#
########################################################################################################################

# Let's create a directory to store the asbuilts. This directory will zipped and provided to the user.
asbuilt_folder = os.path.join(scratch_folder_path, "asbuilts")
# The scratch directory is gauranteed to be empty, so this isn't really needed as a geoprocessing services. However,
# it is useful for debugging purposes within ArcMap.
if not os.path.exists(asbuilt_folder):
    os.mkdir(os.path.join(scratch_folder_path, "asbuilts"))


# Clip the line features to the user defined project area.
clipped_features = clipFeatures(input_feature, target_area)


# Get all the paths to the asbuilt sheets that were used to digitize the feature.
asbuilt_paths = []
asbuilt_folder_path = r"\\fps-777-3.cityofmesquite.com\engineering\Asbuilts"
for feature in clipped_features:
    asbuilt_paths += asbuiltHyperlinkToUNC(feature, asbuilt_folder_path)


# Get the paths of the asbuilt sets by removing the the suffix from the asbuilt sheets.
asbuilt_set_paths = getAsbuiltSetPaths(asbuilt_paths)


# Now that we know what asbuilt set the feature belongs to, we cant retrieve them from the asbuilt database.
getAsbuilts(asbuilt_set_paths, asbuilt_folder)


# Zip the results
# TODO: Check if results were returned to prevent empty zip file.
arcpy.AddMessage("Zipping files...")
zip_folder(
    os.path.join(scratch_folder_path, "asbuilts"),
    os.path.join(scratch_folder_path, "asbuilt_output.zip")
)


# Return the results of the geoprocessing tool as a zip file.
arcpy.SetParameterAsText(2, os.path.join(scratch_folder_path, "asbuilt_output.zip"))


########################################################################################################################
#
#                                                      DONE
#                                                    Mark Buie
#                                              City of Mesquite, Texas
#
########################################################################################################################
