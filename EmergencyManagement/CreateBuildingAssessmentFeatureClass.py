
"""
BuildingAssessment.py: Create a feature class to evaluate damage after a natural disaster.

This script is for an ArcMap Python Toolbox that creates a feature class, which is intended to be published as a service
and used as part of the Collector App for in field damage assessment. The feature class is a snapshot of parcel tax
information with added fields that are necessary for evaluation of the extent of damage for the purpose of qualifying
for FEMA aid. In addition, the user has the option to include a Zoning and USGN layer to add additional fields, which
may be useful for reporting purposes.

The workflow in this script was dervied by the City of Richardson's 'Damage Assessment Walk Through' authored by
Heather Scroggins.

"""

__author__ = "Mark Buie | GIS Coordinator | City of Mesquite"
__credits__ = ["Heather Scroggins | City of Richardson"]
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



# save_path: FEATURE CLASS The path and name of the feature class to be created. This will be the feature class that will
#     be published as a service for parcel damage inspection.
#
# in_spatialref: SPATIAL REFERENCE The spatial reference of the created feature class.
#
# in_tax_layer: FEATURE CLASS A feature class containing the data to be appended to save_path. Note that the field names
#     must exactly match for the attribute data to append.
#
# in_zone_layer: FEATURE CLASS An optional feature class containing a zoning class name field to be appended to the
#     to the ZONE_FULL field in save_path
#
# in_zone_field: FIELD The field in in_zone_layer that contains the data to append to the ZONE_FULL field.
#
# in_grid_layer: FEATURE CLASS An optional feature class containing the USNG label field to be appended to  the
#     USNGCoord field in save_path
#
# in_grid_field: FIELD The field in in_grid_layer that contains the data to append to the USNGCoord field.


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


def pathToFilename(path):
    """
    Extracts geodatabase path from feature class path

    Extracts only the filename from the feature class path to be used in tools that requite the path and filename be
    separate. Has not been tested on feature classes that are within a feature dataset.

    :param path: STRING
        The path and filename of a feature class.
    :return: STRING
        The filename from the path.
    """
    path = path.split("\\")[-1]
    path = path.split(".")[-1]

    return path


def pathToOutpath(path):
    path = path.rsplit("\\", 1)[0]

    return path


def createFeature(out_path, out_name, geometry_type, spatial_reference, fields):
    """
    Creates a feature class and optionally add fields from a dictionary.

    :param out_path: STRING
        The ArcSDE, file, or personal geodatabase, or the folder in which the output feature class
        will be created. This workspace must already exist.
    :param out_name: STRING
        The name of the feature class to be created.
    :param geometry_type: STRING
        The geometry type of the feature class:
            -POINT
            -MULTIPOINT
            -POLYGON
            -POLYLINE
    :param spatial_reference: SPATIAL REFERENCE
        The spatial reference of the output feature dataset. You can specify the
        spatial reference in several ways:
            -By entering the path to a .prj file, such as C:/workspace/watershed.prj.
            -By referencing a feature class or feature dataset whose spatial reference you want to apply, such as
                C:/workspace/myproject.gdb/landuse/grassland.
            -By defining a spatial reference object prior to using this tool, such as
                sr = arcpy.SpatialReference("C:/data/Africa/Carthage.prj"), which you then use as the spatial
                reference parameter.
    :param fields: DICT
        A dictionary of fields where the key in an integer and the value are the parameters of the
        AddField geoprocessing tool.

            fields = {
                0: {
                    'name': 'InspectorId',
                    'type': 'TEXT',
                    'precision': None,
                    'scale': None,
                    'length': 50,
                    'alias': 'Inspector ID',
                    'domain': None
                }
            }

    :return: VOID
    """
    # Send message to tool console.
    arcpy.AddMessage("\n\nCreating feature class {0} in location:{1}".format(out_path, out_name))

    # Create the feature class
    arcpy.CreateFeatureclass_management(out_path, out_name, geometry_type, spatial_reference=spatial_reference)

    fc = os.path.join(out_path, out_name)

    # Add the fields
    for index in fields:
        attributes = fields[index]

        arcpy.AddMessage("    Adding field {0} to {1}...".format(attributes.get("name"), out_name))
        arcpy.AddField_management(in_table=fc,
                                  field_name=attributes.get("name"), field_type=attributes.get("type"),
                                  field_precision=attributes.get("precision"), field_scale=attributes.get("scale"),
                                  field_length=attributes.get("length"), field_alias=attributes.get("alias"))


def addSubtypes(in_table, field, in_subtypes, default_code):
    """
    Adds subtypes to a feature class from a dictionary of subtype coded values.

    :param in_table: STRING
        The feature class to be updated.
    :param field: STRING
        An integer field that will store the subtype codes.
    :param in_subtypes: DICT
        A dictionary of subtype coded values where the subtype code is the 'key' and the subtype
        description is the value.
    :param default_code: STRING
        The default subtype code for the feature class.
    :return: VOID
    """

    arcpy.AddMessage("\nPreparing to add subtypes...")

    # Set the field for the subtype.
    arcpy.SetSubtypeField_management(in_table, field)

    # Add the subtypes to the feature class.
    for subtype in in_subtypes:
        arcpy.AddMessage("    Adding subtype {0}".format(in_subtypes[subtype]))

        arcpy.AddSubtype_management(in_table, subtype, in_subtypes[subtype])

    # Set the default subtype.
    arcpy.SetDefaultSubtype_management(in_table, default_code)


def addDomainsToDatabase(db_path, in_domains):
    """
    Checks if domains are currently in the target database and creates them if they are not.

    :param db_path: STRING
        Path to the target database.
    :param in_domains: DICT
        A dictionary of domains to be added to the target database where the 'key' is the domain
        name and the value is a dictionary of parameters:

            domains = {
                "domain name": {
                    "description": "a description of the domain",
                    "field_type": "TEXT",
                    "domain_type": "CODED",
                    "domDict": {
                        "domain code": "domain value",
                        "domain code": "domain value"
                    }
                }
            }

    :return: VOID
    """
    # Send message to tool console.
    arcpy.AddMessage("\nChecking for domains in {0}...".format(db_path))

    # Get list of all domain objects currently in database
    database_domains = arcpy.da.ListDomains(db_path)
    existing_domains = []

    # Get list of names from domain objects.
    for dbDomain in database_domains:
        existing_domains.append(dbDomain.name)

    # Check if domains are already in the database and create them if not.
    for domain in in_domains:
        if domain not in existing_domains:
            arcpy.AddMessage("Creating domain {0}...".format(domain))

            arcpy.CreateDomain_management(
                db_path,
                domain,
                in_domains[domain]['description'],
                in_domains[domain]['field_type'],
                in_domains[domain]['domain_type']
            )

            for code in addDomains[domain]["domDict"]:
                arcpy.AddMessage("    Adding coded value {0} : {1}".format(
                    code,
                    in_domains[domain]["domDict"][code],
                ))

                arcpy.AddCodedValueToDomain_management(
                    db_path,
                    domain,
                    code,
                    in_domains[domain]["domDict"][code]
                )


def assignDomainToLayer(in_table, domains):
    """
    Assigns domains and, if applicable, the subtype code for a field.

    :param in_table: STRING
        The feature class containing the field(s) to assign a domain
    :param domains: DICT
        A dictionary where the key is the domain name and the value is fields, which contains a dictionary of field names
        and default subtypes for each field that will be assigned the domain. For example,

            domains = {
                "domain_name_A": {
                    fields: {
                        0: {
                            "name": "field_name_1",
                            "subtype: 1
                            }
                        1: {
                            "name": "field_name_1",
                            "subtype: 2
                            }
    :return: VOID
    """
    arcpy.AddMessage("\nAssigning domains to fields...")

    for domain in domains:
        # If the domain has a 'fields' dictionary then iterate over them.
        if domains[domain]["fields"]:
            # Since the domain may be assigned to multiple fields, we iterate through each key in the fields dictionary.
            # and assigne the domain to the field name with the field subtype.
            for key in domains[domain]["fields"]:
                field = domains[domain]["fields"][key]
                arcpy.AddMessage("    Adding {0} to field {1}".format(domain, field["name"]))
                arcpy.AssignDomainToField_management(
                    in_table=in_table,
                    field_name=field["name"],
                    domain_name=domain,
                    subtype_code=field["subtype"]
                )


def updatedFieldFromSpatialJoin(parent_fc, join_field, child_fc, update_field, source_field):
    """
    Updates a field in a parent feature class with a field from a child feature class based on a spatial join.

    The parent feature class is first converted to points before performing the spatial join with the child feature
    class and finally using Field Calculator to update the update_field.

    :param parent_fc: STRING
        The polygon feature class who's field will be updated.
    :param join_field: STRING
        The field that will be used to join resulting spatial join back to the parent feature class.
    :param child_fc:  STRING
        The feature class containing the source field that will update the parent feature class.
    :param update_field: STRING
        The field from the parent feature class to be updated.
    :param source_field: STRING
        The field from the child feature class that will be the source.
    :return: VOID
    """
    arcpy.AddMessage("\nUpdating field from spatial join...")
    arcpy.AddMessage("    Converting parent feature class to points...")
    arcpy.FeatureToPoint_management(parent_fc, r"in_memory\parcel_pnt")

    arcpy.AddMessage("    Creating spatial join...")
    spatial_out = os.path.join(arcpy.env.scratchGDB, "scratch_spatial_out")

    arcpy.SpatialJoin_analysis(
        target_features=r"in_memory\parcel_pnt",
        join_features=child_fc,
        out_feature_class=spatial_out
    )

    arcpy.AddIndex_management(
        in_table=spatial_out,
        fields=join_field,
        index_name=join_field
    )

    arcpy.AddMessage("    Joining back to parent feature class...")
    arcpy.AddJoin_management(
        in_layer_or_view=parent_fc,
        in_field=join_field,
        join_table=spatial_out,
        join_field=join_field,
        join_type="KEEP_ALL"
    )

    arcpy.AddMessage("    Calculating field...this may take a while...")
    arcpy.CalculateField_management(
        in_table=parent_fc,
        field=update_field,
        expression="!" + source_field + "!",
        expression_type="PYTHON"
    )

    arcpy.AddMessage("    Removing join and cleaning workspace...")
    arcpy.RemoveJoin_management("in_memory\parcel")
    arcpy.Delete_management(r"in_memory\parcel_pnt")
    arcpy.Delete_management(r"in_memory\parcel_pnt_U_in_grid")
    arcpy.Delete_management(spatial_out)


def updateFieldFromJoin(in_layer, in_field, join_layer, join_field, calc_field, expression):
    """
    Updates a field in a parent feature class with a field in the joined child feature class.

    :param in_layer: STRING
        The parent feature class who's field will be updated.
    :param in_field: STRING
        The parent feature class field to join on.
    :param join_layer: STRING
        The child feature class.
    :param join_field: STRING
        The child feature class field to join on.
    :param calc_field: STRING
        The field that will be updated.
    :param expression: PYTHON EXPRESSION
        The expression used to update the field. Note that fields from the joined table
        must be preceded with the child feature class name. For example:

            <name of feature class>.<field name>
    :return: VOID
    """
    arcpy.AddMessage("\nUpdating field from join...")

    arcpy.AddJoin_management(
        in_layer_or_view=in_layer,
        in_field=in_field,
        join_table=join_layer,
        join_field=join_field,
        join_type="KEEP_ALL"
    )

    scratch_zoning = os.path.join(arcpy.env.scratchGDB, "scratch_buildingassessment")
    arcpy.CopyFeatures_management(in_layer, scratch_zoning)


    arcpy.AddMessage("    Calculating field...this may take a while...")
    arcpy.CalculateField_management(
        in_table=in_layer,
        field=calc_field,
        expression=expression,
        expression_type="PYTHON"
    )

    arcpy.AddMessage("....Removing Join and cleaning workspace...")
    arcpy.RemoveJoin_management(in_layer)


def isSDE(input_fc):
    """
    Returns true if a feature class is stored in an enterprise geodatabase.

    :param input_fc: The input feature class to be checked
    :return: boolean Returns true if feature class in enterprise geodatabase.
    """
    describe = arcpy.Describe(input_fc)
    if describe.geometryStorage:
        return True
    else:
        return False


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


# fc_path: STRING Derived from the save_path parameter, the path to the geodatabase that the feature class is saved to.
# fc_name: STRING Derived from the save_path parameter, the file name of the saved feature class.
# addFields: DICT A dictionary containing all the fields to be added to the created feature class defined by save_path.
# subtypes: DICT A dictionary of coded values where the key is the subtype code and the value is the subtype description
# addDomains: DICT A dictionary of domains to be added to the geodtabase and fields that will be assigned the domain.

fc_path = pathToOutpath(save_path)
fc_name = pathToFilename(save_path)

addFields = {
    0: {'name': 'InspectorId', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 50, 'alias': 'Inspector ID', 'domain': None},
    1: {'name': 'InspectionDate', 'type': 'DATE', 'precision': None, 'scale': None, 'length': None, 'alias': 'Date of Inspection', 'domain': None},
    # 2: {'name': 'InspectInterior', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 4, 'alias': 'Interior Inspected?', 'domain': None},
    # 3: {'name': 'InspectExterior', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 4, 'alias': 'Exterior Inspected', 'domain': None},
    4: {'name': 'USNGCoord', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 50, 'alias': 'USNG Grid', 'domain': None},
    5: {'name': 'ACCOUNT_NUM', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 50, 'alias': 'Parcel Account', 'domain': None},
    6: {'name': 'DamageExtent', 'type': 'SHORT', 'precision': 5, 'scale': None, 'length': None, 'alias': 'Damage Extent', 'domain': None},
    7: {'name': 'PercentLost', 'type': 'SHORT', 'precision': 5, 'scale': None, 'length': None, 'alias': 'Damage Percent', 'domain': None},
    8: {'name': 'Placard', 'type': 'SHORT', 'precision': 5, 'scale': None, 'length': None, 'alias': 'Placard', 'domain': None},
    9: {'name': 'DamageDesc', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 500, 'alias': 'Description of Damage', 'domain': None},
    10: {'name': 'COMMENT', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 500, 'alias': 'Additional Comments', 'domain': None},
    11: {'name': 'BIZ_NAME', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 150, 'alias': 'Parcel Name', 'domain': None},
    12: {'name': 'OWNER_NAME_1', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 150, 'alias': 'Parcel Owner 1', 'domain': None},
    13: {'name': 'OWNER_NAME_2', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 150, 'alias': 'Parcel Owner 2', 'domain': None},
    14: {'name': 'OWNER_CONTACT', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 150, 'alias': 'Owner Contact 1', 'domain': None},
    15: {'name': 'OWNER_ADDRESS', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 200, 'alias': 'Owner Contact 2', 'domain': None},
    16: {'name': 'OWNER_SUITE', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 50, 'alias': 'Owner Suite', 'domain': None},
    17: {'name': 'OWNER_CITY', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 50, 'alias': 'Owner City', 'domain': None},
    18: {'name': 'OWNER_STATE', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 50, 'alias': 'Owner State', 'domain': None},
    19: {'name': 'OWNER_COUNTRY', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 50, 'alias': 'Owner Country', 'domain': None},
    20: {'name': 'OWNER_ZIPCODE', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 9, 'alias': 'Owner Zip', 'domain': None},
    21: {'name': 'STREET_NUM', 'type': 'LONG', 'precision': 10, 'scale': None, 'length': None, 'alias': 'Parcel St Number', 'domain': None},
    22: {'name': 'STREET_HALF_NUM', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 5, 'alias': 'Parcel St Number Half', 'domain': None},
    23: {'name': 'FULL_STREET_NAME', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 60, 'alias': 'Parcel Full Street Name', 'domain': None},
    24: {'name': 'BLDG_ID', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 5, 'alias': 'Parcel Building', 'domain': None},
    25: {'name': 'UNIT_ID', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 5, 'alias': 'Parcel Unit', 'domain': None},
    26: {'name': 'IMPR_VAL', 'type': 'DOUBLE', 'precision': 38, 'scale': 8, 'length': None, 'alias': 'Improvement Value', 'domain': None},
    27: {'name': 'LAND_VAL', 'type': 'DOUBLE', 'precision': 38, 'scale': 8, 'length': None, 'alias': 'Land Value', 'domain': None},
    28: {'name': 'LAND_AG_EXEMPT', 'type': 'LONG', 'precision': 10, 'scale': None, 'length': None, 'alias': 'Ag Exempt', 'domain': None},
    29: {'name': 'AG_USE_VAL', 'type': 'LONG', 'precision': 10, 'scale': None, 'length': None, 'alias': 'Ag Use Value', 'domain': None},
    30: {'name': 'TOT_VAL', 'type': 'DOUBLE', 'precision': 38, 'scale': 8, 'length': None, 'alias': 'Market Value', 'domain': None},
    31: {'name': 'SPTD_CODE', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 50, 'alias': 'SPTD Code', 'domain': None},
    32: {'name': 'DWEB_ACCT', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 200, 'alias': 'DCAD Account Link', 'domain': None},
    33: {'name': 'DWEB_HIST', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 200, 'alias': 'DCAD History Link', 'domain': None},
    # 34: {'name': 'PROP_CLASS', 'type': 'LONG', 'precision': 10, 'scale': None, 'length': None, 'alias': 'Zoning Class', 'domain': None},
    # 35: {'name': 'ZONE', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 10, 'alias': 'Zone', 'domain': None},
    36: {'name': 'FULL_ZONE', 'type': 'TEXT', 'precision': None, 'scale': None, 'length': 50, 'alias': 'Full Zone', 'domain': None},
    # 37: {'name': 'DAMAGE_CALC', 'type': 'DOUBLE', 'precision': 38, 'scale': 8, 'length': None, 'alias': 'Calculated Damage Value', 'domain': None},
}

subtypes = {
    "0": "Affected",
    "1": "Minor Damage",
    "2": "Major Damage",
    "3": "Destroyed",
    "4": "Inaccessible",
    "5": "Not Assessed",
    "6": "Not Impacted"
}

addDomains = {
    # "Yes_No": {
    #     "fields": {
    #         0: {"name": "InspectInterior", "subtype": None},
    #         1: {"name": "InspectExterior", "subtype": None}
    #     },
    #     "description": "Yes or No",
    #     "field_type": "TEXT",
    #     "domain_type": "CODED",
    #     "domDict": {
    #         "Yes": "Yes",
    #         "No": "No"
    #     }},
    "EM_Placard": {
        "fields": {
            0: {"name": "Placard", "subtype": None}
        },
        "description": "Occupancy Placard for Building Services",
        "field_type": "SHORT",
        "domain_type": "CODED",
        "domDict": {
            "0": "Not Assessed",
            "1": "Green",
            "2": "Yellow",
            "3": "Red"
        }},
    "EM_DmgAffected": {
        "fields": {
            0: {"name": "PercentLost", "subtype": "0"}
        },
        "description": "Percent lost when Affected is selected",
        "field_type": "SHORT",
        "domain_type": "CODED",
        "domDict": {
            "0": "0",
            "5": "5",
            "10": "10"
        }},
    "EM_DmgMinor": {
        "fields": {
            0: {"name": "PercentLost", "subtype": "1"}
        },
        "description": "Percent lost when Minor Damage is selected",
        "field_type": "SHORT",
        "domain_type": "CODED",
        "domDict": {
            "10": "10",
            "20": "10",
            "30": "30",
            "40": "40",
            "50": "50",
        }},
    "EM_DmgMajor": {
        "fields": {
            0: {"name": "PercentLost", "subtype": "2"}
        },
        "description": "Percent lost when Major Damage is selected",
        "field_type": "SHORT",
        "domain_type": "CODED",
        "domDict": {
            "50": "50",
            "60": "60",
            "70": "70",
            "80": "80",
            "90": "90"
        }},
    "EM_DmgDestroyed": {
        "fields": {
            0: {"name": "PercentLost", "subtype": "3"}
        },
        "description": "Percent lost when Destroyed is selected",
        "field_type": "SHORT",
        "domain_type": "CODED",
        "domDict": {
            "90": "90",
            "95": "95",
            "100": "100"
        }},
}


########################################################################################################################
#
#                                                  SCRIPT
#
########################################################################################################################



# Create the feature class, hereafter called the BuildingAssessment feature class, and add the necessary fields that
# will be used to evaluate parcel property damage. The resulting feature class will be published as a service for use in
# Collector App and to display data in an Operational Dashboard.
arcpy.AddMessage("{0}\n{1}".format(fc_path, fc_name))
createFeature(fc_path, fc_name, 'POLYGON', in_spatialref, addFields)


# Add the subtypes to the feature class and assign the default subtype value. The subtypes refer to the extent of damage
# observed for all buildings located on the parcel. The subtypes are used to assign attribute domains for the percentage
# of the parcel that is damage. This preserved the integrity of the data by ensuring that a parcel cannot be assigned
# as 'MINOR DAMAGE', but listed as 100% destroyed.
addSubtypes(save_path, "DamageExtent", subtypes, "5")


# Check if domains already exist in the target database and add them if necessary. The BuildingAssessment feature class
# participates in several attribute domains that ensure the integrity of the data, and which must be present at the
# geodatabase level.
addDomainsToDatabase(fc_path, addDomains)

# Now that the domains exist in the geodatabase. We can assign the domains and subtype code to each field.
assignDomainToLayer(save_path, addDomains)

# Append data from the tax layer to the BuildingAssessment feature class. The tax layer contains pertinent information
# which is needed for both field surveyors and to calculate the total cost in damage, such as the value of the parcel.
# There is no field mapping set, so the field names in the BuildingAssessment feature class MUST match the field names
# in the tax layer, if you want the attributes to be appended.
arcpy.AddMessage("\nAppending data from {0} to {1}".format(in_tax_layer, fc_name))
arcpy.Append_management(
    inputs=in_tax_layer,
    target=save_path,
    schema_type="NO_TEST",
    subtype="Not Assessed")


# At this point the BuildingAssessment feature class has been created and populated with the data from the tax layer. It
# can be used as is, but we are going to add some additional information, such as the USNG grid label and the Zoning
# type for the parcel.


# Add an index to the BuildingAssessment feature class. To add the USNG grid label to the BuildingAssessment feature
# class we convert the BuildingAssessment feature class to points, do a spatial join on the USNG grid, then join the
# resulting feature class back on the original BuildingAssessment feature class on the ACCOUNT_NUM field before using
# the Field Calculator to transfer the data from the joined USNG label to the BuildingAssessment USNG label. Having an
# index on the join field greatly improves the performance of both the join and the Field Calculator.
arcpy.AddIndex_management(
    in_table=save_path,
    fields="ACCOUNT_NUM",
    index_name="ACCOUNTNUM"
)


# Create a feature layer of the BuildingAssessment feature class. ArcPy requires a feature layer to perform joins.
arcpy.MakeFeatureLayer_management(
    in_features=save_path,
    out_layer="in_memory\parcel"
)


# If the user has included a USNG layer, then update the specified BuildingAssessment field with the specified USNG
# field. Note, that we are pointing to the BuildingAssessment feature layer. Any field calculations we do on the feature
# layer will be honored in the feature class.
# The latest USNG layer can be downloaded from https://www.arcgis.com/home/item.html?id=dc352c5f18854d82b32bce92c0b6656b
if in_grid_layer:

    updatedFieldFromSpatialJoin("in_memory\parcel", "ACCOUNT_NUM", in_grid_layer, "USNGCoord", in_grid_field)


# If the user has included a Zoning layer, then update the specidied BuildingAssessment field with the expression. Again,
# we are point to the BuildingAssessment feature layer. Any field calculations we do on the feature layer will be
# honored in the feature class.
if in_zone_layer:

    zone_field = in_zone_layer + "." + in_zone_field
    expression = "!" + zone_field + "!"

    updateFieldFromJoin("in_memory\parcel", "ACCOUNT_NUM",
                        in_zone_layer, "ACCT_",
                        "FULL_ZONE", expression)

# If the feature class was saved to an enterprise geodatabase, register the feature class as versioned so that it can
# be edited.
if isSDE(save_path):
    arcpy.RegisterAsVersioned_management(save_path)

# Add any default values to the feature class.
cursor = arcpy.da.UpdateCursor("in_memory\parcel", ["Placard"])

for row in cursor:
    row[0] = "0"
    cursor.updateRow(row)

########################################################################################################################
#
#                                                      DONE
#                                                    Mark Buie
#                                              City of Mesquite, Texas
#
########################################################################################################################
